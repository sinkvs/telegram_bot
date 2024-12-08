import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# Настроим логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Словарь стран и их валют с флагами
country_currency_map = {
    "Беларусь": ("BYN", "🇧🇾"),
    "Украина": ("UAH", "🇺🇦"),
    "США": ("USD", "🇺🇸"),
    "Россия": ("RUB", "🇷🇺"),
    "Еврозона": ("EUR", "🇪🇺"),
    "Китай": ("CNY", "🇨🇳"),
}

# Функция для получения курса валют
async def get_exchange_rate(update: Update, context: CallbackContext):
    try:
        # Получаем страну из аргумента команды
        if context.args:
            country = ' '.join(context.args)
        else:
            await update.message.reply_text("⚠️ Укажите страну после команды /exchange_rate.")
            return

        # Если страна "Россия", то нужно использовать RUB
        if country == "Россия":
            country_currency = "RUB"
            flag = "🇷🇺"
        else:
            # Проверка на существование в словаре
            if country not in country_currency_map:
                await update.message.reply_text(f"⚠️ К сожалению, я не знаю курс для {country}. Пожалуйста, попробуйте другую страну.")
                return

            # Получаем валюту и флаг
            country_currency, flag = country_currency_map[country]

        # URL для получения данных о курсах валют от Центробанка России
        url = "https://www.cbr-xml-daily.ru/daily_json.js"
        response = requests.get(url)

        if response.status_code != 200:
            logger.error(f"Ошибка при получении данных с API: {response.status_code}")
            await update.message.reply_text("⚠️ Ошибка при получении данных о курсах валют. Попробуйте позже!")
            return

        data = response.json()

        if 'Valute' not in data:
            logger.error(f"Ошибка в формате данных от API: {data}")
            await update.message.reply_text("⚠️ Ошибка при получении данных о курсах валют. Попробуйте позже!")
            return

        # Получение курса валют
        exchange_rates = {
            "USD": data['Valute']['USD']['Value'],
            "EUR": data['Valute']['EUR']['Value'],
            "BYN": data['Valute']['BYN']['Value'],
            "CNY": data['Valute']['CNY']['Value'],
            "UAH": data['Valute']['UAH']['Value'],
            "RUB": data['Valute']['RUB']['Value']
        }

        rate_message = f"💸 Курсы валют для {flag} {country} ({country_currency}):\n"
        for code, rate in exchange_rates.items():
            if code == country_currency:
                continue
            flag_for_code = {
                "USD": "🇺🇸",
                "EUR": "🇪🇺",
                "BYN": "🇧🇾",
                "CNY": "🇨🇳",
                "UAH": "🇺🇦",
                "RUB": "🇷🇺"
            }
            rate_message += f"{flag_for_code.get(code, '')} {code}: 1 {country_currency} = {rate:.2f} {code}\n"

        await update.message.reply_text(rate_message)

    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при запросе: {e}")
        await update.message.reply_text("⚠️ Ошибка при получении курса. Попробуйте позже!")

# Основная функция запуска бота
def main():
    # Вставьте свой токен
    token = '7550339760:AAHD-IdefcXzLER99r9_6zN32GT8g2HlnvU'
    
    # Создаем экземпляр Application и передаем ему токен
    application = Application.builder().token(token).build()

    # Обработчик команды /start
    application.add_handler(CommandHandler('start', start))

    # Обработчик команды /exchange_rate с параметром страны
    application.add_handler(CommandHandler('exchange_rate', get_exchange_rate))

    # Запускаем бота
    application.run_polling()

# Функция для обработки команды /start
def start(update: Update, context: CallbackContext):
    update.message.reply_text("Привет! Я могу предоставить курс валют для разных стран. Введите команду /exchange_rate <страна>, чтобы узнать курс.")

if __name__ == '__main__':
    main()
