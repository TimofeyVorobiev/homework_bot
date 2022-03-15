import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv
from requests import RequestException

from exceptions import (NoStatusCodeError,
                        NoKeyHomeworksCurrentDateError,
                        )
TokenError = 'Отстутствует переменная окружения {name}'

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TOKENS = ('PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID')
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
    except Exception:
        logging.error(f'Бот не отправил сообщение "{message}"', exc_info=True)


def get_api_answer(current_timestamp):
    """Функция делает запрос к API-сервиса."""
#  timestamp = current_timestamp or int(time.time())
    params = {'from_date': current_timestamp}
    try:
        statuses = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except RequestException as error:
        raise ConnectionError (f'Ошибка доступа {error}. '
        f'Проверить API: {ENDPOINT}, '
        f'токен авторизации: {HEADERS}, запрос с момента времени: {params}')
    if statuses.status_code != 200:
        raise NoStatusCodeError(
        f'Ошибка ответа сервера. Проверить API: {ENDPOINT}, '
        f'токен авторизации: {HEADERS}, запрос с момента времени: {params}'
    )
    return statuses.json()


def check_response(response):
    """Функция проверяет ответ API на корректность."""
    if not isinstance(response, dict):
        message = 'Получен некорректный тип данных от сервиса API.'
        raise TypeError(message)
    if 'homeworks' not in response:
        message = 'Получен некорректный ответ от сервиса API.'
        raise NoKeyHomeworksCurrentDateError(message)
    if not isinstance(response['homeworks'], list):
        message = 'В ответе от сервиса API нет списка домашних работ.'
        raise TypeError(message)
    homeworks = response['homeworks']
    return homeworks


def parse_status(homework):
    """Функция проверяет информацию о статусе домашней работы."""
    name = homework.get('homework_name')
    status = homework.get('status')
    if name is None:
        message = f'Отсутствует домашняя работа {status}'
        raise KeyError(message)
    if status not in VERDICTS:
        message = f'Неизвестный статус домашней работы {status}'
        raise ValueError(message)
    return f'Изменился статус проверки работы "{name}". {VERDICTS[status]}'


def check_tokens():
    """Функция проверяет доступность переменных окружения."""
    token_check = [logging.critical(TokenError.format(name=name))
                   for name in TOKENS if globals()[name] is None]
    if token_check:
        return False
    return True


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        message = 'Проверьте значение токенов'
        raise ValueError(message)
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    error_message = ""
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            logging.info("Статус домашней работы")
            if not homeworks:
                logging.debug("Новые статусы отсутствуют.")
            current_timestamp = response.get('current_date')
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            if message != error_message:
                send_message(bot, message)
                error_message = message


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
    LOG_FILE = __file__ + '.log'
    logging.basicConfig(
        level=logging.INFO,
        filename='homework_bot.log',
        filemode='a',
        format='%(asctime)s, %(levelname)s, %(name)s, %(message)s',
    )
    try:
        main()
    except KeyboardInterrupt:
        print('Выход из программы')
