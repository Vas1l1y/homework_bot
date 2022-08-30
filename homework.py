import logging

import os

import requests
import time
import telegram
from dotenv import load_dotenv
from exceptions import (
    ErrorSendingMessage,
    ResponseStatusCodeNoneOk,
    TelegramTokenError)
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
        else:
            response = response.json()
            return response
    except ResponseStatusCodeNoneOk:
        message_error = f'Код ответа {response.status_code}'
        logger.error(message_error)
        raise ResponseStatusCodeNoneOk(message_error)


def check_response(response):
    """Проверяет ответ API на корректность."""
    if type(response) != dict:
        raise TypeError('Тип response не словарь')
    else:
        homeworks = response.get('homeworks')
        homeworks_homeworks = 'homeworks'
        homeworks_current_date = 'current_date'
        for h in homeworks:
            if homeworks_homeworks in h:
                message_error = 'В homeworks есть ключ homeworks'
                logger.error(message_error)
                raise ValueError(message_error)
        for c in homeworks:
            if homeworks_current_date in c:
                message_error = 'В homeworks есть ключ current_date'
                logger.error(message_error)
                raise ValueError(message_error)
        if type(homeworks) == list:
            return homeworks
        else:
            message_error = 'Тип homeworks не список'
            logger.error(message_error)
            raise TypeError(message_error)


def parse_status(homework):
    """Извлекает из информации о конкретной домашке статус работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if 'homework_name' not in homework:
        message_error = 'Нет ключа homework_name в homework'
        logger.error(message_error)
        raise KeyError(message_error)
    if homework_status not in HOMEWORK_VERDICTS:
        message_error = 'Недокумнтированный status в ответе'
        logger.error(message_error)
        raise ValueError(message_error)
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def main():
    """Основная логика работы бота."""
    current_timestamp = int(time.time())
    if check_tokens():
        bot = telegram.Bot(token=TELEGRAM_TOKEN)
    else:
        message_error = 'Неверный TELEGRAM_TOKEN'
        logger.error(message_error)
        TelegramTokenError(message_error)
    last_status = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if len(homework) != 0:
                message_tg = parse_status(homework[0])
                status = message_tg
                try:
                    if status != last_status:
                        send_message(bot, message_tg)
                        logger.info('Удачная отправка сообщения со статусом')
                        last_status = status
                        current_timestamp = response['current_date']
                    else:
                        pass
                except ErrorSendingMessage:
                    message_err = 'Сбой при отправке сообщения со статусом'
                    logger.error(message_err)
                    send_message(bot, message_err)
                    raise ErrorSendingMessage(message_err)
        except ValueError as error:
            ValueError('ошибка')
            message = f'Сбой в работе программы: {error}'
            if message not in messages_error:
                messages_error.append(message)
            Exception(message)
            send_message(bot, message)
        else:
            logger.info('10 минут, полет нормальный')
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
