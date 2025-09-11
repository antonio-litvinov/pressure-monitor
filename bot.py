import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

import json

logging.basicConfig(level=logging.INFO)

from dotenv import load_dotenv

load_dotenv()

import os
from supabase import create_client, Client

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)


# Обработчик команды /start — отправляет кнопку для запуска мини-аппы
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [KeyboardButton(text="🩺 Измерить", web_app=WebAppInfo(url="https://pressure-monitor.ru/app.html"))],
        [KeyboardButton(text="❓ Помощь")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)
    await update.message.reply_text(
        "<b>🙏 Спасибо вам за помощь в тестировании цифрового тонометра!</b>\n\n"
        "Мы настраиваем технологию, и каждое успешное измерение (как и неуспешное) "
        "приближает нас к тому, чтобы у каждого человека было удобное решение для измерения давления — "
        "в любое время и в любом месте.\n\n"
        "<i>Нажмите «Измерить», чтобы начать</i>🚀",
        reply_markup=reply_markup,
        parse_mode="HTML"
    )

# Обработчик команды /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    #await update.message.reply_text(help_text, parse_mode='Markdown')
    await update.message.reply_text(
        "<b>📋 Помощь по использованию цифрового тонометра</b>\n\n"
        "Пожалуйста, <b>сядьте удобно</b> и <b>увеличьте яркость экрана</b> до максимума. "
        "Измерение будет точнее, если ваше лицо <b>хорошо освещено</b>.\n\n"
        "<b>Как использовать:</b>\n"
        "1️⃣ Нажмите <b>«Измерить»</b> для запуска приложения\n"
        "2️⃣ Разрешите доступ к камере\n"
        "3️⃣ Нажмите <b>«Начать измерение»</b>\n"
        "4️⃣ Держите лицо в кадре <b>10 секунд</b>\n"
        "5️⃣ Получите результат измерения давления\n\n"
        "<b>Требования:</b>\n"
        "• Хорошее освещение\n"
        "• Стабильное положение камеры\n"
        "• Лицо должно быть хорошо видно в кадре\n\n"
        "<b>Если возникли проблемы:</b>\n"
        "• Убедитесь, что камера не занята другими приложениями\n"
        "• Проверьте интернет-соединение\n"
        "• Попробуйте в другом браузере\n\n"
        "<i>Для повторного измерения нажмите «Измерить ещё раз» после получения результата.</i>",
        parse_mode="HTML"
    )

# Обработчик кнопки "Помощь"
async def help_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await help_command(update, context)

# Прием данных из мини-аппы
async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    data = update.effective_message.web_app_data.data
    user = update.effective_user.first_name

    try:
        parsed = json.loads(data)
        date = parsed.get("date", "")
        time = parsed.get("time", "")
        upper = parsed.get("upper", "")
        lower = parsed.get("lower", "")
        text = f"🩺 Замер от {date} {time}:\n<b>{upper}</b> на <b>{lower}</b>"

        supabase.table("measures").insert({
            "name": user, 
            "date": date, 
            "time": time, 
            "upper": upper, 
            "lower": lower
        }).execute()

    except Exception:
        text = "Ошибка обработки данных замера"


    await update.message.reply_text(f"{text}", parse_mode='HTML')

def main():
    application = Application.builder().token(os.environ.get("TOKEN")).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^❓ Помощь$"), help_button))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()