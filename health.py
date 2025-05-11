import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    CallbackContext
)
from datetime import datetime
import asyncio
import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
from forms.user import User
from forms.healthtest import HealthTest
from forms.tasks import Task
from sessions import *



logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)



def keyboard():
    return ReplyKeyboardMarkup([
        ['/planning_tasks', '/health'],
        ['/profile', '/help']
    ], resize_keyboard=True)


def get_auth_keyboard():
    return ReplyKeyboardMarkup([
        ['Войти', 'Зарегистрироваться']
    ], one_time_keyboard=True)


(
    MAIN_MENU, AUTH_CHOICE, NAME, AGE, EMAIL, PHONE, PASSWORD,
    TASK_TIME, HEALTH_MENU, BMI_WEIGHT, BMI_HEIGHT,
    FLEXIBILITY_TEST, PUSHUPS_TEST, COOPER_TEST, MILE_TEST
) = range(15)



def get_health_keyboard():
    return ReplyKeyboardMarkup([
        ['/bmi', '/flexibility'],
        ['/pushups', '/cooper'],
        ['/mile', '/cancel']
    ], resize_keyboard=True)


async def pushups_test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Введите количество отжиманий, которые вы смогли выполнить:",
        reply_markup=get_health_keyboard()
    )
    return PUSHUPS_TEST


async def cooper_test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Введите расстояние (в метрах), которое вы пробежали за 12 минут:",
        reply_markup=get_health_keyboard()
    )
    return COOPER_TEST


async def mile_test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Введите время (в минутах), за которое вы пробежали 1 милю:",
        reply_markup=get_health_keyboard()
    )
    return MILE_TEST


async def handle_pushups(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:

    try:
        pushups_count = int(update.message.text)
        user_id = update.message.from_user.id
        
        session = create_session()
        try:
            user = session.query(User).filter(User.id == context.user_data['user_id']).first()
            if user:
                test = HealthTest(
                    user_id=user.id,
                    test_type="Pushups",
                    result=str(pushups_count))
                session.add(test)
                session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка сохранения теста: {e}")
        finally:
            session.close()
        

        if pushups_count < 10:
            msg = "Низкий уровень силы."
        elif 10 <= pushups_count < 20:
            msg = "Средний уровень силы."
        else:
            msg = "Высокий уровень силы."
            
        await update.message.reply_text(
            f"Результат: {pushups_count} отжиманий. {msg}",
            reply_markup=get_health_keyboard()
        )
        return HEALTH_MENU
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число!")
        return PUSHUPS_TEST


async def handle_cooper(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        distance = float(update.message.text)
        user_id = update.message.from_user.id

        session = create_session()
        try:
            user = session.query(User).filter(User.id == context.user_data['user_id']).first()
            if user:
                test = HealthTest(
                    user_id=user.id,
                    test_type="Cooper",
                    result=str(distance))
                session.add(test)
                session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка сохранения теста: {e}")
        finally:
            session.close()

        if distance < 2400:
            msg = "Низкий уровень выносливости."
        elif 2400 <= distance < 3000:
            msg = "Средний уровень выносливости."
        else:
            msg = "Высокий уровень выносливости."
            
        await update.message.reply_text(
            f"Результат: {distance} метров. {msg}",
            reply_markup=get_health_keyboard()
        )
        return HEALTH_MENU
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число")
        return COOPER_TEST


async def handle_mile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        time = float(update.message.text)
        user_id = update.message.from_user.id

        session = create_session()
        try:
            user = session.query(User).filter(User.id == context.user_data['user_id']).first()
            if user:
                test = HealthTest(
                    user_id=user.id,
                    test_type="Mile",
                    result=str(time))
                session.add(test)
                session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка сохранения теста: {e}")
        finally:
            session.close()

        if time < 8:
            msg = "Отличная сердечно-сосудистая выносливость"
        elif 8 <= time < 10:
            msg = "Хорошая сердечно-сосудистая выносливост"
        else:
            msg = "Нужна работа над выносливостью"
            
        await update.message.reply_text(
            f"Результат: {time} минут. {msg}",
            reply_markup=get_health_keyboard()
        )
        return HEALTH_MENU
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите число")
        return MILE_TEST