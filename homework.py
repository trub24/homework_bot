import logging
import logging.handlers
import os
import requests
import time
import sys
from http import HTTPStatus
from dotenv import load_dotenv
from telebot import TeleBot


load_dotenv()


PRACTICUM_TOKEN = os.getenv('TOKEN_YA_PRACT')
TELEGRAM_TOKEN = os.getenv('TOKEN_TELEGA')
TELEGRAM_CHAT_ID = os.getenv('TOKEN_TELEGA_CHAT')


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG,
)


RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка доступности переменных окружения."""
    token_list = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]
    for token in token_list:
        if token is None:
            logging.critical(
                f'Отсутствует обязательная переменная окружения: {token}.'
                'Программа принудительно остановлена.')
            return False
    return True


def send_message(bot, message):
    """Отправка сообщений в в Telegram-чат."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message
        )
        logging.debug('Сообщение отправлено')
    except Exception:
        logging.error('сбой при отправке сообщения')


def get_api_answer(timestamp):
    """запрос к эндпоинту API-сервиса."""
    try:
        homework = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params={'from_date': timestamp}
        )
        if homework.status_code != HTTPStatus.OK:
            logging.error('Эндпоит недоступен')
            raise RuntimeError
        else:
            return homework.json()
    except requests.exceptions.RequestException as error:
        logging.error('Эндпоит недоступен')
        raise RuntimeError(error)


def check_response(response):
    """Проверка ответа API."""
    if not isinstance(response, dict):
        raise TypeError('Ответ не соответствет типу данных')
    elif 'current_date' not in response or 'homeworks' not in response:
        logging.error('отсутствие ожидаемых ключей в ответе API')
        raise KeyError('отсутствие ожидаемых ключей в ответе API')
    hw_list = response.get('homeworks')
    if not isinstance(hw_list, list):
        raise TypeError('Список домашних работ не является спиком')
    elif not hw_list:
        logging.debug('Спико домашних работ пуст')
    return hw_list


def parse_status(homework: dict):
    """Инромация о конкретной домашней работе."""
    homework_name = homework.get('homework_name')
    status = homework.get('status')
    if not homework_name:
        logging.error('Отсутствуют необходимые ключи в переданном словаре')
        raise KeyError
    elif status not in HOMEWORK_VERDICTS:
        logging.error('неожиданный статус домашней работы')
        raise KeyError
    verdict = HOMEWORK_VERDICTS.get(status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    # Создаем объект класса бота
    bot = TeleBot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    if not check_tokens():
        sys.exit(1)

    while True:
        try:
            hw = get_api_answer(timestamp)
            hw_list = check_response(hw)
            if hw_list:
                message = parse_status(hw_list[0])
                send_message(bot, message)
            else:
                logging.debug('отсутствие в ответе новых статусов')
            timestamp = int(hw.get('current_date') - RETRY_PERIOD)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            send_message(bot, message)
        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
