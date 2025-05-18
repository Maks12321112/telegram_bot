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
YANDEX_WEATHER_API_KEY = "90ecda6d-72cb-4436-b48e-65a22dad3143"
YANDEX_GEOCODER_API_KEY = "8013b162-6b42-4997-9691-77b7074026e0"
(MAIN_MENU, AUTH_CHOICE, NAME, AGE, EMAIL, PHONE, PASSWORD, LOGIN_EMAIL, LOGIN_PASSWORD,
TASK_TIME, HEALTH_MENU, BMI_WEIGHT, BMI_HEIGHT,
FLEXIBILITY_TEST, PUSHUPS_TEST, COOPER_TEST, MILE_TEST, WAITING_CITY) = range(18)
def keyboard():
    return ReplyKeyboardMarkup([
        ['/planning_tasks', '/health'],
        ['/profile', '/help',
         '/weather'],
         ['/bmi_stats']
    ], resize_keyboard=True)
import requests


async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Введите название города:")
    return WAITING_CITY

async def handle_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    city_name = update.message.text
    weather_info = get_weather(city_name, YANDEX_WEATHER_API_KEY, YANDEX_GEOCODER_API_KEY)
    
    if 'error' in weather_info:
        await update.message.reply_text(f"Ошибка: {weather_info['error']}")
    else:
        response = (
            f"🌍 Погода в городе: {weather_info['город']}\n"
            f"🌡 Температура: {weather_info['температура']}°C\n"
            f"💭 Ощущается как: {weather_info['ощущается_как']}°C\n"
            f"☁️ Облачность: {weather_info['облачность']}\n"
            f"🌈 Условия: {weather_info['условия']}\n"
            f"🌬 Ветер: {weather_info['ветер']}\n"
            f"💧 Влажность: {weather_info['влажность']}\n"
            f"⏱ Давление: {weather_info['давление']}"
        )
        await update.message.reply_text(response, reply_markup=keyboard())
    
    return MAIN_MENU

def get_weather(city_name, yandex_weather_api_key, yandex_geocoder_api_key):
    geocoder_url = f"https://geocode-maps.yandex.ru/1.x/?apikey={yandex_geocoder_api_key}&format=json&geocode={city_name}"
    
    
    geocoder_response = requests.get(geocoder_url)
    geocoder_response.raise_for_status()
    geocoder_data = geocoder_response.json()
        
    if not geocoder_data.get('response', {}).get('GeoObjectCollection', {}).get('featureMember'):
        return {"error": "Город не найден"}
            
    pos = geocoder_data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['Point']['pos']
    longitude, latitude = pos.split()
        
    weather_url = f"https://api.weather.yandex.ru/v2/forecast?lat={latitude}&lon={longitude}"
    headers = {'X-Yandex-Weather-Key': yandex_weather_api_key}
        
    weather_response = requests.get(weather_url, headers=headers)
    weather_response.raise_for_status()
    weather_data = weather_response.json()
        
    return {
            "город": city_name,
            "температура": weather_data['fact']['temp'],
            "ощущается_как": weather_data['fact']['feels_like'],
            "облачность": get_cloudness(weather_data['fact']['cloudness']),
            "условия": get_condition(weather_data['fact']['condition']),
            "ветер": f"{weather_data['fact']['wind_speed']} м/с",
            "влажность": f"{weather_data['fact']['humidity']}%",
            "давление": f"{weather_data['fact']['pressure_mm']} мм рт.ст."
        }
        
    

def get_cloudness(value):
    cloudness = {
        0: "ясно",
        1: "малооблачно",
        2: "облачно с прояснениями",
        3: "пасмурно"
    }
    return cloudness.get(value, "неизвестно")

def get_condition(value):
    conditions = {
        "clear": "ясно",
        "partly-cloudy": "малооблачно",
        "cloudy": "облачно",
        "overcast": "пасмурно",
        "light-rain": "небольшой дождь",
        "rain": "дождь",
        "heavy-rain": "сильный дождь",
        "showers": "ливень",
        "wet-snow": "дождь со снегом",
        "light-snow": "небольшой снег",
        "snow": "снег",
        "snow-showers": "снегопад",
        "hail": "град",
        "thunderstorm": "гроза",
        "thunderstorm-with-rain": "дождь с грозой",
        "thunderstorm-with-hail": "гроза с градом"
    }
    return conditions.get(value, "неизвестно")