import telebot
from telebot import types
import os
import json
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN = os.getenv("ADMIN_USERNAME")
RENT_AMOUNT = int(os.getenv("RENT_AMOUNT", 15000))

bot = telebot.TeleBot(TOKEN)

DATA_FILE = "data.json"

# загрузка данных
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        data = json.load(f)
        drivers = data.get("drivers", {})
        cars = data.get("cars", ["451BIA05", "651BKD05", "502BKN05", "670BNJ05", "807BNM05"])
else:
    drivers = {}
    cars = ["451BIA05", "651BKD05", "502BKN05", "670BNJ05", "807BNM05"]

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump({"drivers": drivers, "cars": cars}, f)

@bot.message_handler(commands=['start'])
def start(message):
    username = message.from_user.username
    if username not in drivers:
        msg = bot.send_message(message.chat.id, "Введите имя:")
        bot.register_next_step_handler(msg, reg_name)
    else:
        menu(message)

def reg_name(message):
    name = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for car in cars:
        markup.add(car)
    msg = bot.send_message(message.chat.id, "Выбери машину:", reply_markup=markup)
    bot.register_next_step_handler(msg, reg_car, name)

def reg_car(message, name):
    car = message.text
    if car not in cars:
        bot.send_message(message.chat.id, "Ошибка, выбери из списка")
        return start(message)
    username = message.from_user.username
    drivers[username] = {"name": name, "car": car, "paid": 0, "debt": RENT_AMOUNT}
    cars.remove(car)
    save_data()
    bot.send_message(message.chat.id, f"Готово! {car} твоя")
    menu(message)

def menu(message):
    username = message.from_user.username
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Оплатил")
    if username == ADMIN:
        markup.add("Статус", "Добавить авто", "Удалить водителя")
    if username in drivers:
        bot.send_message(message.chat.id, f"Долг: {drivers[username]['debt']} тг")
    bot.send_message(message.chat.id, "Меню:", reply_markup=markup)

@bot.message_handler(content_types=['text'])
def text_handler(message):
    username = message.from_user.username
    text = message.text

    if text == "Оплатил":
        msg = bot.send_message(message.chat.id, "Сколько оплатил?")
        bot.register_next_step_handler(msg, pay)

    elif text == "Статус" and username == ADMIN:
        s = "Статус:\n"
        for u, d in drivers.items():
            s += f"{d['car']} - {d['name']} | {d['paid']} | долг {d['debt']}\n"
        bot.send_message(message.chat.id, s)

    elif text == "Добавить авто" and username == ADMIN:
        msg = bot.send_message(message.chat.id, "Номер авто:")
        bot.register_next_step_handler(msg, add_car)

    elif text == "Удалить водителя" and username == ADMIN:
        msg = bot.send_message(message.chat.id, "username:")
        bot.register_next_step_handler(msg, del_driver)

    else:
        menu(message)

def pay(message):
    username = message.from_user.username
    try:
        amount = int(message.text)
    except:
        bot.send_message(message.chat.id, "Введите число")
        return

    drivers[username]["paid"] += amount
    drivers[username]["debt"] = max(0, RENT_AMOUNT - drivers[username]["paid"])
    save_data()

    bot.send_message(message.chat.id, f"Принял {amount}. Долг: {drivers[username]['debt']}")
    menu(message)

def add_car(message):
    car = message.text
    if car not in cars:
        cars.append(car)
        save_data()
        bot.send_message(message.chat.id, "Добавлено")
    else:
        bot.send_message(message.chat.id, "Уже есть")
    menu(message)

def del_driver(message):
    uname = message.text
    if uname in drivers:
        car = drivers[uname]["car"]
        cars.append(car)
        del drivers[uname]
        save_data()
        bot.send_message(message.chat.id, "Удалён")
    else:
        bot.send_message(message.chat.id, "Нет такого")
    menu(message)

bot.infinity_polling()
