# coding: utf-8
from logging import getLogger
import os.path

from tarantool.error import DatabaseError
from . import to_unicode, get_redirect_history

from utils import get_tube

logger = getLogger('redirect_checker')


def get_redirect_history_from_task(task, timeout, max_redirects=30, user_agent=None):
    url = to_unicode(task.data['url'], 'ignore')
    is_recheck = bool(task.data.get('recheck'))

    logger.info(u'Task id={} url={} url_id={} is_recheck={}'.format(
        task.task_id, url, task.data["url_id"], is_recheck
    ))

    history_types, history_urls, counters = get_redirect_history(
        url, timeout, max_redirects, user_agent
    )
    if 'ERROR' in history_types and not is_recheck:
        task.data['recheck'] = True
        data = task.data
        is_input = True
    else:
        data = {
            "url_id": task.data["url_id"],
            "result": [history_types, history_urls, counters],
            "check_type": "normal"
        }
        if 'suspicious' in task.data:
            data['suspicious'] = task.data['suspicious']

        is_input = False
    return is_input, data


def worker(config, parent_pid):
    input_tube = get_tube(
        host=config.INPUT_QUEUE_HOST,
        port=config.INPUT_QUEUE_PORT,
        space=config.INPUT_QUEUE_SPACE,
        name=config.INPUT_QUEUE_TUBE
    )
    logger.info(u'Connected to input queue server on {host}:{port} space #{space}. name={name}'.format(
        host=input_tube.queue.host,
        port=input_tube.queue.port,
        space=input_tube.queue.space,
        name=input_tube.opt['tube']
    ))

    output_tube = get_tube(
        host=config.OUTPUT_QUEUE_HOST,
        port=config.OUTPUT_QUEUE_PORT,
        space=config.OUTPUT_QUEUE_SPACE,
        name=config.OUTPUT_QUEUE_TUBE
    )
    logger.info(u'Connected to output queue server on {host}:{port} space #{space} name={name}.'.format(
        host=output_tube.queue.host,
        port=output_tube.queue.port,
        space=output_tube.queue.space,
        name=output_tube.opt['tube']
    ))

    parent_proc = '/proc/{}'.format(parent_pid)

    # run while parent is alive
    while os.path.exists(parent_proc):
        task = input_tube.take(config.QUEUE_TAKE_TIMEOUT)
        if task:
            logger.info(u'Starting task id={}.'.format(task.task_id))
            result = get_redirect_history_from_task(
                task,
                config.HTTP_TIMEOUT,
                config.MAX_REDIRECTS,
                config.USER_AGENT
            )
            if result:
                is_input, data = result
                if is_input:
                    input_tube.put(
                        data,
                        delay=config.RECHECK_DELAY,
                        pri=task.meta()['pri']
                    )
                else:
                    output_tube.put(data)
                logger.debug(u'Task id={} data:{}'.format(task.task_id, data))
            try:
                task.ack()
                logger.info(u'Task id={} done'.format(task.task_id))
            except DatabaseError as e:
                logger.info('Task ack fail')
                logger.exception(e)
    else:
        logger.info('Parent is dead. exiting')
