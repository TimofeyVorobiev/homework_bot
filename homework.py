import logging
import os
import sys
import time

import requests
import telegram
from dotenv import load_dotenv
from requests import RequestException

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600

ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'

HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
ERROR = 'Ошибка: {0}'

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logger = logging.getLogger(__name__)
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s',
)
logger.addHandler(logging.StreamHandler())


def send_message(bot, message):
    """Бот отправляет сообщения."""
    logger.info(f'Отправка сообщения: {message}')
    bot_message = bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    if not bot_message:
        logger.info(f'Ошибка при отправке: {message}')
    else:
        logger.info(f'Отправка сообщения: {message}')


def get_api_answer(current_timestamp):
    """Отправляет запрос к API."""
    params = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params
        )
        if homework_statuses.status_code != 200:
            raise Exception('Сервер не работает.')
        return homework_statuses.json()
    except RequestException as error:
        logging.error('Ошибочный запрос')
        raise error


def check_response(response):
    """Ответ от сервера с домашней работой."""
    try:
        homeworks = response['homeworks']
    except KeyError:
        raise KeyError('Нет ключа homeworks')
    if not isinstance(homeworks, list) and homeworks:
        raise Exception('Нет homeworks')
    return homeworks


def parse_status(homework):
    """Извлекает статус работы."""
    name = homework.get('homework_name')
    status = homework.get('status')
    if status not in HOMEWORK_VERDICTS:
        raise KeyError(f'Неизвестный статус {status}')
    return f'Изменился статус проверки работы "{name}". ' \
           f'{HOMEWORK_VERDICTS.get(status)}'


def check_tokens():
    """Проверка значения переменных TOKENS."""
    tokens = (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
    return all(tokens)


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        raise Exception(
            "Проверить PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID.")
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if isinstance(homeworks, list) and homeworks:
                send_message(bot, parse_status(homeworks[0]))
            else:
                logger.info("Работы нет")
            current_timestamp = response.get('current_date'[1])
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message, exc_info=True)
            send_message(bot, message)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Выход из программы')
