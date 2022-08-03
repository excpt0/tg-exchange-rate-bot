from os import environ

import requests
from cachetools.func import ttl_cache
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import CommandHandler, Updater, CallbackContext, MessageHandler, Filters


RESPONSE_TO_CURRENCY_CODE_MAP = {
    'RUB/USD': 'USD',
    'RUB/EUR': 'EUR',
    'RUB/CNY': 'CNY',
    'RUB/HKD': 'HKD',
}


class RubleExchangeRate():
    def __init__(self):
        self._session = requests.Session()

    @ttl_cache
    def get(self, currency_code: str) -> float:
        resp = self._session.get('https://www.cbr-xml-daily.ru/daily_json.js').json()

        return resp['Valute'][currency_code]['Value']


class AppBot():
    def __init__(self, bot_token: str):
        self._updater = Updater(bot_token)
        self._ruble_exchange_rate = RubleExchangeRate()
        self._dispatcher = self._updater.dispatcher
        self._dispatcher.add_handler(CommandHandler("start", self._start_handler))
        self._dispatcher.add_handler(MessageHandler(Filters.text, self._response_handler))

    def serve(self) -> None:
        self._updater.start_polling(allowed_updates=Update.ALL_TYPES)
        self._updater.idle()

    def _response_handler(self, update: Update, context: CallbackContext) -> None:
        for search_text, currency_code in RESPONSE_TO_CURRENCY_CODE_MAP.items():
            if search_text in update.message.text:
                exchange_rate = self._ruble_exchange_rate.get(currency_code)
                update.effective_message.reply_text(
                    f'стоимость 1 {currency_code} = {exchange_rate} ₽'
                )
                return

        update.effective_message.reply_text('Ой, не могу понять что вы хотите =(')

    def _start_handler(self, update: Update, context: CallbackContext) -> None:
        buttons = []
        button_source = [
            ['Доллар США [RUB/USD]', 'Евро [RUB/EUR]'],
            ['Китайский Юань [RUB/CNY]', 'Гонконгский доллар [RUB/HKD]'],
        ]
        for names in button_source:
            buttons.append([KeyboardButton(names[0]), KeyboardButton(names[1])],)

        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Привет! Это бот курса рубля.',
            reply_markup=ReplyKeyboardMarkup(buttons)
        )


if __name__ == '__main__':
    AppBot('SOME_TOKEN').serve()
