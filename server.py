import g4f
from datetime import datetime
import asyncio
import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler
)
from data.user import User
from data.healthtest import HealthTest
from data.tasks import Task
from data.questionnaire import Questionnaire
from data.sessions import *
import requests
from forms.health import *

from forms.weather import *
from forms.test import *
import logging

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
global_init("db/bot_database.db")

(MAIN_MENU, AUTH_CHOICE, NAME, AGE, EMAIL, PHONE, PASSWORD, LOGIN_EMAIL, LOGIN_PASSWORD,
TASK_TIME, HEALTH_MENU, BMI_WEIGHT, BMI_HEIGHT, FLEXIBILITY_TEST, PUSHUPS_TEST,
COOPER_TEST, MILE_TEST, WAITING_CITY, QUESTIONNAIRE,
DOC_RESPONSE) = range(20)




def keyboard():
    return ReplyKeyboardMarkup([
        ['/planning_tasks', '/health'],
        ['/profile', '/help',
         '/weather'],
         ['/bmi_stats', '/check_questionnaire']
    ], resize_keyboard=True)


def get_auth_keyboard():
    return ReplyKeyboardMarkup([
        ['Войти', 'Зарегистрироваться']
    ], one_time_keyboard=True)


def get_health_keyboard():
    return ReplyKeyboardMarkup([
        ['/bmi', '/flexibility'],
        ['/pushups', '/cooper'],
        ['/mile', '/new_case', '/ask'],
        ['/cancel']
    ], resize_keyboard=True)


async def restart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /restart"""
    user_id = update.message.from_user.id
    logger.info(f"Пользователь {user_id} запросил перезапуск")
    
   
    context.user_data.clear()
    context.user_data['user_id'] = user_id  
    
    await update.message.reply_text(
        "Бот перезапущен. Все данные сброшены.\n"
        "Используйте /start для начала работы.",
        reply_markup=get_auth_keyboard()  
    )
    
    return AUTH_CHOICE 

async def check_questionnaire(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data['user_id']
    session = create_session()
    try:
        questionnaire = session.query(Questionnaire).filter(Questionnaire.user_id == user_id)\
            .order_by(Questionnaire.created_at.desc())\
            .first()
        
        if not questionnaire:
            await update.message.reply_text("У вас нет активных анкет.")
            return
        
        status_message = (
            f"📋 Статус вашей анкеты #{questionnaire.id}:\n"
            f"🔄 Статус: {questionnaire.status}\n"
        )
        
        if questionnaire.status == 'Завершено':
            status_message += f"📝 Рекомендации врача:\n{questionnaire.recommendations}"
        await update.message.reply_text(status_message)
    except Exception as e:
        logger.error(f"Ошибка при проверке анкеты: {e}")
        await update.message.reply_text(" Произошла ошибка. Попробуйте позже.")
    finally:
        session.close()






async def view_questionnaires(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if context.user_data.get('user_id') != 13:
        await update.message.reply_text("Эта функция доступна только врачам.")
        return MAIN_MENU
    
    session = create_session()
    questionnaires = session.query(Questionnaire).filter(Questionnaire.status == 'Новый').all()
    
    if not questionnaires:
        await update.message.reply_text("Нет новых анкет.")
        return
    
    keyboard = []
    for q in questionnaires:

        user = session.query(User).filter(User.id == q.user_id).first()
        user_info = f"{user.name}, {user.age} лет" if user else "Неизвестный пользователь"
        keyboard.append([InlineKeyboardButton(
            f"Анкета #{q.id} от {user_info}", 
            callback_data=f"q_{q.id}"
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите анкету для ответа:", reply_markup=reply_markup)
    session.close()

async def questionnaire_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if context.user_data.get('user_id') != 13:
        await query.message.reply_text("Эта функция доступна только врачам.")
        return MAIN_MENU
    
    q_id = int(query.data.split('_')[1])
    context.user_data['current_q'] = q_id
    
    session = create_session()
    questionnaire = session.query(Questionnaire).get(q_id)
    user = session.query(User).filter(User.id == questionnaire.user_id).first()
    
    if questionnaire:

        user_info = f"{user.name}, {user.age} лет" if user else "Неизвестный пользователь"
        text = (
            f"Анкета #{q_id}\n"
            f"Пациент: {user_info}\n"
            f"Симптомы:\n{questionnaire.symptoms}\n\n"
            "Введите рекомендации для пациента:"
        )
        await query.message.reply_text(text)
    else:
        await query.message.reply_text("Анкета не найдена!")
    
    session.close()
    return DOC_RESPONSE

async def start_questionnaire(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data['user_id']

    session = create_session()
    active_questionnaire = session.query(Questionnaire).filter(
        Questionnaire.user_id == user_id,
        Questionnaire.status == 'Новый'
    ).first()
    session.close()
    
    if active_questionnaire:
        await update.message.reply_text(
            "У вас уже есть активная анкета. Дождитесь ответа врача.",
            reply_markup=keyboard()
        )
        return MAIN_MENU
    
    await update.message.reply_text("Опишите ваши симптомы:")
    return QUESTIONNAIRE

async def save_questionnaire(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data['user_id']
    symptoms = update.message.text

    session = create_session()
    active_questionnaire = session.query(Questionnaire).filter(
        Questionnaire.user_id == user_id,
        Questionnaire.status == 'Новый'
    ).first()
    
    if active_questionnaire:
        await update.message.reply_text(
            "У вас уже есть активная анкета. Дождитесь ответа врача.",
            reply_markup=keyboard()
        )
        session.close()
        return MAIN_MENU
    
    try:
        questionnaire = Questionnaire(
            user_id=user_id,
            symptoms=symptoms,
            status='Новый'
        )
        session.add(questionnaire)
        session.commit()
        await update.message.reply_text(
            "Анкета сохранена! Ожидайте ответа врача.",
            reply_markup=keyboard()
        )
    except Exception as e:
        session.rollback()
        logger.error(f"Ошибка сохранения анкеты: {e}")
        await update.message.reply_text(
            "Произошла ошибка при сохранении анкеты. Попробуйте позже.",
            reply_markup=keyboard()
        )
    finally:
        session.close()
    
    return MAIN_MENU

async def save_recommendations(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('user_id') != 13:
        await update.message.reply_text("Эта функция доступна только врачам.")
        return MAIN_MENU

    if 'current_q' not in context.user_data:
        await update.message.reply_text("Анкета не выбрана.")
        return MAIN_MENU

    q_id = context.user_data['current_q']
    recommendations = update.message.text
    session = create_session()
    try:
        questionnaire = session.query(Questionnaire).get(q_id)
        if questionnaire:
            questionnaire.recommendations = recommendations
            questionnaire.status = 'Завершено'
            session.commit()
            await update.message.reply_text("Рекомендации успешно сохранены!")
        else:
            await update.message.reply_text("Анкета не найдена!")
    except Exception as e:
        session.rollback()
        logger.error(f" {e}")
        await update.message.reply_text(" Произошла ошибка. Попробуйте позже.")
    finally:
        session.close()

    return MAIN_MENU













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

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = """
Доступные команды:

