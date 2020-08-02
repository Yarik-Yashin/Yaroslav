import sqlite3
from bs4 import BeautifulSoup
import requests
import asyncio
import datetime
import telebot
from token import token

bot = telebot.TeleBot(token)
db = sqlite3.connect('data.db')  # Подрубаемся к бд
cursor = db.cursor()
list_of_stocks = {'fl': "https://www.fl.ru/projects/"}  # Список бирж
keywords = ['парсер', 'парсинг', 'спарсить', 'python', 'бот', 'telegram', 'viber', 'vk', 'телеграм', 'flask']
keywords1 = list(map(lambda x: x.capitalize(), keywords))
keywords += keywords1


async def check():
    """
    Функция проверяет есть ли новые записи в бд, и есть ли в них keywords, если есть - отправляем сообщение в телеге

    """
    await asyncio.sleep(30)

    not_posted = cursor.execute("SELECT * FROM orders WHERE was_posted != 1").fetchone()
    if not_posted:
        bot.send_message(chat_id=588084243,
                         text=f"Заказ: {not_posted[1]} "
                              f"Биржа: {not_posted[2]} "
                              f"Цена: {not_posted[3]} ")
        # Ты потом поковыряйся с ботом и добавь еще отправку на свой chat id
        cursor.execute("""
                        UPDATE orders
                        SET was_posted = 1
                        WHERE was_posted == 0
                             """)


async def parse_fl():
    """
    Функция для поиска на FL
    """
    print('Парсим с fl')
    await asyncio.sleep(20)
    r = requests.get(list_of_stocks['fl']).text  # Get запрос на сайт
    html = BeautifulSoup(r, 'html.parser')
    orders = html.find_all('div', class_='b-post')  # Все заказы
    for i in orders:
        name = i.h2.text.replace('\n', '')
        price = str(i.script).split()[-2].replace('&nbsp;',
                                                  '')
        time = datetime.datetime.now()
        stock = 'Fl'
        name_lower = name.lower().split()
        isname = True
        for i in cursor.execute("SELECT title FROM orders").fetchall():
            if name in i:
                isname = False
        if isname and (set(name_lower) & set(keywords)):
            # Если имени нет в бд и там есть ключевые слова - заносим в бд
            cursor.execute("INSERT INTO orders (title, stock, price, times, was_posted) VALUES (?, ?, ?, ?, ?)",
                           (name, stock, price, time, 0))
            db.commit()


if __name__ == '__main__':
    """
    Сложные асинхронные штуки, которые я не смогу объяснить даже если захочу, но смысл в том, что мы одновременно будем
     парсить и писать в телеге
    """
    while True:
        ioloop = asyncio.get_event_loop()
        tasks = [ioloop.create_task(parse_fl()),
                 ioloop.create_task(check())]  # Сюда также добавь функцию как у меня сделано
        wait_tasks = asyncio.wait(tasks)
        ioloop.run_until_complete(wait_tasks)
