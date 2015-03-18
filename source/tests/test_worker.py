__author__ = 'leshiy1295'

import unittest
import mock
from lib.worker import get_redirect_history_from_task, worker
from tarantool.error import DatabaseError

class WorkerTestCase(unittest.TestCase):

    def test_get_redirect(self):
        to_unicode_mock = mock.Mock(return_value=u'url')
        task_mock = mock.Mock()
        task_mock.data = {'url': 'url', 'url_id': 7}
        with mock.patch('lib.worker.to_unicode', to_unicode_mock, create=True):
            with mock.patch('lib.worker.logger', mock.Mock(), create=True):
                with mock.patch('lib.worker.get_redirect_history', mock.Mock(return_value=([], [], []))):
                    is_input, data = get_redirect_history_from_task(task_mock, 10)
                    self.assertEqual(False, is_input)

    def test_get_redirect_with_suspicious(self):
        to_unicode_mock = mock.Mock(return_value=u'url')
        task_mock = mock.Mock()
        task_mock.data = {'url': 'url', 'url_id': 7, 'suspicious': 'some text'}
        with mock.patch('lib.worker.to_unicode', to_unicode_mock, create=True):
            with mock.patch('lib.worker.logger', mock.Mock(), create=True):
                with mock.patch('lib.worker.get_redirect_history', mock.Mock(return_value=([], [], []))):
                    is_input, data = get_redirect_history_from_task(task_mock, 10)
                    self.assertEqual(False, is_input)

    def test_get_redirect_with_error(self):
        to_unicode_mock = mock.Mock(return_value=u'url')
        task_mock = mock.Mock()
        task_mock.data = {'url': 'url', 'url_id': 7}
        with mock.patch('lib.worker.to_unicode', to_unicode_mock, create=True):
            with mock.patch('lib.worker.logger', mock.Mock(), create=True):
                with mock.patch('lib.worker.get_redirect_history', mock.Mock(return_value=(['ERROR'], [], []))):
                    is_input, data = get_redirect_history_from_task(task_mock, 10)
                    self.assertEqual(True, is_input)

    def test_worker_with_bad_ppid(self):
        config_mock = mock.Mock()

        tube_mock = mock.Mock()
        tube_mock.opt = {'tube': 'tube'}

        task_mock = mock.Mock()
        task_mock.task_id = None
        task_mock.meta = mock.Mock(return_value={'pri': 'pri'})

        tube_mock.take = mock.Mock(side_effect=[task_mock, task_mock, task_mock, None])

        get_tube_mock = mock.Mock(return_value=tube_mock)

        with mock.patch('lib.worker.get_tube', get_tube_mock, create=True):
            with mock.patch('lib.worker.logger', mock.Mock(), create=True):
                with mock.patch('os.path.exists', mock.Mock(return_value=False), create=True):
                    worker(config_mock, None)
                    self.assertFalse(tube_mock.take.called)

    def test_worker_with_bad_task(self):
        config_mock = mock.Mock()

        tube_mock = mock.Mock()
        tube_mock.opt = {'tube': 'tube'}

        tube_mock.take = mock.Mock(return_value=False)

        get_tube_mock = mock.Mock(return_value=tube_mock)

        get_redirect_mock = mock.Mock(return_value=None)

        with mock.patch('lib.worker.get_tube', get_tube_mock, create=True):
            with mock.patch('lib.worker.logger', mock.Mock(), create=True):
                with mock.patch('os.path.exists', mock.Mock(side_effect=[True, False]), create=True):
                    with mock.patch('lib.worker.get_redirect_history_from_task', get_redirect_mock, create=True):
                        worker(config_mock, None)
                        self.assertFalse(get_redirect_mock.called)

    def test_worker_with_good_task_and_bad_result(self):
        config_mock = mock.Mock()

        tube_mock = mock.Mock()
        tube_mock.opt = {'tube': 'tube'}
        tube_mock.put = mock.Mock()

        task_mock = mock.Mock()
        task_mock.task_id = None
        task_mock.meta = mock.Mock(return_value={'pri': 'pri'})

        tube_mock.take = mock.Mock(return_value=task_mock)

        get_tube_mock = mock.Mock(return_value=tube_mock)

        get_redirect_mock = mock.Mock(return_value=None)

        with mock.patch('lib.worker.get_tube', get_tube_mock, create=True):
            with mock.patch('lib.worker.logger', mock.Mock(), create=True):
                with mock.patch('os.path.exists', mock.Mock(side_effect=[True, False]), create=True):
                    with mock.patch('lib.worker.get_redirect_history_from_task', get_redirect_mock, create=True):
                        worker(config_mock, None)
                        self.assertFalse(tube_mock.put.called)

    def test_worker_with_good_task_and_good_result_and_true_is_input(self):
        config_mock = mock.Mock()

        tube_mock = mock.Mock()
        tube_mock.opt = {'tube': 'tube'}
        tube_mock.put = mock.Mock()

        task_mock = mock.Mock()
        task_mock.task_id = None
        task_mock.meta = mock.Mock(return_value={'pri': 'pri'})
        task_mock.ack = mock.Mock()

        tube_mock.take = mock.Mock(return_value=task_mock)

        get_tube_mock = mock.Mock(return_value=tube_mock)

        get_redirect_mock = mock.Mock(return_value=(True, None))

        with mock.patch('lib.worker.get_tube', get_tube_mock, create=True):
            with mock.patch('lib.worker.logger', mock.Mock(), create=True):
                with mock.patch('os.path.exists', mock.Mock(side_effect=[True, False]), create=True):
                    with mock.patch('lib.worker.get_redirect_history_from_task', get_redirect_mock, create=True):
                        worker(config_mock, None)
                        task_mock.meta.assert_called_once_with()


    def test_worker_with_good_task_and_good_result_and_false_is_input(self):
        config_mock = mock.Mock()

        tube_mock = mock.Mock()
        tube_mock.opt = {'tube': 'tube'}
        tube_mock.put = mock.Mock()

        task_mock = mock.Mock()
        task_mock.task_id = None
        task_mock.ack = mock.Mock()

        tube_mock.take = mock.Mock(return_value=task_mock)

        get_tube_mock = mock.Mock(return_value=tube_mock)

        get_redirect_mock = mock.Mock(return_value=(False, None))

        with mock.patch('lib.worker.get_tube', get_tube_mock, create=True):
            with mock.patch('lib.worker.logger', mock.Mock(), create=True):
                with mock.patch('os.path.exists', mock.Mock(side_effect=[True, False]), create=True):
                    with mock.patch('lib.worker.get_redirect_history_from_task', get_redirect_mock, create=True):
                        worker(config_mock, None)
                        tube_mock.put.assert_called_once_with(None)


    def test_worker_with_exception(self):
        config_mock = mock.Mock()

        logger_mock = mock.Mock()

        tube_mock = mock.Mock()
        tube_mock.opt = {'tube': 'tube'}

        task_mock = mock.Mock()
        task_mock.task_id = None
        task_mock.ack = mock.Mock(side_effect=DatabaseError)

        tube_mock.take = mock.Mock(return_value=task_mock)

        get_tube_mock = mock.Mock(return_value=tube_mock)

        get_redirect_mock = mock.Mock(return_value=(False, None))

        with mock.patch('lib.worker.get_tube', get_tube_mock, create=True):
            with mock.patch('lib.worker.logger', logger_mock, create=True):
                with mock.patch('os.path.exists', mock.Mock(side_effect=[True, False]), create=True):
                    with mock.patch('lib.worker.get_redirect_history_from_task', get_redirect_mock, create=True):
                        worker(config_mock, None)
                        logger_mock.exception.assert_called_once()
