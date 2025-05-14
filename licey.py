
from datetime import datetime
import asyncio
import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
from forms.user import User
from forms.healthtest import HealthTest
from forms.tasks import Task
from sessions import *
import requests
from health import *
from weather import *
from test import *
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


global_init("bot_database.db")

(MAIN_MENU, AUTH_CHOICE, NAME, AGE,  EMAIL, PHONE, PASSWORD, LOGIN_EMAIL, LOGIN_PASSWORD,
TASK_TIME, HEALTH_MENU, BMI_WEIGHT, BMI_HEIGHT,
FLEXIBILITY_TEST, PUSHUPS_TEST, COOPER_TEST, MILE_TEST, WAITING_CITY
) = range(18)


def keyboard():
    return ReplyKeyboardMarkup([
        ['/planning_tasks', '/health'],
        ['/profile', '/help',
         '/weather'],
         ['/bmi_stats']
    ], resize_keyboard=True)


def get_auth_keyboard():
    return ReplyKeyboardMarkup([
        ['Войти', 'Зарегистрироваться']
    ], one_time_keyboard=True)


def get_health_keyboard():
    return ReplyKeyboardMarkup([
        ['/bmi', '/flexibility'],
        ['/pushups', '/cooper'],
        ['/mile', '/cancel']
    ], resize_keyboard=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Добро пожаловать! Пожалуйста, выберите действие:",
        reply_markup=get_auth_keyboard()
    )
    return AUTH_CHOICE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Вы закрыли функцию",
        reply_markup=keyboard()
    )
    return MAIN_MENU

async def handle_auth_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    choice = update.message.text
    
    if choice == 'Зарегистрироваться':
        await update.message.reply_text("Пожалуйста, введите ваше полное имя.")
        return NAME
    elif choice == 'Войти':
        await update.message.reply_text("Пожалуйста, введите ваш email.")
        return LOGIN_EMAIL

async def login_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['login_email'] = update.message.text
    await update.message.reply_text("Введите ваш пароль:")
    return LOGIN_PASSWORD

async def login_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    email = context.user_data['login_email']
    password = update.message.text
    
    session = create_session()
    try:
        user = session.query(User).filter(User.email == email, User.password == password).first()
        if user:
            context.user_data['user_id'] = user.id
            await update.message.reply_text(
                "Вы успешно вошли в систему!",
                reply_markup=keyboard()
            )
            session.close()
            return MAIN_MENU
        else:
            await update.message.reply_text(
                "Неверный email или пароль. Попробуйте еще раз.",
                reply_markup=get_auth_keyboard()
            )
            session.close()
            return AUTH_CHOICE
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка при входе: {e}")
        await update.message.reply_text(
            "Произошла ошибка при входе. Попробуйте позже.",
            reply_markup=get_auth_keyboard()
        )
        return AUTH_CHOICE

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['name'] = update.message.text
    await update.message.reply_text("Спасибо! Теперь введите ваш возраст.")
    return AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['age'] = update.message.text
    await update.message.reply_text("Спасибо! Теперь введите ваш email.")
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['email'] = update.message.text
    await update.message.reply_text("Введите ваш номер телефона.")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data['phone'] = update.message.text
    await update.message.reply_text("Введите пароль.")
    return PASSWORD

async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user.id
    context.user_data['password'] = update.message.text

    session = create_session()
    try:
        user = User(
            name=context.user_data['name'],
            age=context.user_data['age'],
            email=context.user_data['email'],
            phone=context.user_data['phone'],
            password=context.user_data['password'],
            
        )
        session.add(user)
        session.commit()
        context.user_data['user_id'] = user.id
        logger.info(f"Пользователь {user_id} сохранен")
        session.close()
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка сохранения пользователя: {e}")
    
    await update.message.reply_text(
        "Регистрация завершена!",
        reply_markup=keyboard()
    )
    return MAIN_MENU

async def planning_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Введите задачу в формате: 'HH:MM:SS задача'")
    return TASK_TIME

