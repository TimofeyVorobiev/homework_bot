import logging
import os
import time
from http import HTTPStatus
from json import JSONDecodeError

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


def send_message(bot, message):
    """Бот отправляет сообщения."""
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        logging.info(f'Отправка сообщения: {message}')
    except Exception as error:
        logging.exception(
            f'Сообщение {message} не отправлено, ошибка: {error}'
        )


def get_api_answer(current_timestamp):
    """Отправляет запрос к API."""
    params = {'from_date': current_timestamp}
    try:
        homework_statuses = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params
        )
        if homework_statuses.status_code != HTTPStatus.OK:
            raise Exception('Сервер не работает.')
        return homework_statuses.json()
    except RequestException as error:
        logging.error('Ошибки в запросе к серверу, '
                      'проверьте ENDPOINT, HEADERS')
        raise error
    except JSONDecodeError:
        logging.error('Ответ от сервера не в формате JSON')


def check_response(response):
    """Ответ от сервера с домашней работой."""
    try:
        homeworks = response['homeworks']
    except KeyError:
        raise KeyError('Нет ключа homeworks')
    if not isinstance(homeworks, list):
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
    """Проверяет доступность переменных окружения."""
    if not PRACTICUM_TOKEN:
        logging.critical(f'Ошибка в {PRACTICUM_TOKEN}')
        return False
    if not TELEGRAM_TOKEN:
        logging.critical(f'Ошибка в {TELEGRAM_TOKEN}')
        return False
    if not TELEGRAM_CHAT_ID:
        logging.critical(f'Ошибка в {TELEGRAM_CHAT_ID}')
        return False
    return True


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        raise ValueError('Ошибка, связанная с токенами')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    message = ''
    prev_message = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                send_message(bot, parse_status(homeworks[0]))
            if message != prev_message:
                send_message(bot, message)
                prev_message = message
            else:
                logger.info("Работы нет")
            current_timestamp = response['current_date']
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message, exc_info=True)


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        level=logging.INFO,
        filename='main.log',
        filemode='a',
        format='%(asctime)s, %(levelname)s, %(name)s, %(message)s',
    )
    try:
        main()
    except KeyboardInterrupt:
        print('Выход из программы')
