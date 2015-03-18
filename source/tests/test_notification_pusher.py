__author__ = 'leshiy1295'

import unittest
from gevent import queue as gevent_queue
import mock
import requests
import tarantool
from notification_pusher import notification_worker, done_with_processed_tasks, stop_handler, install_signal_handlers, SIGNAL_EXIT_CODE_OFFSET, main_loop, main

class NotificationPusherTestCase(unittest.TestCase):
    def test_notification_worker(self):
        task_mock = mock.Mock()
        task_mock.data.copy.return_value = {'id': 1, 'callback_url': 2}
        queue_mock = mock.Mock()
        with mock.patch('notification_pusher.current_thread', mock.Mock(), create=True):
            with mock.patch('notification_pusher.logger', mock.Mock(), create=True):
                with mock.patch('notification_pusher.json', mock.Mock(), create=True):
                    with mock.patch('notification_pusher.requests', mock.Mock(), create=True):
                        notification_worker(task_mock, queue_mock)
                        self.assertEqual(queue_mock.put.call_count, 1)

    def test_done_with_processed_tasks(self):
        size = 7
        queue_mock = mock.Mock()
        task_mock = mock.Mock()
        queue_mock.qsize.return_value = size
        queue_mock.get_nowait.return_value = (task_mock, 'some action')
        getattr_mock = mock.Mock()
        logger_mock = mock.Mock()
        with mock.patch('notification_pusher.logger', logger_mock, create=True):
            with mock.patch('notification_pusher.getattr', getattr_mock, create=True):
                done_with_processed_tasks(queue_mock)
                self.assertEqual(getattr_mock.call_count, size)
                self.assertFalse(logger_mock.exception.called)

    def test_install_signal_handlers(self):
        gevent_mock = mock.Mock()
        gevent_mock.signal.return_value = None
        with mock.patch('notification_pusher.gevent.signal', gevent_mock, create=True):
            install_signal_handlers()
            self.assertEqual(4, gevent_mock.call_count)

    def test_notification_worker_with_exception(self):
        task_mock = mock.Mock()
        queue_mock = mock.Mock()
        logger_mock = mock.Mock()
        logger_mock.exception = mock.Mock()
        with mock.patch('notification_pusher.current_thread', mock.Mock(side_effect=requests.RequestException), create=True):
            with mock.patch('notification_pusher.logger', logger_mock, create=True):
                notification_worker(task_mock, queue_mock)
                self.assertEqual(logger_mock.exception.call_count, 1)

    def test_done_with_processed_tasks_with_tarantool_exception(self):
        size = 7
        queue_mock = mock.Mock()
        task_mock = mock.Mock()
        queue_mock.qsize.return_value = size
        queue_mock.get_nowait.return_value = (task_mock, 'some action')
        getattr_mock = mock.Mock(side_effect=tarantool.DatabaseError)
        logger_mock = mock.Mock()
        logger_mock.exception = mock.Mock()
        with mock.patch('notification_pusher.logger', logger_mock, create=True):
            with mock.patch('notification_pusher.getattr', getattr_mock, create=True):
                done_with_processed_tasks(queue_mock)
                self.assertEqual(logger_mock.exception.call_count, size)

    def test_done_with_processed_tasks_with_gevent_exception(self):
        size = 7
        queue_mock = mock.Mock()
        queue_mock.qsize.return_value = size
        queue_mock.get_nowait.side_effect = gevent_queue.Empty
        mocked_method_mock = mock.Mock()
        with mock.patch('notification_pusher.logger', mock.Mock(), create=True):
            with mock.patch('notification_pusher.my_mocked_method_for_test', mocked_method_mock, create=True):
                done_with_processed_tasks(queue_mock)
                self.assertEqual(mocked_method_mock.call_count, 1)

    def test_stop_handler(self):
        current_thread_mock = mock.Mock()
        mocked_method_mock = mock.Mock()
        signum = 10
        with mock.patch('notification_pusher.current_thread', current_thread_mock, create=True):
            with mock.patch('notification_pusher.my_mocked_method_for_test', mocked_method_mock, create=True):
                with mock.patch('notification_pusher.logger', mock.Mock(), create=True):
                    stop_handler(signum)
                    mocked_method_mock.assert_called_once_with(SIGNAL_EXIT_CODE_OFFSET + signum)

    def test_main_loop_with_task(self):
        config_mock = mock.Mock()
        logger_mock = mock.Mock()

        queue_mock = mock.Mock()
        tube_mock = mock.Mock()

        task_mock = mock.Mock()

        tube_mock.take = mock.Mock(return_value=task_mock)
        queue_mock.tube = mock.Mock(return_value=tube_mock)

        worker_pool_mock = mock.Mock()
        worker_pool_mock.add = mock.Mock()
        worker_pool_mock.free_count = mock.Mock(return_value=1)

        gevent_mock = mock.Mock()
        processed_task_query_mock = mock.Mock()
        gevent_mock.Queue = mock.Mock(return_value=processed_task_query_mock)

        worker_mock = mock.Mock()
        worker_mock.start = mock.Mock()

        with mock.patch('notification_pusher.logger', logger_mock, create=True):
            with mock.patch('notification_pusher.tarantool_queue', mock.Mock(return_value=queue_mock), create=True):
                with mock.patch('notification_pusher.Pool', mock.Mock(return_value=worker_pool_mock), create=True):
                    with mock.patch('notification_pusher.gevent_queue', gevent_mock, create=True):
                        with mock.patch('notification_pusher.run_application', mock.Mock(side_effect=[True, False]), create=True):
                            with mock.patch('notification_pusher.Greenlet', mock.Mock(return_value=worker_mock), create=True):
                                with mock.patch('notification_pusher.done_with_processed_tasks', mock.Mock(), create=True):
                                    with mock.patch('notification_pusher.sleep', mock.Mock(), create=True):
                                        main_loop(config_mock)
                                        self.assertEqual(worker_pool_mock.add.call_count, 1)

    def test_main_loop_with_bad_task(self):
        config_mock = mock.Mock()
        logger_mock = mock.Mock()

        queue_mock = mock.Mock()
        tube_mock = mock.Mock()

        tube_mock.take = mock.Mock(return_value=None)
        queue_mock.tube = mock.Mock(return_value=tube_mock)

        tarantool_queue_mock = mock.Mock()
        tarantool_queue_mock.Queue = mock.Mock(return_value=queue_mock)

        worker_pool_mock = mock.Mock()
        worker_pool_mock.free_count = mock.Mock(return_value=1)

        gevent_mock = mock.Mock()
        processed_task_query_mock = mock.Mock()
        gevent_mock.Queue = mock.Mock(return_value=processed_task_query_mock)

        with mock.patch('notification_pusher.logger', logger_mock, create=True):
            with mock.patch('notification_pusher.tarantool_queue', tarantool_queue_mock, create=True):
                with mock.patch('notification_pusher.Pool', mock.Mock(return_value=worker_pool_mock), create=True):
                    with mock.patch('notification_pusher.gevent_queue', gevent_mock, create=True):
                        with mock.patch('notification_pusher.run_application', mock.Mock(side_effect=[True, False]), create=True):
                            with mock.patch('notification_pusher.done_with_processed_tasks', mock.Mock(), create=True):
                                with mock.patch('notification_pusher.sleep', mock.Mock(), create=True):
                                    main_loop(config_mock)
                                    self.assertFalse(worker_pool_mock.add.called)

    def test_main_without_parameters(self):
        args_mock = mock.Mock()
        args_mock.daemon = None
        args_mock.pidfile = None
        parse_mock = mock.Mock(return_value=args_mock)

        daemonize_mock = mock.Mock()
        create_pidfile_mock = mock.Mock()

        config_mock = mock.Mock()

        with mock.patch('lib.utils.parse_cmd_args', parse_mock, create=True):
            with mock.patch('lib.utils.daemonize', daemonize_mock, create=True):
                with mock.patch('lib.utils.create_pidfile', create_pidfile_mock, create=True):
                    with mock.patch('lib.utils.load_config_from_pyfile', mock.Mock(return_value=config_mock), create=True):
                        with mock.patch('os.path', mock.Mock(), create=True):
                            with mock.patch('notification_pusher.patch_all', mock.Mock(), create=True):
                                with mock.patch('notification_pusher.dictConfig', mock.Mock(), create=True):
                                    with mock.patch('notification_pusher.current_thread', mock.Mock(), create=True):
                                        with mock.patch('notification_pusher.install_signal_handlers', mock.Mock(), create=True):
                                            with mock.patch('notification_pusher.run_application', mock.Mock(side_effect=[True, False]), create=True):
                                                with mock.patch('notification_pusher.main_loop', mock.Mock(), create=True):
                                                    self.assertEqual(main([]), 0)
                                                    self.assertFalse(daemonize_mock.called)
                                                    self.assertFalse(create_pidfile_mock.called)

    def test_main_with_parameters(self):
        args_mock = mock.Mock()
        args_mock.daemon = True
        args_mock.pidfile = True
        parse_mock = mock.Mock(return_value=args_mock)

        daemonize_mock = mock.Mock()
        create_pidfile_mock = mock.Mock()

        config_mock = mock.Mock()

        with mock.patch('lib.utils.parse_cmd_args', parse_mock, create=True):
            with mock.patch('lib.utils.daemonize', daemonize_mock, create=True):
                with mock.patch('lib.utils.create_pidfile', create_pidfile_mock, create=True):
                    with mock.patch('lib.utils.load_config_from_pyfile', mock.Mock(return_value=config_mock), create=True):
                        with mock.patch('os.path', mock.Mock(), create=True):
                            with mock.patch('notification_pusher.patch_all', mock.Mock(), create=True):
                                with mock.patch('notification_pusher.dictConfig', mock.Mock(), create=True):
                                    with mock.patch('notification_pusher.current_thread', mock.Mock(), create=True):
                                        with mock.patch('notification_pusher.install_signal_handlers', mock.Mock(), create=True):
                                            with mock.patch('notification_pusher.run_application', mock.Mock(side_effect=[True, False]), create=True):
                                                with mock.patch('notification_pusher.main_loop', mock.Mock(), create=True):
                                                    self.assertEqual(main([]), 0)
                                                    self.assertEqual(daemonize_mock.call_count, 1)
                                                    self.assertEqual(create_pidfile_mock.call_count, 1)

    def test_main_with_exception(self):
        args_mock = mock.Mock()
        args_mock.daemon = None
        args_mock.pidfile = None
        parse_mock = mock.Mock(return_value=args_mock)

        daemonize_mock = mock.Mock()
        create_pidfile_mock = mock.Mock()

        config_mock = mock.Mock()

        main_loop_mock = mock.Mock(side_effect=Exception)
        sleep_mock = mock.Mock()

        with mock.patch('lib.utils.parse_cmd_args', parse_mock, create=True):
            with mock.patch('lib.utils.daemonize', daemonize_mock, create=True):
                with mock.patch('lib.utils.create_pidfile', create_pidfile_mock, create=True):
                    with mock.patch('lib.utils.load_config_from_pyfile', mock.Mock(return_value=config_mock), create=True):
                        with mock.patch('os.path', mock.Mock(), create=True):
                            with mock.patch('notification_pusher.patch_all', mock.Mock(), create=True):
                                with mock.patch('notification_pusher.dictConfig', mock.Mock(), create=True):
                                    with mock.patch('notification_pusher.current_thread', mock.Mock(), create=True):
                                        with mock.patch('notification_pusher.install_signal_handlers', mock.Mock(), create=True):
                                            with mock.patch('notification_pusher.run_application', mock.Mock(side_effect=[True, False]), create=True):
                                                with mock.patch('notification_pusher.main_loop', main_loop_mock, create=True):
                                                    with mock.patch('notification_pusher.logger', mock.Mock(), create=True):
                                                        with mock.patch('notification_pusher.sleep', sleep_mock, create=True):
                                                            self.assertEqual(main([]), 0)
                                                            self.assertEqual(sleep_mock.call_count, 1)
