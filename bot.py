import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)

# Обработчик команды /start — отправляет кнопку для запуска мини-аппы
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [KeyboardButton(text="Измерить", web_app=WebAppInfo(url="https://pressure-monitor.ru/app.html"))],
        [KeyboardButton(text="Помощь")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)
    await update.message.reply_text("Нажмите на кнопку 'Измерить' для запуска приложения:", reply_markup=reply_markup)

# Обработчик команды /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = """
📋 **Помощь по использованию цифрового тонометра**

**Как использовать:**
1. Нажмите "Измерить" для запуска приложения
2. Разрешите доступ к камере
3. Нажмите "Начать измерение"
4. Держите лицо в кадре 10 секунд
5. Получите результат измерения давления

**Требования:**
• Хорошее освещение
• Стабильное положение камеры
• Лицо должно быть хорошо видно в кадре

**Поддерживаемые браузеры:**
• Safari на iOS 14.3+
• Chrome, Firefox на Android
• Требуется HTTPS соединение

**Если возникли проблемы:**
• Убедитесь, что камера не занята другими приложениями
• Проверьте интернет-соединение
• Попробуйте в другом браузере

Для повторного измерения нажмите "Измерить ещё раз" после получения результата.
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

# Обработчик кнопки "Помощь"
async def help_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await help_command(update, context)

# Прием данных из мини-аппы
async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.effective_message.web_app_data.data
    await update.message.reply_text(f"{text}")

def main():
    application = Application.builder().token("8462728848:AAFcqpERSPj88PaHdfyX0Qcjnqrb_pOk3Cw").build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.Regex("^Помощь$"), help_button))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()