/start - Начать работу с ботом
/help - Получить справку
/profile - Просмотреть профиль
/planning_tasks - Запланировать задачу
/health - Тесты здоровья
/weather - Узнать погоду
/bmi_stats - Статистика BMI

Тесты здоровья:
/bmi - Индекс массы тела
/flexibility - Тест на гибкость
/pushups - Тест отжиманий
/cooper - Тест Купера
/mile - Тест "Мили"
/ask - Консультация с AI
/cancel - Отмена действия
"""
    await update.message.reply_text(help_text, reply_markup=keyboard())

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = context.user_data['user_id']
    session = create_session()
    user = session.query(User).filter(User.id == user_id).first()
    tests = session.query(HealthTest).filter(HealthTest.user_id == user_id).all()
    
    profile_text = f"""
Ваш профиль:

Имя: {user.name}
Возраст: {user.age}
Email: {user.email}
Телефон: {user.phone}

Результаты тестов:
"""

    if not tests:
        profile_text += "\nНет результатов тестов"
    else:
        for test in tests:
            profile_text += f"\n{test.test_type}: {test.result}"

    await update.message.reply_text(profile_text, reply_markup=keyboard())
    session.close()

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






async def ask_gpt(prompt: str) -> str:
    try:
        response = await g4f.ChatCompletion.create_async(
            model=g4f.models.gpt_4,
            messages=[{"role": "user", "content": prompt}],
        )
        return response if response else "Не удалось получить ответ"
    except Exception as e:
        return f"Ошибка: {str(e)}"

async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = ' '.join(context.args)
    
    if not user_input:
        await update.message.reply_text("Пожалуйста, укажите симптомы после команды\nПример: /ask головная боль")
        return
    
    await update.message.reply_text("Обрабатываю запрос...")
    
    prompt = f"""Дай медицинский ответ на русском языке. 
    Запрос: {user_input}
    Формат ответа:
    1. Возможные причины
    2. Рекомендации
    3. Когда обратиться к врачу
    """
    
    response = await ask_gpt(prompt)
    await update.message.reply_text(f"Результат по запросу '{user_input}':\n\n{response}")





def main():
    application = ApplicationBuilder().token("7871402870:AAE8IaiUJy-CEO2OOWVvDmAwdpntbFg4eBU").build()

    main_conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            MAIN_MENU: [
                CommandHandler('planning_tasks', planning_tasks),
                CommandHandler('health', health_menu),
                CommandHandler('weather', weather_command),
                CommandHandler('bmi_stats', bmi_stats),
                CallbackQueryHandler(questionnaire_button, pattern="^q_"),
                CommandHandler('restart', restart_command),
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
            DOC_RESPONSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_recommendations)],
            HEALTH_MENU: [
                CommandHandler('bmi', bmi_start),
                CommandHandler('flexibility', flexibility_test),
                CommandHandler('pushups', pushups_test),
                CommandHandler('cooper', cooper_test),
                CommandHandler('mile', mile_test),
                CommandHandler('new_case', start_questionnaire),
                CommandHandler('ask', ask_command),
                CommandHandler('cancel', cancel)
],

            BMI_WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bmi_weight)],
            BMI_HEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, bmi_height)],
            FLEXIBILITY_TEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_flexibility)],
            PUSHUPS_TEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_pushups)],
            COOPER_TEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_cooper)],
            MILE_TEST: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_mile)],
            QUESTIONNAIRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_questionnaire)],


           
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    application.add_handler(CommandHandler('view_cases', view_questionnaires))
    application.add_handler(CommandHandler('check_questionnaire', check_questionnaire))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('profile', profile))
   
    application.add_handler(main_conv)
    application.run_polling()

if __name__ == '__main__':
    main()