# try:
        #     homework_name = homework.get('homework_name')
        # except ValueError:
        #     logger.error('Нет ключа homework_name в ответе от API')
        #     raise ValueError('Нет ключа homework_name в ответе от API')
        # try:
        #     homework_status = homework.get('status')
        #     print()
        # except ValueError:
        #     logger.error('Недокументированный статус '
        #                  'домашней работы в ответе от API')
        #     raise ('Недокументированный статус '
        #            'домашней работы в ответе от API')
        verdict = HOMEWORK_STATUSES[homework_status]
        message_tg = f'Изменился статус проверки работы "{homework_name}". {verdict}'



if len(homework) != 0:
        if homework['homework_name'] in homework:
                homework_name = homework.get('homework_name')
                return homework_name
        else:
            logger.error('Нет ключа homework_name в ответе от API')
            # raise ValueError('Нет ключа homework_name в ответе от API')
        if homework['status'] in homework:
            homework_status = homework.get('status')
            return homework_status
        else:
            logger.error('Нет ключа status в ответе от API')
        #     raise ValueError('Нет ключа status в ответе от API')









def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе
    статус этой работы"""
    # pprint(homework)
    # print(type(homework))
    verdict = ''
    homework_name = ''
    if len(homework) != 0:
        try:
            if homework[0]['homework_name'] in homework:
                homework_name = homework.get('homework_name')
                return homework_name
            if homework[0]['status'] in homework:
                homework_status = homework.get('status')
                if homework_status in HOMEWORK_STATUSES[homework_status]:
                    verdict = HOMEWORK_STATUSES[homework_status]
                    return verdict
                else:
                    message_err = 'Неизвестный статус домашней работы в ответе'
                    logger.error(message_err)
                    if message_err not in messages_error:
                        messages_error.append(message_err)
                    raise ValueError(message_err)
            message_tg = f'Изменился статус проверки работы ' \
                         f'{homework_name}. {verdict}'
            return message_tg
        except ValueError:
            message_err = 'Нет необходимых ключей в ответе от API'
            if message_err not in messages_error:
                messages_error.append(message_err)
            logger.error(message_err)
            raise ValueError(message_err)
    else:
        list_empty = (f'С возвращением, Сер! '
                      f'Все системы запущены и работают в штатном режиме. '
                      f'Пока список пуст, ожидаем проверки. '
                      f'Как изменится статус, я сообщу. '
                      f'Хорошего дня!'
                      )
        return list_empty
