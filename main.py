import sqlite3
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import TOKEN
from database import init_db, get_premium

# Состояние пользователя (0 - ожидание кода, 1 - ожидание табельного номера)
user_states = {}

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
        try:
            tab_number = int(user_input)
            premium, error_message = get_premium(tab_number)
            
            if error_message:
                await update.message.reply_text(error_message)
            elif premium is not None:
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
                await update.message.reply_text(response)
            else:
                await update.message.reply_text(
                    f"Табельный номер {tab_number} не найден в базе данных.\n"
                    f"Пожалуйста, проверьте номер и попробуйте снова или обратитесь к ВС/РГ своей смены."
                )
        except ValueError:
            await update.message.reply_text(
                "Пожалуйста, введите корректный табельный номер (только цифры)."
            )

def main():
    # Инициализация базы данных
    init_db()
    
    # Создаем приложение
    application = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
