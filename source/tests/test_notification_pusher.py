import signal
import unittest
import mock
import requests
import tarantool
from notification_pusher import notification_worker, done_with_processed_tasks, stop_handler, install_signal_handlers, \
    SIGNAL_EXIT_CODE_OFFSET, main_loop, main, run, main_loop_run, run_application, mocked_run_application

__author__ = 'leshiy1295'

class NotificationPusherTestCase(unittest.TestCase):
    def test_mocked_run_application(self):
        self.assertEqual(mocked_run_application(), run_application)

    def test_notification_worker(self):
        task_mock = mock.Mock()
        task_mock.task_id = 1
        task_mock.data = {'callback_url': 'url'}
        task_queue_mock = mock.Mock()
        task_queue_mock.put = mock.Mock()
        current_thread_mock = mock.Mock()
        response_mock = mock.Mock()
        response_mock.status_code = 200
        mocked_method = mock.Mock()
        with mock.patch('notification_pusher.current_thread', mock.Mock(return_value=current_thread_mock), create=True):
            with mock.patch('notification_pusher.logger', mock.Mock(), create=True):
                with mock.patch('notification_pusher.requests.post', mock.Mock(return_value=response_mock), create=True):
                    with mock.patch('notification_pusher.my_mocked_method_for_test', mocked_method, create=True):
                        notification_worker(task_mock, task_queue_mock)
                        self.assertEqual(current_thread_mock.name, "pusher.worker#1")
                        mocked_method.assert_called_once_with(200)
                        task_queue_mock.put.assert_called_once_with((task_mock, 'ack'))

    def test_notification_worker_with_exception(self):
        task_mock = mock.Mock()
        task_mock.task_id = 1
        task_mock.data = {'callback_url': 'url'}
        task_queue_mock = mock.Mock()
        task_queue_mock.put = mock.Mock()
        current_thread_mock = mock.Mock()
        with mock.patch('notification_pusher.current_thread', mock.Mock(return_value=current_thread_mock), create=True):
            with mock.patch('notification_pusher.logger', mock.Mock(), create=True):
                with mock.patch('notification_pusher.requests.post',
                                mock.Mock(side_effect=requests.RequestException), create=True):
                    notification_worker(task_mock, task_queue_mock)
                    self.assertEqual(current_thread_mock.name, "pusher.worker#1")
                    task_queue_mock.put.assert_called_once_with((task_mock, 'bury'))

    def test_done_with_processed_tasks(self):
        task_queue_mock = mock.Mock()
        task_mock = mock.Mock()
        task_mock.some_action = mock.Mock()
        task_queue_mock.qsize.return_value = 1
        task_queue_mock.get_nowait.return_value = (task_mock, 'some_action')
        mocked_method = mock.Mock()

        with mock.patch('notification_pusher.logger', mock.Mock(), create=True):
            with mock.patch('notification_pusher.my_mocked_function_for_test', mocked_method, create=True):
                done_with_processed_tasks(task_queue_mock)
                task_mock.some_action.assert_called_once_with()

    def test_done_with_processed_tasks_with_tarantool_exception(self):
        task_queue_mock = mock.Mock()
        task_mock = mock.Mock()
        task_mock.some_action = mock.Mock(side_effect=tarantool.DatabaseError)
        task_queue_mock.qsize.return_value = 1
        task_queue_mock.get_nowait.return_value = (task_mock, 'some_action')
        mocked_method = mock.Mock()

        with mock.patch('notification_pusher.logger', mock.Mock(), create=True):
            with mock.patch('notification_pusher.my_mocked_method_for_test', mocked_method, create=True):
                done_with_processed_tasks(task_queue_mock)
                mocked_method.assert_called_once_with('tarantool.DatabaseError')

    def test_stop_handler(self):
        current_thread_mock = mock.Mock()
        mocked_method = mock.Mock()
        signum = 10
        with mock.patch('notification_pusher.current_thread', mock.Mock(return_value=current_thread_mock), create=True):
            with mock.patch('notification_pusher.my_mocked_method_for_test', mocked_method, create=True):
                with mock.patch('notification_pusher.logger', mock.Mock(), create=True):
                    stop_handler(signum)
                    self.assertEqual(current_thread_mock.name, 'pusher.signal')
                    mocked_method.assert_called_once_with(SIGNAL_EXIT_CODE_OFFSET + signum, False)

    def test_main_loop_run_with_task(self):
        config_mock = mock.Mock()

        worker_pool_mock = mock.Mock()
        worker_pool_mock.add = mock.Mock()
        worker_pool_mock.free_count = mock.Mock(return_value=1)

        tube_mock = mock.Mock()

        task_mock = mock.Mock()

        tube_mock.take = mock.Mock(return_value=task_mock)

        processed_task_query_mock = mock.Mock()

        worker_mock = mock.Mock()
        worker_mock.start = mock.Mock()

        with mock.patch('notification_pusher.mocked_run_application', mock.Mock(side_effect=[True, False]), create=True):
            with mock.patch('notification_pusher.Greenlet', mock.Mock(return_value=worker_mock), create=True):
                with mock.patch('notification_pusher.done_with_processed_tasks', mock.Mock(), create=True):
                    with mock.patch('notification_pusher.sleep', mock.Mock(), create=True):
                        main_loop_run(config_mock, worker_pool_mock, tube_mock, processed_task_query_mock)
                        worker_mock.start.assert_called_once_with()

    def test_main_loop_run_with_bad_task(self):
        config_mock = mock.Mock()

        worker_pool_mock = mock.Mock()
        worker_pool_mock.add = mock.Mock()
        worker_pool_mock.free_count = mock.Mock(return_value=1)

        tube_mock = mock.Mock()

        tube_mock.take = mock.Mock(return_value=None)

        processed_task_query_mock = mock.Mock()

        mocked_method = mock.Mock()
        with mock.patch('notification_pusher.mocked_run_application', mock.Mock(side_effect=[True, False]), create=True):
            with mock.patch('notification_pusher.my_mocked_method_for_test', mocked_method, create=True):
                with mock.patch('notification_pusher.done_with_processed_tasks', mock.Mock(), create=True):
                    with mock.patch('notification_pusher.sleep', mock.Mock(), create=True):
                        main_loop_run(config_mock, worker_pool_mock, tube_mock, processed_task_query_mock)
                        mocked_method.assert_called_once_with('no_task')

    def test_main_loop(self):
        config_mock = mock.Mock()

        queue_mock = mock.Mock()
        tube_mock = mock.Mock()

        queue_mock.tube = mock.Mock(return_value=tube_mock)

        worker_pool_mock = mock.Mock()

        processed_task_query_mock = mock.Mock()
        gevent_queue_mock = mock.Mock(return_value=processed_task_query_mock)

        main_loop_run_mock = mock.Mock()
        with mock.patch('notification_pusher.logger', mock.Mock(), create=True):
            with mock.patch('notification_pusher.tarantool_queue.Queue', mock.Mock(return_value=queue_mock), create=True):
                with mock.patch('notification_pusher.Pool', mock.Mock(return_value=worker_pool_mock), create=True):
                    with mock.patch('notification_pusher.gevent_queue.Queue', gevent_queue_mock, create=True):
                        with mock.patch('notification_pusher.main_loop_run', main_loop_run_mock, create=True):
                            main_loop(config_mock)
                            main_loop_run_mock.assert_called_once_with(config_mock, worker_pool_mock,
                                                                       tube_mock, processed_task_query_mock)

    def test_install_signal_handlers(self):
        gevent_signal_mock = mock.Mock()
        stop_handler_mock = mock.Mock()
        with mock.patch('notification_pusher.gevent.signal', gevent_signal_mock, create=True):
            with mock.patch('notification_pusher.stop_handler', stop_handler_mock, create=True):
                install_signal_handlers()
                self.assertEqual(gevent_signal_mock.call_count, 4)
                for signum in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT):
                    gevent_signal_mock.assert_any_call(signum, stop_handler_mock, signum)

    def test_run(self):
        config_mock = mock.Mock()

        mocked_method = mock.Mock()
        with mock.patch('notification_pusher.mocked_run_application', mock.Mock(side_effect=[True, False]), create=True):
            with mock.patch('notification_pusher.main_loop', mock.Mock(), create=True):
                with mock.patch('notification_pusher.my_mocked_method_for_test', mocked_method, create=True):
                    with mock.patch('notification_pusher.logger', mock.Mock(), create=True):
                        run(config_mock)
                        mocked_method.assert_called_once_with('main_loop')

    def test_run_with_exception(self):
        config_mock = mock.Mock()
        config_mock.SLEEP_ON_FAIL = 10

        main_loop_mock = mock.Mock(side_effect=Exception)
        sleep_mock = mock.Mock()
        with mock.patch('notification_pusher.mocked_run_application', mock.Mock(side_effect=[True, False]), create=True):
            with mock.patch('notification_pusher.main_loop', main_loop_mock, create=True):
                with mock.patch('notification_pusher.logger', mock.Mock(), create=True):
                    with mock.patch('notification_pusher.sleep', sleep_mock, create=True):
                        run(config_mock)
                        sleep_mock.assert_called_once_with(config_mock.SLEEP_ON_FAIL)

    def test_main_with_exception(self):
        config_mock = mock.Mock()

        args_mock = mock.Mock()
        parse_mock = mock.Mock(return_value=args_mock)

        current_thread_mock = mock.Mock()

        with mock.patch('lib.utils.parse_cmd_args', parse_mock, create=True):
            with mock.patch('lib.utils.get_config_with_args', mock.Mock(return_value=config_mock), create=True):
                with mock.patch('notification_pusher.patch_all', mock.Mock(), create=True):
                    with mock.patch('notification_pusher.current_thread',
                                    mock.Mock(return_value=current_thread_mock), create=True):
                        with mock.patch('notification_pusher.install_signal_handlers', mock.Mock(), create=True):
                            with mock.patch('notification_pusher.run', mock.Mock(), create=True):
                                    self.assertEqual(main([]), 0)
                                    self.assertEqual(current_thread_mock.name, 'pusher.main')