import logging
import os
import time

import requests
from telegram import Bot, TelegramError
from dotenv import load_dotenv
from requests import RequestException

from exceptions import (StatusCodeError, BotSendMessageError)

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TOKENS = ['PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']
RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """Функция отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.info(f'Бот отправил сообщение "{message}"')
    except TelegramError as error:
        logging.error(f'{error}, Бот не отправил сообщение '
                      f'{message}', exc_info=True)
        raise BotSendMessageError(f'Бот не отправил сообщение {message}')


def get_api_answer(current_timestamp):
    """Функция делает запрос к API-сервиса."""
    params = {'from_date': current_timestamp}
    try:
        statuses = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except RequestException as error:
        raise ConnectionError(f'Ошибка доступа {error}. '
                              f'Проверить API: {ENDPOINT}, '
                              f'токен авторизации: {HEADERS}, '
                              f'апрос с момента времени: {params}')
    if statuses.status_code != 200:
        raise StatusCodeError(
            f'Ошибка ответа сервера. Проверить API: {ENDPOINT}, '
            f'токен авторизации: {HEADERS}, '
            f'запрос с момента времени: {params},'
            f'код возврата {statuses.status_code}'
        )
    return statuses.json()


def check_response(response):
    """Функция проверяет ответ API на корректность."""
    if not isinstance(response, dict):
        raise TypeError('В ответ от сервиса API нет словаря.')
    if 'homeworks' not in response:
        raise KeyError('Нет ключа homeworks в ответе от сервиса API')
    homeworks = response['homeworks']
    if not isinstance(response['homeworks'], list):
        raise TypeError('Ответ от сервиса API нет представлен списком.')
    return homeworks


def parse_status(homework):
    """Функция проверяет информацию о статусе домашней работы."""
    name = homework['homework_name']
    status = homework['status']
    if VERDICTS is None:
        raise KeyError(f'Отсутствует домашняя работа {VERDICTS}')
    if status not in VERDICTS:
        raise ValueError(f'Неизвестный статус домашней работы {status}')
    return f'Изменился статус проверки работы "{name}". {VERDICTS[status]}'


def check_tokens():
    """Функция проверяет доступность переменных окружения."""
    for name in TOKENS:
        if globals()[name] is None:
            logging.info(f'Проверьте {name} токен')
            return False
    return True


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        raise ValueError('Проверьте значение токенов')
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            logging.info("Статус домашней работы")
            if not homeworks:
                logging.info("Новые статусы отсутствуют.")
            else:
                send_message(bot, parse_status(homeworks[0]))
            current_timestamp = response.get(
                'current_date', 'current_timestamp'
            )
            time.sleep(RETRY_TIME)
        except Exception as error:
            logging.error(f'Сбой в работе программы: {error}')


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    LOG_FILE = __file__ + '.log'
    logging.basicConfig(
        level=logging.INFO,
        filename='homework_bot.log',
        filemode='w',
        format='%(asctime)s, %(levelname)s, %(name)s, %(message)s',
    )
    try:
        main()
    except KeyboardInterrupt:
        print('Выход из программы')
