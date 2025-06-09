import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import TOKEN
from database import init_db, get_premium

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Введите ваш табельный номер для получения информации о премии."
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    
    try:
        # Проверяем, является ли введенный текст числом
        tab_number = int(user_input)
        
        # Получаем данные о премии из базы
        premium = get_premium(tab_number)
        
        if premium:
            gross_premium = premium  # Сумма без НДФЛ
            ndfl = gross_premium * 0.13  # НДФЛ 13%
            net_premium = gross_premium - ndfl  # Сумма с учетом НДФЛ
            
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