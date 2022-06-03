from telebot import TeleBot, types
from configparser import ConfigParser
import requests
import json


class APIException(Exception):
    pass


class CurrencyConverter:
    def __init__(self):
        config = ConfigParser()
        config.read('config.ini')
        self.api_key = config['Keys']['api_key']

    def convert(self, _from, _to, _amount=1):
        req_str = f'https://api.apilayer.com/exchangerates_data/convert?from={_from}&to={_to}&amount={_amount}'
        try:
            req = requests.get(req_str, headers={'apikey': self.api_key})
        except requests.exceptions.ConnectionError:
            result_content = f'Connection error'
            result_status = 'ErrorConnection'
            message_for_human = f'Error: connection to server error'
        else:
            if req.status_code == 400:
                result_content = f'Incorrect input'
                result_status = 'ErrorInput'
                message_for_human = f'Error: incorrect input'
            elif req.status_code != 200:
                result_content = f'Error in HTTP request: {req.status_code}'
                result_status = 'ErrorHTTP'
                message_for_human = f'Error: {result_content}'
            else:
                result_content = json.loads(req.content)['result']
                result_status = 'OK'
                message_for_human = f'{_amount} {_from} = {result_content} {_to}'
        return {'status': result_status, 'content': result_content, 'for_human': message_for_human}


def bot_conv(message: types.Message, bot: TeleBot):
    try:
        text = message.text.split()
        _from = text[1].upper()
        _to = text[2].upper()
        _amount = 1 if len(text) == 3 else float(text[3])
    except Exception:
        bot.send_message(message.chat.id, 'Incorrect input')
        return
    try:
        if _from not in bot.possible_currencies:
            raise APIException(f'Incorrect currency {_from}')
        if _to not in bot.possible_currencies:
            raise APIException(f'Incorrect currency {_to}')
    except APIException as e:
        bot.send_exception(message.chat.id, e)
    else:
        result = CurrencyConverter().convert(_from, _to, _amount)
        bot.send_message(message.chat.id, result['for_human'])


def bot_values(message: types.Message, bot: TeleBot):
    bot.send_message(message.chat.id, f'Possible currencies: {bot.possible_currencies}')


def bot_info(message: types.Message, bot: TeleBot):
    bot.send_message(message.chat.id, 'SuperBot v 1.0')


def bot_help(message: types.Message, bot: TeleBot):
    bot.send_message(message.chat.id, '/help - this message\n'
                                      '/conv from to (amount)- convert currencies, default amount = 1\n'
                                      '/values - possibles currencies\n'
                                      '/info - Bot version\n'
                                      'Examples:\n'
                                      '/conv usd rub\n'
                                      '/conv eur usd 15.5')


class SuperBot(TeleBot):
    def __init__(self):
        config = ConfigParser()
        config.read('config.ini')
        token = config['Keys']['bot_token']
        super().__init__(token)

        self.possible_currencies = config['Currencies']['possible_currencies'].split()

        self.register_message_handler(SuperBot.bot_start, commands=['start'], pass_bot=True)
        self.register_message_handler(bot_help, commands=['help'], pass_bot=True)
        self.register_message_handler(bot_info, commands=['info'], pass_bot=True)
        self.register_message_handler(bot_conv, commands=['conv'], pass_bot=True)
        self.register_message_handler(bot_values, commands=['values'], pass_bot=True)

    @staticmethod
    def bot_start(message: types.Message, bot: TeleBot):
        bot.send_message(message.chat.id, 'Currency converter\ntype /help for usage')

    def send_exception(self, chat_id, message):
        self.send_message(chat_id, message)

    def start(self):
        self.polling(none_stop=True)
