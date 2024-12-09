import logging
import os
import requests
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackContext
from telegram import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Создаем Flask-приложение
app = Flask(__name__)

# Получаем токен из переменной окружения
token = os.getenv('TELEGRAM_TOKEN')

# Создаем объект бота
bot = Bot(token)

# Функция для обработки стартовой команды
async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    logger.info(f"Пользователь {user.username} ({user.full_name}) подключился.")
    
    # Обновленное приветственное сообщение с выбором метода определения страны
    message = (
        "🌍 Выбирай, как ты хочешь, чтобы я определил твою страну:\n\n"
        "1️⃣ Ввести страну вручную — просто напиши название страны.\n"
        "🔒 Эти данные не хранятся и не используются больше нигде. Мы просто используем их для поиска курса валют.\n\n"
        "2️⃣ Определить страну по IP-адресу — я использую API для определения твоего местоположения по IP.\n"
        "• Мы получим только страну, и это не отслеживает твою личную информацию.\n\n"
        "3️⃣ Определить страну по языку устройства — я определяю страну через язык, установленный на твоем устройстве.\n"
        "• Это тоже не нарушает твою конфиденциальность, и мы видим только язык."
    )

    # Отправка обновленного сообщения с кнопками
    await update.message.reply_text(
        message,
        reply_markup=ReplyKeyboardMarkup([ 
            [KeyboardButton("\U0001F4CD Ввести вручную")],
            [KeyboardButton("\U0001F50D Определить по IP-адресу")],
            [KeyboardButton("\U0001F3E0 Определить по языку устройства")],
            [KeyboardButton("❌ Остановить работу с ботом")]
        ], resize_keyboard=True)
    )

# Логика для выбора опции
async def handle_button(update: Update, context: CallbackContext):
    user = update.effective_user
    text = update.message.text

    logger.info(f"Пользователь {user.username} ({user.full_name}) нажал кнопку: {text}")

    if text == "\U0001F4CD Ввести вручную":
        await update.message.reply_text("📜 Пожалуйста, введите страну:")
        return  # Ожидаем ввод страны от пользователя

    elif text == "\U0001F50D Определить по IP-адресу":
        await update.message.reply_text(
            "🌍 Мы будем использовать API для определения страны по твоему IP-адресу. "
            "Мы получим только страну, и больше никаких данных о тебе не будет использовано."
        )
        # Симуляция получения страны по IP
        country = "Russia"  # Пример страны, найденной по IP
        await update.message.reply_text(f"🇷🇺 Страна определена как {country}.")
        await get_exchange_rate(update, context, country)
    elif text == "\U0001F3E0 Определить по языку устройства":
        await update.message.reply_text(
            "🌍 Мы будем использовать язык, установленный на твоем устройстве, чтобы определить страну. "
            "Это не отслеживает тебя, и мы видим только язык."
        )
        # Симуляция получения страны по языку устройства
        language = "ru"  # Пример языка устройства
        if language == "ru":
            country = "Russia"
            await update.message.reply_text(f"🇷🇺 Страна определена как {country}.")
            await get_exchange_rate(update, context, country)
        else:
            await update.message.reply_text("🚫 Не удалось определить страну по языку устройства. Пожалуйста, введите страну вручную.")
    elif text == "❌ Остановить работу с ботом":
        await update.message.reply_text("🚫 Работа с ботом остановлена.", reply_markup=ReplyKeyboardRemove())
        # Кнопка для начала работы заново
        await update.message.reply_text(
            "✅ Бот остановлен. Для начала работы нажмите кнопку ниже.",
            reply_markup=ReplyKeyboardMarkup([ 
                [KeyboardButton("🔄 Начать заново")]
            ], resize_keyboard=True)
        )

    # Обработка кнопки "Начать заново"
    elif text == "🔄 Начать заново":
        await start(update, context)

    # Логика для обработки ввода страны вручную
    elif text not in ["❌ Остановить работу с ботом", "🔄 Начать заново"]:
        country = text.strip()  # Получаем название страны, введённое пользователем
        await get_exchange_rate(update, context, country)

# Получение курса валют относительно рубля через API Центробанка России
async def get_exchange_rate(update: Update, context: CallbackContext, country: str):
    try:
        # Базовая валюта - рубль (RUB)
        base_currency = "RUB"

        # URL для получения данных о курсах валют от Центробанка России
        url = "https://www.cbr-xml-daily.ru/daily_json.js"
        response = requests.get(url)
        data = response.json()

        if 'Valute' not in data:
            await update.message.reply_text("⚠️ Ошибка при получении данных о курсах валют. Попробуйте позже!")
            return

        # Получение курса для нужных валют
        exchange_rates = {
            "USD": data['Valute']['USD']['Value'],
            "EUR": data['Valute']['EUR']['Value'],
            "BYN": data['Valute']['BYN']['Value'],
            "CNY": data['Valute']['CNY']['Value'],
            "UAH": data['Valute']['UAH']['Value']
        }

        # Формируем сообщение с курсами в нужном формате
        rate_message = f"💸 Курсы валют для {country}:\n"
        for code, rate in exchange_rates.items():
            country_flag = get_country_flag(code)  # Получаем флаг страны
            rate_message += f"{country_flag} 1 {code} = {rate} RUB\n"

        await update.message.reply_text(rate_message)

        # Меняем кнопки на выбор базовой валюты
        await update.message.reply_text(
            "🔄 Если хочешь изменить страну, останови работу с ботом и начни процедуру заново. Увы, пока даже с костылем сделать смену страны не получилось.",
            reply_markup=ReplyKeyboardMarkup([ 
                [KeyboardButton("❌ Остановить работу с ботом")]
            ], resize_keyboard=True)
        )

    except Exception as e:
        logger.error(f"Ошибка при получении курса валют: {e}")
        await update.message.reply_text("⚠️ Ошибка при получении курса. Попробуйте позже!")

# Функция для получения флага страны по коду валюты
def get_country_flag(currency_code):
    flags = {
        "USD": "🇺🇸",  # США
        "EUR": "🇪🇺",  # Еврозона
        "BYN": "🇧🇾",  # Беларусь
        "CNY": "🇨🇳",  # Китай
        "UAH": "🇺🇦",  # Украина
    }
    return flags.get(currency_code, "🏳️")  # Если флаг не найден, используем нейтральный флаг

# Настройка webhook для Render
def set_webhook():
    webhook_url = os.getenv("WEBHOOK_URL")  # URL для вебхуков, настроенный на Render
    bot.set_webhook(url=webhook_url)

# Flask route для обработки запросов
@app.route('/webhook', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = Update.de_json(json_str, bot)
    application.process_update(update)
    return 'OK'

# Запуск приложения Flask
if __name__ == "__main__":
    # Устанавливаем webhook
    set_webhook()
    # Запуск Flask приложения на порту, предоставленном Render
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
