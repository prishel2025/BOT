import sqlite3
import time
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import TOKEN
from database import init_db, get_premium

# Состояние пользователя (0 - ожидание кода, 1 - ожидание табельного номера)
user_states = {}

# Инициализация базы данных с таблицей для отслеживания запросов
def init_db_with_limit():
    conn = sqlite3.connect('premiums.db')
    c = conn.cursor()
    # Создаем таблицу для хранения запросов пользователей
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_requests (
            user_id INTEGER,
            request_time REAL,
            PRIMARY KEY (user_id, request_time)
        )
    ''')
    conn.commit()
    conn.close()
    init_db()  # Вызываем оригинальную функцию инициализации базы данных

# Проверка количества запросов пользователя за последние 24 часа
def check_request_limit(user_id):
    conn = sqlite3.connect('premiums.db')
    c = conn.cursor()
    one_day_ago = time.time() - 24 * 60 * 60  # Время 24 часа назад
    c.execute('''
        SELECT COUNT(*) FROM user_requests 
        WHERE user_id = ? AND request_time > ?
    ''', (user_id, one_day_ago))
    count = c.fetchone()[0]
    
    if count >= 6:
        # Находим время первого запроса из последних 6
        c.execute('''
            SELECT request_time FROM user_requests 
            WHERE user_id = ? AND request_time > ?
            ORDER BY request_time ASC LIMIT 1
        ''', (user_id, one_day_ago))
        first_request_time = c.fetchone()[0]
        reset_time = first_request_time + 24 * 60 * 60
        remaining_seconds = reset_time - time.time()
        remaining_hours = int(remaining_seconds // 3600)
        remaining_minutes = int((remaining_seconds % 3600) // 60)
        conn.close()
        return False, f"Превышен лимит запросов (6 в сутки). Пожалуйста, подождите {remaining_hours} часов и {remaining_minutes} минут до следующей попытки."
    
    conn.close()
    return True, ""

# Регистрация запроса пользователя
def log_request(user_id):
    conn = sqlite3.connect('premiums.db')
    c = conn.cursor()
    c.execute('INSERT INTO user_requests (user_id, request_time) VALUES (?, ?)', (user_id, time.time()))
    conn.commit()
    conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_states[user_id] = 0  # Устанавливаем состояние: ожидание кода
    await update.message.reply_text(
        "Для продолжения введите код доступа."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_input = update.message.text.strip()
    
    if user_id not in user_states:
        user_states[user_id] = 0  # Состояние по умолчанию: ожидание кода
    
    if user_states[user_id] == 0:  # Ожидание кода
        if user_input == "1808":
            user_states[user_id] = 1  # Переключаем состояние на ожидание табельного номера
            await update.message.reply_text(
                "Код верный! Теперь введите ваш табельный номер."
            )
        else:
            await update.message.reply_text(
                "Неверный код. Пожалуйста, введите правильный код (УЗНАТЬ ЕГО МОЖНО У ВАШЕГО ВС/РГ)."
            )
    elif user_states[user_id] == 1:  # Ожидание табельного номера
        # Проверка лимита запросов
        is_allowed, error_message = check_request_limit(user_id)
        if not is_allowed:
            await update.message.reply_text(error_message)
            return
        
        try:
            tab_number = int(user_input)
            # Регистрируем запрос после успешной проверки табельного номера
            log_request(user_id)
            premium = get_premium(tab_number)
            
            if premium:
                gross_premium = premium
                ndfl = gross_premium * 0.13
                net_premium = gross_premium - ndfl
                
                response = (
                    f"Табельный номер: {tab_number}\n"
                    f"Сумма премии без НДФЛ: {gross_premium} руб.\n"
                    f"Сумма премии с учетом НДФЛ: {net_premium:.2f} руб.\n\n"
                    f"Для получения подробной информации или при обнаружении ошибки "
                    f"обращайтесь к ВС/РГ своей смены."
                )
            else:
                response = (
                    f"Табельный номер {tab_number} не найден в базе данных.\n"
                    f"Пожалуйста, проверьте номер и попробуйте снова или обратитесь к ВС/РГ своей смены."
                )
                
            await update.message.reply_text(response)
            
        except ValueError:
            await update.message.reply_text(
                "Пожалуйста, введите корректный табельный номер (только цифры)."
            )

def main():
    # Инициализация базы данных с учетом лимитов
    init_db_with_limit()
    
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