async def receive_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = context.user_data['user_id']
    data = update.message.text.split()
    
    if len(data) < 2:
        await update.message.reply_text("Пожалуйста, укажите время и задачу.")
        return TASK_TIME
    time_str = data[0]
    task_text = ' '.join(data[1:])
    
    session = create_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            task = Task(
                user_id=user.id,
                time=time_str,
                text=task_text
            )
            session.add(task)
            session.commit()
            logger.info(f"Задача сохранена для {user_id}")
            session.close()
        else:
            await update.message.reply_text("не найден!")
            return MAIN_MENU
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка{e}")
    
        
    
    await update.message.reply_text(
        f"Задача '{task_text}' запланирована на {time_str}",
        reply_markup=keyboard()
    )
    

    async def check_time():
        while True:
            if datetime.now().strftime("%H:%M:%S") == time_str:
                await update.message.reply_text(f"Время выполнять: {task_text}!")
                break
            await asyncio.sleep(1)
    
    asyncio.create_task(check_time())
    return MAIN_MENU


async def health_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Выберите тест здоровья:",
        reply_markup=get_health_keyboard()
    )
    return HEALTH_MENU


async def bmi_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Введите ваш вес (кг):")
    return BMI_WEIGHT


async def bmi_weight(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        context.user_data['weight'] = float(update.message.text)
        await update.message.reply_text("Введите ваш рост (м):")
        return BMI_HEIGHT
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число!")
        return BMI_WEIGHT


async def bmi_height(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        user_id = update.message.from_user.id
        weight = context.user_data['weight']
        height = float(update.message.text)
        bmi = weight / (height ** 2)
        
        if bmi < 18.5:
            status = "Недостаточный вес"
        elif 18.5 <= bmi < 25:
            status = "Нормальный вес"
        elif 25 <= bmi < 30:
            status = "Избыточный вес"
        else:
            status = "Ожирение"


        session = create_session()
        try:
            user = session.query(User).filter(User.id == context.user_data['user_id']).first()
            if user:
                test = HealthTest(
                    user_id=user.id,
                    test_type="BMI",
                    result=f"{bmi:.1f} ({status})"
                )
                session.add(test)
                session.commit()
                session.close()
            else:
                print('ERROR')
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка сохранения теста: {e}")
        
        
        
        await update.message.reply_text(
            f"Ваш ИМТ: {bmi:.1f}\nСтатус: {status}",
            reply_markup=get_health_keyboard()
        )
        return HEALTH_MENU
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число!")
        return BMI_HEIGHT


async def flexibility_test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("На сколько см вы дотянулись до пальцев ног? (+ если дотянулись, - если нет):")
    return FLEXIBILITY_TEST

async def handle_flexibility(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        distance = float(update.message.text)
        user_id = update.message.from_user.id
        
        if distance >= 0:
            result = f"Гибкость: +{distance} см (хорошо)"
        else:
            result = f"Гибкость: {-distance} см (ниже нормы)"

        session = create_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                test = HealthTest(
                    user_id=user.id,
                    test_type="Flexibility",
                    result=result
                )
                session.add(test)
                session.commit()
                session.close()
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка сохранения теста: {e}")
        
            
        
        await update.message.reply_text(
            result,
            reply_markup=get_health_keyboard()
        )
        return HEALTH_MENU
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число!")
        return FLEXIBILITY_TEST


async def bmi_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
   
    buf = plot_bmi()
    
    buf.seek(0)  
    await update.message.reply_photo(
        photo=buf,
        caption="График зависимости BMI от возраста пользователей"
    )

    buf.close()












def main():
    application = ApplicationBuilder().token("7862025833:AAHgRdxBJDe5imV42ZGJQGSOSZY7Bz6MZuI").build()

    main_conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN_MENU: [
                CommandHandler('planning_tasks', planning_tasks),
                CommandHandler('health', health_menu),
                CommandHandler('weather', weather_command),
                CommandHandler('bmi_stats', bmi_stats),
                CommandHandler('cancel', cancel)
            ],
            AUTH_CHOICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_auth_choice)],
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            AGE:  [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)],
            LOGIN_EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_email)],
            LOGIN_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, login_password)],
            TASK_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_task)],
            WAITING_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city)],
            HEALTH_MENU: [
                CommandHandler('bmi', bmi_start),
                CommandHandler('flexibility', flexibility_test),
                CommandHandler('pushups', pushups_test),
                CommandHandler('cooper', cooper_test),
                CommandHandler('mile', mile_test),

                CommandHandler('cancel', cancel)
            ],

            BMI_WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bmi_weight)],
            BMI_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bmi_height)],
            FLEXIBILITY_TEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_flexibility)],
            PUSHUPS_TEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_pushups)],
            COOPER_TEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_cooper)],
            MILE_TEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_mile)],
            

           
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(main_conv)
    application.run_polling()

if __name__ == '__main__':
    main()