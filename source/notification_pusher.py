#!/usr/bin/env python2.7
# coding: utf-8

import argparse
import json
import logging
import os
import signal
import sys
from logging.config import dictConfig
from threading import current_thread

import gevent
from gevent import Greenlet
from gevent import queue as gevent_queue
from gevent import sleep
from gevent.monkey import patch_all
from gevent.pool import Pool
import requests
import tarantool
import tarantool_queue

SIGNAL_EXIT_CODE_OFFSET = 128
"""Коды выхода рассчитываются как 128 + номер сигнала"""

run_application = True
"""Флаг, определяющий, должно ли приложение продолжать работу."""

exit_code = 0
"""Код возврата приложения"""

logger = logging.getLogger('pusher')


def notification_worker(task, task_queue, *args, **kwargs):
    """
    Обработчик задачи отправки уведомления.

    :param task: задача
    :type task: tarantool_queue.Task
    :param task_queue: очередь для обработанных задач
    :type task_queue: gevent.queue.Queue
    :param args:
    :param kwargs:
    """
    try:
        current_thread().name = "pusher.worker#{task_id}".format(task_id=task.task_id)

        data = task.data.copy()

        url = data.pop('callback_url')
        data['id'] = task.task_id

        logger.info('Send data to callback url [{url}].'.format(url=url))

        response = requests.post(
            url, data=json.dumps(data), *args, **kwargs
        )

        logger.info('Callback url [{url}] response status code={status_code}.'.format(
            url=url, status_code=response.status_code
        ))

        task_queue.put((task, 'ack'))
    except requests.RequestException as exc:
        logger.exception(exc)
        task_queue.put((task, 'bury'))


def done_with_processed_tasks(task_queue):
    """
    Удаляет завешенные задачи.

    :param task_queue: очередь, хранящая кортежи (объект задачи, имя действия)
    """
    logger.debug('Send info about finished tasks to queue.')

    for _ in xrange(task_queue.qsize()):
        try:
            task, action_name = task_queue.get_nowait()

            logger.debug('{name} task#{task_id}.'.format(
                name=action_name.capitalize(),
                task_id=task.task_id
            ))

            try:
                getattr(task, action_name)()
            except tarantool.DatabaseError as exc:
                logger.exception(exc)
        except gevent_queue.Empty:
            break


def stop_handler(signum):
    """
    Обработчик сигналов завершения приложения.

    :param signum: номер сигнала
    :type signum: int
    """
    global run_application
    global exit_code

    current_thread().name = 'pusher.signal'

    logger.info('Got signal #{signum}.'.format(signum=signum))

    run_application = False
    exit_code = SIGNAL_EXIT_CODE_OFFSET + signum


def main_loop(config):
    """
    Основной цикл приложения.

    :param config: конфигурация
    :type config: Config

    Алгоритм:
     * Открываем соединение с tarantool.queue, использую config.QUEUE_* настройки.
     * Создаем пул обработчиков.
     * Создаем очередь куда обработчики будут помещать выполненные задачи.
     * Пока количество обработчиков <= config.WORKER_POOL_SIZE, берем задачу из tarantool.queue
       и запускаем greenlet для ее обработки.
     * Посылаем уведомления о том, что задачи завершены в tarantool.queue.
     * Спим config.SLEEP секунд.
    """
    logger.info('Connect to queue server on {host}:{port} space #{space}.'.format(
        host=config.QUEUE_HOST, port=config.QUEUE_PORT, space=config.QUEUE_SPACE
    ))
    queue = tarantool_queue.Queue(
        host=config.QUEUE_HOST, port=config.QUEUE_PORT, space=config.QUEUE_SPACE
    )

    logger.info('Use tube [{tube}], take timeout={take_timeout}.'.format(
        tube=config.QUEUE_TUBE,
        take_timeout=config.QUEUE_TAKE_TIMEOUT
    ))

    tube = queue.tube(config.QUEUE_TUBE)

    logger.info('Create worker pool[{size}].'.format(size=config.WORKER_POOL_SIZE))
    worker_pool = Pool(config.WORKER_POOL_SIZE)

    processed_task_queue = gevent_queue.Queue()

    logger.info('Run main loop. Worker pool size={count}. Sleep time is {sleep}.'.format(
        count=config.WORKER_POOL_SIZE, sleep=config.SLEEP
    ))

    while run_application:
        free_workers_count = worker_pool.free_count()

        logger.debug('Pool has {count} free workers.'.format(count=free_workers_count))

        for number in xrange(free_workers_count):
            logger.debug('Get task from tube for worker#{number}.'.format(number=number))

            task = tube.take(config.QUEUE_TAKE_TIMEOUT)

            if task:
                logger.info('Start worker#{number} for task id={task_id}.'.format(
                    task_id=task.task_id, number=number
                ))

                worker = Greenlet(
                    notification_worker,
                    task,
                    processed_task_queue,
                    timeout=config.HTTP_CONNECTION_TIMEOUT,
                    verify=False
                )
                worker_pool.add(worker)
                worker.start()

        done_with_processed_tasks(processed_task_queue)

        sleep(config.SLEEP)
    else:
        logger.info('Stop application loop.')


