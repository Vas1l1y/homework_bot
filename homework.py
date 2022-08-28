import os

import requests
import time
import telegram
from dotenv import load_dotenv
import app_logger

logger = app_logger.get_logger(__name__)

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

messages_error = []


def send_message(bot, message_tg):
    """Отправляет сообщение в Telegram чат."""
    bot.send_message(
        chat_id=TELEGRAM_CHAT_ID,
        text=message_tg
    )


def get_api_answer(current_timestamp):
    """Делает запрос эндпоинту API-сервиса.
    Параметр - временная метка.
    В случае успешного запроса должна вернуть ответ API.
    Преобразовав из JSON в Python.
    """
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != 200:
        message_err = 'проверьте код ответа'
        logger.error(message_err)
        if message_err not in messages_error:
            messages_error.append(message_err)
        raise RuntimeError(message_err)
    else:
        response = response.json()
        # print(type(response))
        return response


def check_response(response):
    """Проверяет ответ API на корректность."""
    try:
        homeworks = response['homeworks']
        # pprint(homeworks)
        # print(type(homeworks))
        # homeworks = response.get('homeworks')
    except (isinstance(response, dict)):
        message_err = 'Ответ сервера не является словарем!'
        if message_err not in messages_error:
            messages_error.append(message_err)
        logger.error(message_err)
        raise TypeError(message_err)
    except Exception as error:
        message_err = f'Не получен список работ. Ошибка {error}'
        if message_err not in messages_error:
            messages_error.append(message_err)
        logger.error(message_err)
        raise Exception(message_err)
    if not (isinstance(homeworks, list)):
        message_err = 'Ответ сервера не является списком!'
        if message_err not in messages_error:
            messages_error.append(message_err)
        logger.error(message_err)
        raise TypeError(message_err)
    return homeworks


def parse_status(homework):
    """Извлекает из информации о конкретной домашке статус работы."""
    # pprint(homework)
    # print(type(homework))
    # verdict = ''
    # homework_name = ''
    if len(homework) != 0:
        try:
            homework_name = homework.get('homework_name')
        except ValueError:
            message_err = 'Нет ключа homework_name в ответе от API'
            logger.error(message_err)
            if message_err not in messages_error:
                messages_error.append(message_err)
            raise ValueError(message_err)
        try:
            homework_status = homework.get('status')
            print()
        except ValueError:
            message_err = 'Недокументированный статус домашки в ответе от API'
            logger.error(message_err)
            raise ValueError(message_err)
        verdict = HOMEWORK_STATUSES[homework_status]
        message_tg = (f'Изменился статус проверки работы '
                      f'"{homework_name}". {verdict}')
        return message_tg
    else:
        list_empty = ('С возвращением, Сер! '
                      'Все системы запущены и работают в штатном режиме. '
                      'Пока список пуст, ожидаем проверки. '
                      'Как изменится статус, я сообщу. '
                      'Хорошего дня!'
                      )
        return list_empty


def check_tokens():
    """Проверяет доступность переменных окружения."""
    if PRACTICUM_TOKEN:
        if TELEGRAM_TOKEN:
            if TELEGRAM_CHAT_ID:
                return True
            else:
                logger.critical('Проверьте переменные окружения')
                raise ValueError('Проверьте переменные окружения')


def main():
    """Основная логика работы бота."""
    current_timestamp = int(time.time())
    # current_timestamp = 1659965401
    # current_timestamp = 0
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    check_tokens()
    # run_time_10 = 5
    statuses = []

    while True:
        if check_tokens():
            try:
                response = get_api_answer(current_timestamp)
                homework = check_response(response)
                message_tg = parse_status(homework)
                status = message_tg
                statuses.append(status)
                if len(statuses) > 2:
                    del statuses[0]
                if statuses[0] != statuses[-1]:
                    try:
                        send_message(bot, message_tg)
                        logger.info('Удачная отправка сообщения со статусом')
                    except RuntimeError:
                        message_err = 'Сбой при отправке сообщения со статусом'
                        if message_err not in messages_error:
                            messages_error.append(message_err)
                        logger.error(message_err)
                        RuntimeError(message_err)
                        # send_message(bot, error)
                current_timestamp = response['current_date']
                # time.sleep(run_time_10)
                time.sleep(RETRY_TIME)

            except ValueError as error:
                ValueError('ошибка')
                message = f'Сбой в работе программы: {error}'
                if message not in messages_error:
                    messages_error.append(message)
                Exception(message)
                send_message(bot, message)
                # time.sleep(run_time_10)
                time.sleep(RETRY_TIME)
            # else:
            #     # time.sleep(run_time_10)
            #     time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
