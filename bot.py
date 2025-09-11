import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)

# Обработчик команды /start — отправляет кнопку для запуска мини-аппы
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [KeyboardButton(text="Открыть мини-аппу", web_app=WebAppInfo(url="https://pressure-monitor.ru/app3.html"))]  # замените на адрес вашего приложения
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Нажмите на кнопку для запуска мини-аппы:", reply_markup=reply_markup)

# Прием данных из мини-аппы
async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.effective_message.web_app_data.data
    await update.message.reply_text(f"{text}", reply_markup=ReplyKeyboardRemove())

def main():
    application = Application.builder().token("8462728848:AAFcqpERSPj88PaHdfyX0Qcjnqrb_pOk3Cw").build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()