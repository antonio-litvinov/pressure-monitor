#!/usr/bin/env python3
"""
Telegram бот "Тонометр" для тестирования Web App
"""

import os
import logging
import json
from datetime import datetime
from telegram import Update, WebAppInfo, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.getenv('BOT_TOKEN')
WEBAPP_URL = os.getenv('WEBAPP_URL', 'http://localhost:8000/video_recorder.html')

# Проверка токена
if not BOT_TOKEN:
    print("❌ Ошибка: Установите переменную окружения BOT_TOKEN")
    print("Создайте файл .env с содержимым:")
    print("BOT_TOKEN=ваш_токен_здесь")
    print("WEBAPP_URL=http://localhost:8000/video_recorder.html")
    exit(1)

class TonometerBot:
    def __init__(self):
        self.application = Application.builder().token(BOT_TOKEN).build()
        self.setup_handlers()
        
    def setup_handlers(self):
        """Настройка обработчиков команд"""
        # Основные команды
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("measure", self.measure_command))
        self.application.add_handler(CommandHandler("history", self.status_command))
        
        # Обработка Web App данных
        self.application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, self.handle_webapp_data))
        
        # Обработка callback запросов
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Обработка текстовых сообщений
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        
    def get_persistent_keyboard(self):
        """Получить постоянную клавиатуру с меню, которая не исчезает"""
        keyboard = [
            [
                KeyboardButton("🩺 Измерить давление", web_app=WebAppInfo(url=WEBAPP_URL)),
                KeyboardButton("📊 История")
            ]
        ]
        return ReplyKeyboardMarkup(
            keyboard, 
            resize_keyboard=True, 
            one_time_keyboard=False,
            is_persistent=True,
            input_field_placeholder="Выберите действие или напишите сообщение..."
        )
        
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /start"""
        user = update.effective_user
        
        # Удаляем команды бота, чтобы убрать встроенное меню
        try:
            await self.application.bot.delete_my_commands()
            logger.info("Команды бота удалены")
        except Exception as e:
            logger.error(f"Ошибка удаления команд: {e}")
        
        welcome_text = f"""
<b>Добро пожаловать в Тонометр!</b>

Привет! Я ваш персональный помощник для измерения артериального давления с помощью камеры телефона.

<b>Как это работает:</b>

1️⃣ Нажмите "🩺 Измерить давление"
2️⃣ Разрешите доступ к камере  
3️⃣ Снимите 10-секундное видео
4️⃣ Получите точный результат

<b>Доступные функции:</b>

• 🩺 <b>Измерить давление</b> - основная функция
• 📊 <b>История</b> - ваши предыдущие измерения

<b>🚀 Начните прямо сейчас!</b>
        """
        
        await update.message.reply_text(
            welcome_text, 
            parse_mode='HTML',
            reply_markup=self.get_persistent_keyboard()
        )
        
        # Логируем нового пользователя
        logger.info(f"Новый пользователь: {user.id} - {user.first_name} {user.last_name or ''}")
        
    async def measure_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /measure - открывает Web App"""
        measure_text = """
🩺 <b>Измерение давления</b>

Сейчас откроется Web App для измерения давления с помощью камеры.

<b>📋 Подготовка к измерению:</b>

• 🌟 Найдите хорошо освещенное место
• 📱 Убедитесь, что камера чистая
• 👆 Приготовьте палец или запястье для съемки
• 😌 Расслабьтесь и не двигайтесь во время съемки

<b>⏱️ Процесс измерения:</b>

• 🎥 Видео записывается 10 секунд
• ⚡ Анализ занимает 5-10 секунд
• 📊 Результат покажет систолическое и диастолическое давление

<b>🚀 Нажмите кнопку ниже, чтобы начать!</b>
        """
        
        await update.message.reply_text(
            measure_text, 
            parse_mode='HTML',
            reply_markup=self.get_persistent_keyboard()
        )
        
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /status - показывает статус измерений"""
        user_id = update.effective_user.id
        
        # Здесь можно добавить логику получения истории измерений из БД
        status_text = f"""
📊 <b>История измерений</b>

<b>👤 Пользователь:</b> {update.effective_user.first_name}
<b>📅 Дата регистрации:</b> {datetime.now().strftime('%d.%m.%Y')}

<b>📈 Статистика:</b>

• 📅 Последнее измерение: <i>Не проводилось</i>
• 📊 Всего измерений: <b>0</b>
• 📉 Среднее давление: <i>Нет данных</i>
• 📈 Тренд: <i>Нет данных</i>

<b>🎯 Рекомендации:</b>

Проведите первое измерение для получения статистики и отслеживания динамики давления.

