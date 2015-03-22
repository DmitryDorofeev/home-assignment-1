__author__ = 'leshiy1295'

import unittest
import mock
from lib.worker import get_redirect_history_from_task, worker
from tarantool.error import DatabaseError

class WorkerTestCase(unittest.TestCase):

    def test_get_redirect_with_no_recheck_and_no_error(self):
        task_mock = mock.Mock()
        task_mock.data = {'url': 'url', 'url_id': 7, 'recheck': False}
        with mock.patch('lib.worker.to_unicode', mock.Mock(return_value=u'url'), create=True):
            with mock.patch('lib.worker.logger', mock.Mock(), create=True):
                with mock.patch('lib.worker.get_redirect_history', mock.Mock(return_value=(['meta_tag', 'http_status'],
                                                                                           [u'another_url', u'url'],
                                                                                           ['GOOGLE_ANALYTICS']))):
                    is_input, data = get_redirect_history_from_task(task_mock, 10)
                    self.assertFalse(is_input)
                    self.assertEqual({'url_id': 7,
                                      'result': [['meta_tag', 'http_status'],
                                                 [u'another_url', u'url'],
                                                 ['GOOGLE_ANALYTICS']],
                                      'check_type': 'normal'}, data)

    def test_get_redirect_with_all_parameters(self):
        task_mock = mock.Mock()
        task_mock.data = {'url': 'another_url', 'url_id': 6, 'recheck': True}
        user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36"
        with mock.patch('lib.worker.to_unicode', mock.Mock(return_value=u'another_url'), create=True):
            with mock.patch('lib.worker.logger', mock.Mock(), create=True):
                with mock.patch('lib.worker.get_redirect_history', mock.Mock(return_value=(['meta_tag'],
                                                                                           [u'another_url'],
                                                                                           []))):
                    is_input, data = get_redirect_history_from_task(task_mock, 10, 30, user_agent)
                    self.assertFalse(is_input)
                    self.assertEqual({'url_id': 6,
                                      'result': [['meta_tag'],
                                                 [u'another_url'],
                                                 []],
                                      'check_type': 'normal'}, data)

    def test_get_redirect_with_suspicious_and_without_recheck(self):
        task_mock = mock.Mock()
        task_mock.data = {'url': 'url', 'url_id': 7, 'suspicious': 'some text'}
        with mock.patch('lib.worker.to_unicode', mock.Mock(return_value=u'url'), create=True):
            with mock.patch('lib.worker.logger', mock.Mock(), create=True):
                with mock.patch('lib.worker.get_redirect_history', mock.Mock(return_value=(['meta_tag', 'http_status'],
                                                                                           [u'another_url', u'url'],
                                                                                           ['GOOGLE_ANALYTICS']))):
                    is_input, data = get_redirect_history_from_task(task_mock, 10)
                    self.assertFalse(is_input)
                    self.assertEqual({'url_id': 7,
                                      'result': [['meta_tag', 'http_status'],
                                                 [u'another_url', u'url'],
                                                 ['GOOGLE_ANALYTICS']],
                                      'check_type': 'normal',
                                      'suspicious': 'some text'}, data)

    def test_get_redirect_with_empty_url(self):
        task_mock = mock.Mock()
        task_mock.data = {'url': '', 'url_id': 0}
        with mock.patch('lib.worker.to_unicode', mock.Mock(return_value=u''), create=True):
            with mock.patch('lib.worker.logger', mock.Mock(), create=True):
                with mock.patch('lib.worker.get_redirect_history', mock.Mock(return_value=([],
                                                                                           [u''],
                                                                                           []))):
                    is_input, data = get_redirect_history_from_task(task_mock, 10)
                    self.assertFalse(is_input)
                    self.assertEqual({'url_id': 0,
                                      'result': [[],
                                                 [u''],
                                                 []],
                                      'check_type': 'normal'}, data)

    def test_get_redirect_without_url(self):
        task_mock = mock.Mock()
        task_mock.data = {'url': None, 'url_id': None}
        with mock.patch('lib.worker.to_unicode', mock.Mock(return_value=u''), create=True):
            with mock.patch('lib.worker.logger', mock.Mock(), create=True):
                with mock.patch('lib.worker.get_redirect_history', mock.Mock(return_value=([],
                                                                                           [None],
                                                                                           []))):
                    is_input, data = get_redirect_history_from_task(task_mock, 10)
                    self.assertFalse(is_input)
                    self.assertEqual({'url_id': None,
                                      'result': [[],
                                                 [None],
                                                 []],
                                      'check_type': 'normal'}, data)

    def test_get_redirect_with_error_and_no_recheck(self):
        task_mock = mock.Mock()
        task_mock.data = {'url': 'error_url', 'url_id': 5}
        with mock.patch('lib.worker.to_unicode', mock.Mock(return_value=u'url'), create=True):
            with mock.patch('lib.worker.logger', mock.Mock(), create=True):
                with mock.patch('lib.worker.get_redirect_history', mock.Mock(return_value=(['ERROR'],
                                                                                           [u'error_url'],
                                                                                           []))):
                    is_input, data = get_redirect_history_from_task(task_mock, 10)
                    self.assertTrue(task_mock.data['recheck'])
                    self.assertTrue(is_input)
                    self.assertEqual(task_mock.data, data)

    def test_worker_with_bad_ppid(self):
        config_mock = mock.Mock()

        tube_mock = mock.Mock()
        tube_mock.opt = {'tube': 'tube'}

        task_mock = mock.Mock()
        task_mock.meta = mock.Mock(return_value={'pri': 'pri'})

        get_tube_mock = mock.Mock(return_value=tube_mock)

        mocked_method = mock.Mock()
        with mock.patch('lib.worker.get_tube', get_tube_mock, create=True):
            with mock.patch('lib.worker.logger', mock.Mock(), create=True):
                with mock.patch('os.path.exists', mock.Mock(return_value=False), create=True):
                    with mock.patch('lib.worker.my_mocked_method_for_test', mocked_method, create=True):
                        worker(config_mock, None)
                        mocked_method.assert_called_once_with('return')

    def test_worker_with_no_task(self):
        config_mock = mock.Mock()

        tube_mock = mock.Mock()
        tube_mock.opt = {'tube': 'tube'}

        tube_mock.take = mock.Mock(return_value=False)

        get_tube_mock = mock.Mock(return_value=tube_mock)

        mocked_method = mock.Mock()
        with mock.patch('lib.worker.get_tube', get_tube_mock, create=True):
            with mock.patch('lib.worker.logger', mock.Mock(), create=True):
                with mock.patch('os.path.exists', mock.Mock(side_effect=[True, False]), create=True):
                    with mock.patch('lib.worker.my_mocked_method_for_test', mocked_method, create=True):
                        worker(config_mock, None)
                        self.assertEqual(mocked_method.call_count, 2)
                        mocked_method.assert_any_call('no_task')
                        mocked_method.assert_any_call('return')

    def test_worker_with_true_is_input(self):
        config_mock = mock.Mock()
        config_mock.RECHECK_DELAY = 300

        tube_mock = mock.Mock()
        tube_mock.opt = {'tube': 'tube'}
        tube_mock.put = mock.Mock()

        task_mock = mock.Mock()
        task_mock.data = {'url': 'error_url', 'url_id': 5}
        task_mock.meta = mock.Mock(return_value={'pri': 'pri'})
        task_mock.ack = mock.Mock()

        tube_mock.take = mock.Mock(return_value=task_mock)

        get_tube_mock = mock.Mock(return_value=tube_mock)

        get_redirect_mock = mock.Mock(return_value=(True, task_mock.data))

        mocked_method = mock.Mock()
        with mock.patch('lib.worker.get_tube', get_tube_mock, create=True):
            with mock.patch('lib.worker.logger', mock.Mock(), create=True):
                with mock.patch('os.path.exists', mock.Mock(side_effect=[True, False]), create=True):
                    with mock.patch('lib.worker.get_redirect_history_from_task', get_redirect_mock, create=True):
                        with mock.patch('lib.worker.my_mocked_method_for_test', mocked_method, create=True):
                            worker(config_mock, None)
                            tube_mock.put.assert_called_once_with(task_mock.data, delay=config_mock.RECHECK_DELAY, pri='pri')
                            self.assertEqual(mocked_method.call_count, 2)
                            mocked_method.assert_any_call('task_done')
                            mocked_method.assert_any_call('return')

    def test_worker_with_false_is_input(self):
        config_mock = mock.Mock()

        tube_mock = mock.Mock()
        tube_mock.opt = {'tube': 'tube'}
        tube_mock.put = mock.Mock()

        task_mock = mock.Mock()
        task_mock.data = {'url': 'url', 'url_id': 7, 'recheck': False}
        task_mock.ack = mock.Mock()

        tube_mock.take = mock.Mock(return_value=task_mock)

        get_tube_mock = mock.Mock(return_value=tube_mock)

        data = {'url_id': 7,
                'result': [['meta_tag', 'http_status'],
                           [u'another_url', u'url'],
                           ['GOOGLE_ANALYTICS']],
                'check_type': 'normal'}
        get_redirect_mock = mock.Mock(return_value=(False, data))
        mocked_method = mock.Mock()
        with mock.patch('lib.worker.get_tube', get_tube_mock, create=True):
            with mock.patch('lib.worker.logger', mock.Mock(), create=True):
                with mock.patch('os.path.exists', mock.Mock(side_effect=[True, False]), create=True):
                    with mock.patch('lib.worker.get_redirect_history_from_task', get_redirect_mock, create=True):
                        with mock.patch('lib.worker.my_mocked_method_for_test', mocked_method, create=True):
                            worker(config_mock, None)
                            tube_mock.put.assert_called_once_with(data)
                            self.assertEqual(mocked_method.call_count, 2)
                            mocked_method.assert_any_call('task_done')
                            mocked_method.assert_any_call('return')


    def test_worker_with_exception(self):
        config_mock = mock.Mock()

        logger_mock = mock.Mock()
        logger_mock.exception = mock.Mock()

        tube_mock = mock.Mock()
        tube_mock.opt = {'tube': 'tube'}

        task_mock = mock.Mock()
        task_mock.data = {'url': 'error_url', 'url_id': 5}
        task_mock.meta = mock.Mock(return_value={'pri': 'pri'})
        task_mock.ack = mock.Mock(side_effect=DatabaseError)

        tube_mock.take = mock.Mock(return_value=task_mock)

        get_tube_mock = mock.Mock(return_value=tube_mock)

        get_redirect_mock = mock.Mock(return_value=(True, task_mock.data))

        mocked_method = mock.Mock()
        with mock.patch('lib.worker.get_tube', get_tube_mock, create=True):
            with mock.patch('lib.worker.logger', logger_mock, create=True):
                with mock.patch('os.path.exists', mock.Mock(side_effect=[True, False]), create=True):
                    with mock.patch('lib.worker.get_redirect_history_from_task', get_redirect_mock, create=True):
                        with mock.patch('lib.worker.my_mocked_method_for_test', mocked_method, create=True):
                            worker(config_mock, None)
                            self.assertEqual(mocked_method.call_count, 2)
                            mocked_method.assert_any_call('DatabaseError')
                            mocked_method.assert_any_call('return')
