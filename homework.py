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

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

TOKEN_ERRORS = ['Проверить значение "TELEGRAM_TOKEN"',
                'Проверить значение "TELEGRAM_CHAT_ID"',
                'Проверить значение "PRACTICUM_TOKEN"']

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
        raise telegram.TelegramError(f'Ошибка при отправке: {message}')
    else:
        logger.info(f'Отправка сообщения: {message}')


def get_api_answer(ENDPOINT, current_timestamp):
    """Отправляет запрос к API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT, headers=HEADERS, params=params)
        if homework_statuses.status_code == 500:
            raise Exception('Нет ответа от сервера')
        if homework_statuses.status_code != 200:
            raise Exception('Ошибка в коде состояния HTTP')
    except RequestException as error:
        logging.error(error)
        raise RequestException(
            'Ошибка ответа от сервера')

    return homework_statuses.json()

def check_response(response):
    """Ответ от сервера с домашней работой."""
    try:
        homeworks = response['homeworks']
    except KeyError:
        raise KeyError('Нет ключа homeworks')
    return homeworks


def parse_status(homework: dict) -> str:
    """Извлекает статус работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_STATUSES:
        raise KeyError(f'Неизвестный статус {homework_status}')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверка значения переменных TOKENS."""
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        return True
    logging.error('Проверить значения TOKENS')
    return False


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(ENDPOINT, current_timestamp)
            homework = check_response(response)
            logger.info("Домашняя работа")
            if isinstance(homework, list) and homework:
                send_message(bot, parse_status(homework))
            else:
                logger.info("Работы нет")
            current_timestamp = response['current_date']
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message, stack_info=True)
            send_message(bot, message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Выход из программы')
        sys.exit(0)
