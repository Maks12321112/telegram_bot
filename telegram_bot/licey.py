import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from datetime import datetime
import asyncio


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


reply_keyboard = [['/planning_tasks', '/game'],
                  ['/health', '/work_time']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)

auth_keyboard = [['Войти', 'Зарегистрироваться']]
auth_markup = ReplyKeyboardMarkup(auth_keyboard, one_time_keyboard=True)


NAME, EMAIL, PHONE, PASSWORD, TIME, TASK = range(6)

user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Добро пожаловать! Пожалуйста, выберите действие:",
        reply_markup=auth_markup
    )
    return NAME  

async def handle_auth_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    choice = update.message.text
    
    if choice == 'Зарегистрироваться':
        await update.message.reply_text("Пожалуйста, введите ваше полное имя.")
        return NAME
    elif choice == 'Войти':
        await update.message.reply_text("пусто.")
        return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data[user_id] = {'name': update.message.text}
    await update.message.reply_text("Пожалуйста, введите ваше полное имя.")
    if update.message.text == 'Зарегистрироваться':
        return NAME
    else:
        await update.message.reply_text("Спасибо, {}! Теперь, пожалуйста, введите ваш email.".format(update.message.text))
        return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data[user_id]['email'] = update.message.text
    await update.message.reply_text("Отлично! Теперь, пожалуйста, введите ваш номер телефона.")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data[user_id]['phone'] = update.message.text
    await update.message.reply_text("Отлично! Теперь, пожалуйста, введите пароль.")
    return PASSWORD

async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    user_data[user_id]['password'] = update.message.text
    await update.message.reply_text("Спасибо за регистрацию! Вы ввели:\nИмя: {}\nEmail: {}\nТелефон: {}\n".format(
        user_data[user_id]['name'],
        user_data[user_id]['email'],
        user_data[user_id]['phone']
    ), reply_markup=markup)
    return ConversationHandler.END

async def planning_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отлично! Теперь, напиши свою задачу в формате: 'HH:MM:SS задача'")
    print(2)
    return TIME  

async def receive_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.message.text.split()
    print(1)
    if len(data) < 2:
        await update.message.reply_text("Пожалуйста, укажи время и задачу.")
        return TIME  
    time_str = data[0]
    task_str = ' '.join(data[1:])
    

    await update.message.reply_text(f"Задача '{task_str}' запланирована на {time_str }.")

    while True:
        current_time = datetime.now().strftime("%H:%M:%S")
        if current_time == time_str:
            await update.message.reply_text(f"Выполняю задачу: {task_str}")
            break
        await asyncio.sleep(1)  

    return ConversationHandler.END  

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Регистрация отменена.")
    return ConversationHandler.END

def main():
    application = ApplicationBuilder().token("7862025833:AAHgRdxBJDe5imV42ZGJQGSOSZY7Bz6MZuI").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    application.add_handler(conv_handler)
    conv_handler2 = ConversationHandler(
        entry_points=[CommandHandler("planning_tasks", planning_tasks)],
        states={
            TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_task)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    application.add_handler(conv_handler2)
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_auth_choice))
    

    application.run_polling()

if __name__ == '__main__':
    main()