def parse_cmd_args(args):
    """
    Разбирает аргументы командной строки.

    :param args: список аргументов
    :type args: list

    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(
        description='Push notifications daemon.'
    )
    parser.add_argument(
        '-c',
        '--config',
        dest='config',
        required=True,
        help='Path to configuration file.'
    )
    parser.add_argument(
        '-d',
        '--daemon',
        dest='daemon',
        action='store_true',
        help='Daemonize process.'
    )
    parser.add_argument(
        '-P',
        '--pid',
        dest='pidfile',
        help='Path to pidfile.'
    )

    return parser.parse_args(args=args)


def daemonize():
    """
    Демонизирует текущий процесс.
    """
    try:
        pid = os.fork()
    except OSError as exc:
        raise Exception("%s [%d]" % (exc.strerror, exc.errno))

    if pid == 0:
        os.setsid()

        try:
            pid = os.fork()
        except OSError as exc:
            raise Exception("%s [%d]" % (exc.strerror, exc.errno))

        if pid > 0:
            os._exit(0)
    else:
        os._exit(0)


class Config(object):
    """
    Класс для хранения настроек приложения.
    """
    pass


def load_config_from_pyfile(filepath):
    """
    Создает Config объект из py файла и загружает в него настройки.

    Используются только camel-case переменные.

    :param filepath: путь до py файла с настройками
    :type filepath: basestring

    :rtype: Config
    """
    cfg = Config()

    variables = {}

    execfile(filepath, variables)

    for key, value in variables.iteritems():
        if key.isupper():
            setattr(cfg, key, value)

    return cfg


def install_signal_handlers():
    """
    Устанавливает обработчики системных сигналов.
    """
    logger.info('Install signal handlers.')

    for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT):
        gevent.signal(signum, stop_handler, signum)


def create_pidfile(pidfile_path):
    pid = str(os.getpid())
    with open(pidfile_path, 'w') as f:
        f.write(pid)


def main(argv):
    """
    Точка входа в приложение.

    В случае возникновения ошибки в приложении, оно засыпает на config.SLEEP_ON_FAIL секунд.

    :param argv: агрументы командной строки.
    :type argv: list
    """
    args = parse_cmd_args(argv[1:])

    if args.daemon:
        daemonize()

    if args.pidfile:
        create_pidfile(args.pidfile)

    config = load_config_from_pyfile(
        os.path.realpath(os.path.expanduser(args.config))
    )

    patch_all()

    dictConfig(config.LOGGING)

    current_thread().name = 'pusher.main'

    install_signal_handlers()

    while run_application:
        try:
            main_loop(config)
        except Exception as exc:
            logger.error(
                'Error in main loop. Go to sleep on {} second(s).'.format(config.SLEEP_ON_FAIL)
            )
            logger.exception(exc)

            sleep(config.SLEEP_ON_FAIL)
    else:
        logger.info('Stop application loop in main.')

    return exit_code


if __name__ == '__main__':
    sys.exit(main(sys.argv))
