MENU = """
*Список підтримуваних команд:*
 - /start - почати роботу з ботом
 - /list - список підписок
 - /add - підписатися на нові сповіщення
 - /unsubscribe - відписатися від всіх сповіщень
 - /help - отримати довідку
"""


ADMIN_MENU = """
*Список підтримуваних команд:*
 - /start - почати роботу з ботом
 - /list - список підписок
 - /add - підписатися на нові сповіщення
 - /post - сворити оголошення про роботу
 - /stat - отримати посилання для статистики
 - /greeting - змінити привітання для бота
 - /unsubscribe - відписатися від всіх сповіщень
 - /help - отримати довідку
"""

DEFAULT_GREETING = "Привіт я телеграм бот який буде шукати роботу за тебе"

PAGINATION_SIZE = 5

HOST = 'https://dou-jobs-telegram-bot.herokuapp.com'

ALL_COMMANDS = [
    'start',
    'list',
    'add',
    'post',
    'stat',
    'greeting',
    'unsubscribe',
    'help',
]


DEFAULT_GROUP = 1000