<b>🚀 Нажмите "🩺 Измерить давление" для начала!</b>
        """
        
        await update.message.reply_text(
            status_text, 
            parse_mode='HTML',
            reply_markup=self.get_persistent_keyboard()
        )
        

        

        
    async def handle_webapp_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик данных от Web App"""
        user = update.effective_user
        data = update.effective_message.web_app_data.data
        
        try:
            # Парсим данные от Web App
            webapp_data = json.loads(data)
            logger.info(f"Получены данные от Web App от пользователя {user.id}: {webapp_data}")
            
            # Обрабатываем результат измерения
            if 'pressure' in webapp_data:
                pressure_data = webapp_data['pressure']
                systolic = pressure_data.get('systolic', 'N/A')
                diastolic = pressure_data.get('diastolic', 'N/A')
                category = pressure_data.get('category', 'Не определено')
                
                result_text = f"""
📊 <b>Результат измерения давления</b>

<b>📈 Показатели:</b>

• 💓 <b>Систолическое</b> (верхнее): <b>{systolic} мм рт.ст.</b>
• 💙 <b>Диастолическое</b> (нижнее): <b>{diastolic} мм рт.ст.</b>
• 📋 <b>Категория:</b> <i>{category}</i>

<b>⏰ Время измерения:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}

<b>💡 Рекомендации:</b>

{self.get_pressure_recommendations(systolic, diastolic)}

<b>📱 Используйте кнопки ниже для дальнейших действий</b>
                """
                
                await update.message.reply_text(
                    result_text, 
                    parse_mode='HTML',
                    reply_markup=self.get_persistent_keyboard()
                )
                
            elif webapp_data.get('action') == 'webapp_closed':
                # Пользователь закрыл Web App
                logger.info(f"Пользователь {user.id} закрыл Web App")
                await update.message.reply_text(
                    "👋 Добро пожаловать обратно!\n\n"
                    "Выберите действие из меню ниже:",
                    reply_markup=self.get_persistent_keyboard()
                )
                
            else:
                # Общие данные от Web App
                await update.message.reply_text(
                    f"✅ Получены данные от Web App!\n\n"
                    f"Для измерения давления используйте кнопку меню.",
                    reply_markup=self.get_persistent_keyboard()
                )
                
        except json.JSONDecodeError:
            logger.error(f"Ошибка парсинга JSON от пользователя {user.id}: {data}")
            await update.message.reply_text(
                "❌ Ошибка обработки данных.\n"
                "Попробуйте провести измерение еще раз.",
                reply_markup=self.get_persistent_keyboard()
            )
        except Exception as e:
            logger.error(f"Ошибка обработки Web App данных от пользователя {user.id}: {e}")
            await update.message.reply_text(
                "❌ Произошла ошибка при обработке данных.\n"
                "Попробуйте еще раз.",
                reply_markup=self.get_persistent_keyboard()
            )
            
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик callback запросов от inline кнопок"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text("❌ Неизвестная команда")
            
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик текстовых сообщений"""
        text = update.message.text.lower()
        
        if "давление" in text or "измерить" in text:
            await self.measure_command(update, context)
        elif "история" in text:
            await self.status_command(update, context)
        else:
            # Для любого неизвестного сообщения показываем подсказку
            await update.message.reply_text(
                "🤔 Не понимаю команду. Используйте кнопки меню или напишите:\n"
                "• 'измерить' - для измерения давления\n"
                "• 'история' - для просмотра истории",
                reply_markup=self.get_persistent_keyboard()
            )
            

        
    def get_pressure_recommendations(self, systolic, diastolic):
        """Получить рекомендации по давлению"""
        try:
            sys_val = int(systolic)
            dia_val = int(diastolic)
            
            if sys_val < 90 and dia_val < 60:
                return "• Низкое давление - рекомендуется консультация врача"
            elif sys_val < 120 and dia_val < 80:
                return "• Нормальное давление - продолжайте вести здоровый образ жизни"
            elif sys_val < 130 and dia_val < 80:
                return "• Повышенное нормальное - следите за образом жизни"
            elif sys_val < 140 and dia_val < 90:
                return "• Высокое нормальное - рекомендуется контроль"
            elif sys_val < 160 and dia_val < 100:
                return "• Умеренная гипертензия - обратитесь к врачу"
            elif sys_val < 180 and dia_val < 110:
                return "• Высокая гипертензия - срочно к врачу"
            else:
                return "• Критически высокое давление - немедленно вызывайте скорую!"
        except:
            return "• Не удалось определить рекомендации"
            

        
    def run(self):
        """Запуск бота"""
        print("🤖 Запуск Telegram бота 'Тонометр'...")
        print(f"🌐 Web App URL: {WEBAPP_URL}")
        print("📱 Отправьте /start в Telegram для начала работы")
        print("🔄 Бот работает... Нажмите Ctrl+C для остановки")
        
        try:
            self.application.run_polling(allowed_updates=Update.ALL_TYPES)
        except KeyboardInterrupt:
            print("\n🛑 Остановка бота...")
        except Exception as e:
            print(f"❌ Ошибка запуска бота: {e}")

def main():
    """Главная функция"""
    print("🩺 Telegram Бот 'Тонометр'")
    print("=" * 50)
    
    # Проверяем конфигурацию
    if not BOT_TOKEN:
        print("❌ Ошибка: BOT_TOKEN не установлен")
        print("Создайте файл .env с содержимым:")
        print("BOT_TOKEN=ваш_токен_здесь")
        print("WEBAPP_URL=http://localhost:8000/video_recorder.html")
        return
        
    # Создаем и запускаем бота
    bot = TonometerBot()
    bot.run()

if __name__ == '__main__':
    main()
