import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    message = f'Бот {message}'
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)


def get_api_answer(current_timestamp):
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    statuses = requests.get(ENDPOINT, headers=HEADERS, params=params)
    return statuses.json()


def check_response(response):
    homeworks = response['homeworks']
    return homeworks


def parse_status(homework):
    name = homework["homework_name"]
    status = homework["status"]
    return f'Изменился статус проверки работы "{name}".' \
           f' {HOMEWORK_VERDICTS[status]}'


def check_tokens():
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        return True
    else:
        return False


def main():
    """Основная логика работы бота."""
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
            for homework in homeworks:
                send_message(bot, parse_status(homework))
            current_timestamp = response["current_date"]
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            if error_message != message:
                send_message(bot, message)
                error_message = message
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logger = logging.getLogger(__name__)
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
