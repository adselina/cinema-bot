import telebot
import sqlite3

import datetime
import random
from telebot import types
from pathlib import Path

#req = f'https://kinopoiskapiunofficial.tech/api/v2.2/films/{filmID_1}/reviews' ДЛЯ ОТЗЫВОВ ПО ИД ФИЛЬМА

import requests
#from dostoevsky.tokenization import RegexTokenizer
#from dostoevsky.models import FastTextSocialNetworkModel


#Переменные
global cursor               #для выполнения запросов в бд
global sqlite_connection    #строка подключения
#Токены
#tokenizer = RegexTokenizer()
#model = FastTextSocialNetworkModel(tokenizer=tokenizer)
token = '_'
headers = {'X-API-KEY': '9152f2a7-2888-41df-b32f-eaad535ed8b3', 'Content-Type': 'application/json'}
bot = telebot.TeleBot('_')

#Проверка подключения к БД
def db_connection():
    global cursor
    global sqlite_connection
    try:
        sqlite_connection = sqlite3.connect('identifier.sqlite')
        cursor = sqlite_connection.cursor()
        print("БД успешно подключена")
    except sqlite3.Error as error:
        print("Ошибка при подключении к sqlite", error)

def db_table_val(user_id: int):
    global cursor  # для выполнения запросов в бд
    global sqlite_connection
    try:
        print (user_id)
        cursor.execute(f'INSERT INTO users (id) VALUES ({user_id})')
        sqlite_connection.commit()
        return True
    except sqlite3.Error:
            return False


#ПОИСК ФИЛЬМА
def get_film(genre: int):
    rand_page = random.randint(1,5)
    rand_film = random.randint(1,20)
    print(str(rand_page) + "  " + str(rand_film))
    req = f'https://kinopoiskapiunofficial.tech/api/v2.2/films?genres={genre}&type=ALL&ratingFrom=0&ratingTo=10&yearFrom=2010&yearTo={datetime.datetime.now().year}&page={rand_page}'
    response = requests.get(url=req, headers=headers);
    print (response.json())


    filmID = response.json()['items'][rand_film]['kinopoiskId']
    req_2 = f'https://kinopoiskapiunofficial.tech/api/v2.2/films/{filmID}'
    response = requests.get(url=req_2, headers=headers);

    #filmname = response.json()['nameRu']
    # Лена тут можно обратиться к [imdbId] чтобы искать отзывы там?
    #print (response.json())
    return response


#При первом подключении добавляем юзера в таблицу
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.send_message(message.from_user.id,
                     'Привет! Я бот, который подберет тебе фильм на вечер. Напиши /help, для просмотра команд')
    db_connection()

    flag = db_table_val(message.from_user.id)
    if flag:
        bot.send_message(message.from_user.id,
                     "Вы у нас первый раз? Мы добавили ваc, теперь вы сможете отмечать какие фильмы вы уже посмотрели и мы не будем вам их предлагать")
    else:
        bot.send_message(message.from_user.id, "Рады вас снова видеть!")


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    global cursor
    if message.text == "Привет" or message.text == "Начать":
        bot.send_message(message.from_user.id, text='Привет! Я бот, который подберет тебе фильм на вечер. Напиши /help, для просмотра команд')

    if message.text == "/help":
        bot.send_message(message.from_user.id, "Доступны следующие команды:"
                                               "\n/searchfilm - Найти фильм по настроению"
                                               "\n/randomfilm - Не знаете, что посмотреть?"
                                               "\n/recentsearch - То, что вы недавно искали"
                                               "\n/watchedfilms - То, что вы уже посмотрели"
                                               "\n/newfilms - Подборка новых фильмов")

    elif message.text == "/searchfilm":
        db_connection()
        global cursor
        keyboard = telebot.types.InlineKeyboardMarkup()
        sqlite_select_query = "Select * from genres"
        cursor.execute(sqlite_select_query)
        record = cursor.fetchall()
        for rec in record:
            keyboard.add(telebot.types.InlineKeyboardButton(text=f'{rec[1]}', callback_data=f'genre_{rec[0]}'))
        cursor.close()

        bot.send_message(message.from_user.id, text='Выберите жанр', reply_markup=keyboard)

    elif message.text == "/randomfilm":
        bot.send_message(message.from_user.id, "_")

    elif message.text == "/recentsearch":
        bot.send_message(message.from_user.id, "_")

    elif message.text == "/watchedfilms":
        bot.send_message(message.from_user.id, "_")

    elif message.text == "/newfilms":
        bot.send_message(message.from_user.id, "_")


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    if "genre" in call.data:
        response = get_film(call.data.split('_')[1])
        film_name = response.json()['nameRu']
        film_photo = response.json()['coverUrl']
        film_description = response.json()['description']
        film_year = response.json()['year']
        print(response.json()['ratingKinopoisk'])
        print(response.json()['ratingImdb'])
        print(response.json()['ratingFilmCritics'])
        film_ratingKinopoisk = response.json()['ratingKinopoisk']
        film_ratingImdb = response.json()['ratingImdb']

        try:
            average_rating = (float(film_ratingKinopoisk) + float(film_ratingImdb)) / 2
        except:
            average_rating = float(film_ratingKinopoisk)



        bot_rating = 0
        average_rating = round (average_rating,2)


        try:
            bot.send_photo(call.message.chat.id, film_photo)
        except:
            bot.send_photo(call.message.chat.id, "https://avatars.mds.yandex.net/i?id=164e005994fabf3781f078f28a858e90800bce62-7011746-images-thumbs&n=13")
        bot.send_message(call.message.chat.id, f"Как насчет \"{film_name}\"?"
                                               f"\nОценка на кинопоиске: {film_ratingKinopoisk} "
                                               f"\nГод: {film_year}"
                                               f"\nСредняя оценка: {average_rating}"
                                               f"\nОценка бота {bot_rating}"
                                               f"\n{film_description}")


bot.polling(none_stop=True, interval=0)