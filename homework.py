import logging

import os
import sys

import requests
import time
import telegram
from dotenv import load_dotenv
from exceptions import (
    ErrorSendingMessage,
    ResponseStatusCodeNoneOk)
from http import HTTPStatus

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


formatter = (
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def get_stream_handler():
    """Настройка хендлера."""
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(logging.Formatter(formatter))
    return stream_handler


def get_logger(name):
    """Настройка логирования."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(get_stream_handler())
    return logger


logger = get_logger(__name__)


def send_message(bot, message_tg):
    """Отправляет сообщение в Telegram чат."""
    try:
        logger.info('Начали отправку сообщения')
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message_tg
        )
    except ErrorSendingMessage:
        message_error = 'Не удалось отправить сообщение'
        logger.error(message_error)
        raise ErrorSendingMessage(message_error)
    else:
        logger.info('Удачная отправка сообщения')


def get_api_answer(current_timestamp):
    """Делает запрос эндпоинту API-сервиса.
    Параметр - временная метка.
    В случае успешного запроса должна вернуть ответ API.
    Преобразовав из JSON в Python.
    """
    try:
        logger.info('Начали запрос к API')
        timestamp = current_timestamp or int(time.time())
        params = {'from_date': timestamp}
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != HTTPStatus.OK:
            raise ResponseStatusCodeNoneOk
        return response.json()
    except ResponseStatusCodeNoneOk:
        message_error = f'Код ответа {response.status_code}'
        raise ResponseStatusCodeNoneOk(message_error)


def check_response(response):
    """Проверяет ответ API на корректность."""
    if not isinstance(response, dict):
        raise TypeError(
            'Ответ от API. Тип не словарь.'
            f' response = {response}.')
    homeworks = response.get('homeworks')
    if 'homeworks' not in response or 'current_date' not in response:
        raise KeyError(
            'В ответе от API присутствуют ключ(и) '
            '"homeworks" и/или "current_date".'
            f' response = {response}.')
    if not isinstance(homeworks, list):
        raise TypeError(
            'В ответе от API под ключом "homeworks" пришел не список.'
            f' response = {response}.')
    return homeworks


def parse_status(homework):
    """Извлекает из информации о конкретной домашке статус работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if 'homework_name' not in homework:
        message_error = 'Нет ключа "homework_name" в homework'
        raise KeyError(message_error)
    if homework_status not in HOMEWORK_VERDICTS:
        message_error = 'Недокумнтированный "status" в ответе'
        raise ValueError(message_error)
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def main():
    """Основная логика работы бота."""
    current_timestamp = int(time.time())
    if not check_tokens():
        sys.exit('Проверьте переменные окружения')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    last_status = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if homework:
                message_tg = parse_status(homework[0])
                status = message_tg
                if status != last_status:
                    send_message(bot, message_tg)
                    logger.info('Удачная отправка сообщения со статусом')
                    last_status = status
                    current_timestamp = response['current_date']
                else:
                    logger.info('Статус домашней работы не поменяося')
        except ValueError as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            send_message(bot, message)
        else:
            logger.info('Бот работает исправно')
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
