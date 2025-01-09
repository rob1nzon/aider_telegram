import os
import subprocess
import telebot
import threading
import time
from telebot import types
import sys
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Получаем значения из .env
BOT_TOKEN = os.getenv('BOT_TOKEN')
ALLOWED_USERS = [int(id) for id in os.getenv('ALLOWED_USERS', '').split(',') if id]

# Создаем бота
bot = telebot.TeleBot(BOT_TOKEN)

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
            ['aider', text], 
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

