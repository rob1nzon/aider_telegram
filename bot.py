import os
import subprocess
import telebot
import threading
import time
import random
import requests
from telebot import types
import sys
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Получаем значения из .env
BOT_TOKEN = os.getenv('BOT_TOKEN')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')
ALLOWED_USERS = [int(id) for id in os.getenv('ALLOWED_USERS', '').split(',') if id]

# Создаем бота
bot = telebot.TeleBot(BOT_TOKEN)

def get_weather(city):
    """
    Функция для получения погоды в городе
    """
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': city,
        'appid': WEATHER_API_KEY,
        'units': 'metric',
        'lang': 'ru'
    }
    
    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        
        if response.status_code == 200:
            temp = data['main']['temp']
            feels_like = data['main']['feels_like']
            description = data['weather'][0]['description']
            
            weather_message = (
                f"Погода в {city}:\n"
                f"Температура: {temp}°C\n"
                f"Ощущается как: {feels_like}°C\n"
                f"Описание: {description}"
            )
            return weather_message
        else:
            return f"Не удалось получить погоду для города {city}"
    
    except Exception as e:
        return f"Произошла ошибка: {str(e)}"

def run_aider(message):
    """
    Функция для запуска aider с переданным текстом
    """
    try:
        # Извлекаем текст после команды /aider
        text = message.text.replace('/aider', '').strip()
        
        if not text:
            bot.reply_to(message, "Пожалуйста, введите текст после команды /aider")
            return
        
        # Запускаем aider с переданным текстом
        process = subprocess.Popen(
            ['aider', '--model', 'openrouter/anthropic/claude-3-5-haiku', 'bot.py', '-m "', text, '"'], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True
        )
        
        # Получаем вывод
        stdout, stderr = process.communicate()
        
        # Отправляем результат
        if stdout:
            bot.reply_to(message, f"Результат:\n{stdout}")
        if stderr:
            bot.reply_to(message, f"Ошибка:\n{stderr}")
    
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка: {str(e)}")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """
    Обработчик команды /start
    """
    if message.from_user.id not in ALLOWED_USERS:
        bot.reply_to(message, "У вас нет доступа к этому боту.")
        return
    
    bot.reply_to(message, "Привет! Я бот для работы с aider. Используйте /aider [текст]")

@bot.message_handler(commands=['aider'])
def handle_aider_command(message):
    """
    Обработчик команды /aider
    """
    if message.from_user.id not in ALLOWED_USERS:
        bot.reply_to(message, "У вас нет доступа к этому боту.")
        return
    
    run_aider(message)

@bot.message_handler(commands=['dice'])
def roll_dice(message):
    """
    Обработчик команды /dice для броска кубика
    """
    if message.from_user.id not in ALLOWED_USERS:
        bot.reply_to(message, "У вас нет доступа к этому боту.")
        return
    
    # Бросок кубика для пользователя
    user_roll = random.randint(1, 6)
    
    # Бросок кубика для бота
    bot_roll = random.randint(1, 6)
    
    # Определение победителя
    if user_roll > bot_roll:
        result = "Вы выиграли! 🎉"
    elif user_roll < bot_roll:
        result = "Я выиграл! 🤖"
    else:
        result = "Ничья! 🤝"
    
    # Отправка результатов
    response = (
        f"Вы бросили кубик и выпало: {user_roll} 🎲\n"
        f"Я бросил кубик и выпало: {bot_roll} 🎲\n"
        f"{result}"
    )
    
    bot.reply_to(message, response)

@bot.message_handler(commands=['weather'])
def handle_weather_command(message):
    """
    Обработчик команды /weather для получения погоды
    """
    if message.from_user.id not in ALLOWED_USERS:
        bot.reply_to(message, "У вас нет доступа к этому боту.")
        return
    
    # Извлекаем название города после команды /weather
    city = message.text.replace('/weather', '').strip()
    
    if not city:
        bot.reply_to(message, "Пожалуйста, укажите город после команды /weather")
        return
    
    # Получаем и отправляем погоду
    weather_info = get_weather(city)
    bot.reply_to(message, weather_info)

def start_bot():
    """
    Функция для запуска бота с автоперезагрузкой
    """
    while True:
        try:
            print("Запуск бота...")
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Произошла ошибка: {e}")
            print("Перезапуск бота через 5 секунд...")
            time.sleep(5)

def restart_script():
    """
    Функция для перезапуска скрипта
    """
    print("Перезапуск скрипта...")
    python = sys.executable
    os.execl(python, python, *sys.argv)

def watch_for_changes():
    """
    Функция для отслеживания изменений в скрипте
    """
    script_path = os.path.abspath(__file__)
    last_modified = os.path.getmtime(script_path)
    
    while True:
        current_modified = os.path.getmtime(script_path)
        if current_modified != last_modified:
            print("Обнаружены изменения в скрипте. Перезапуск...")
            restart_script()
        
        time.sleep(1)

def main():
    # Создаем потоки
    bot_thread = threading.Thread(target=start_bot)
    watcher_thread = threading.Thread(target=watch_for_changes)
    
    # Запускаем потоки
    bot_thread.start()
    watcher_thread.start()
    
    # Ждем завершения потоков
    bot_thread.join()
    watcher_thread.join()

if __name__ == '__main__':
    main()
