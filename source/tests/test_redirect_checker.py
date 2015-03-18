import unittest
import mock
import redirect_checker

__author__ = "leshiy1295"

class RedirectCheckerTestCase(unittest.TestCase):
    def test_main_without_parameters(self):
        config_mock = mock.Mock()
        config_mock.EXIT_CODE = 0

        args_mock = mock.Mock()
        args_mock.daemon = None
        args_mock.pidfile = None
        parse_mock = mock.Mock(return_value=args_mock)

        redirect_checker_mock = mock.Mock(return_value=config_mock)
        daemonize_mock = mock.Mock()
        create_pidfile_mock = mock.Mock()
        with mock.patch('redirect_checker.parse_cmd_args', parse_mock, create=True):
            with mock.patch('redirect_checker.daemonize', daemonize_mock, create=True):
                with mock.patch('redirect_checker.create_pidfile', create_pidfile_mock, create=True):
                    with mock.patch('redirect_checker.load_config_from_pyfile', redirect_checker_mock, create=True):
                        with mock.patch('os.path', mock.Mock(), create=True):
                            with mock.patch('redirect_checker.dictConfig', mock.Mock(), create=True):
                                with mock.patch('redirect_checker.main_loop', mock.Mock(), create=True):
                                    self.assertEqual(redirect_checker.main([]), config_mock.EXIT_CODE)
                                    self.assertFalse(daemonize_mock.called)
                                    self.assertFalse(create_pidfile_mock.called)

    def test_main_with_daemon_parameter(self):
        config_mock = mock.Mock()
        config_mock.EXIT_CODE = 0

        args_mock = mock.Mock()
        args_mock.daemon = True
        args_mock.pidfile = None
        parse_mock = mock.Mock(return_value=args_mock)

        redirect_checker_mock = mock.Mock(return_value=config_mock)
        daemonize_mock = mock.Mock()
        with mock.patch('redirect_checker.parse_cmd_args', parse_mock, create=True):
            with mock.patch('redirect_checker.daemonize', daemonize_mock, create=True):
                with mock.patch('redirect_checker.load_config_from_pyfile', redirect_checker_mock, create=True):
                    with mock.patch('os.path', mock.Mock(), create=True):
                        with mock.patch('redirect_checker.dictConfig', mock.Mock(), create=True):
                            with mock.patch('redirect_checker.main_loop', mock.Mock(), create=True):
                                self.assertEqual(redirect_checker.main([]), config_mock.EXIT_CODE)
                                daemonize_mock.assert_called_once_with()

    def test_main_with_pidfile_parameter(self):
        config_mock = mock.Mock()
        config_mock.EXIT_CODE = 0

        args_mock = mock.Mock()
        args_mock.daemon = None
        args_mock.pidfile = True
        parse_mock = mock.Mock(return_value=args_mock)

        redirect_checker_mock = mock.Mock(return_value=config_mock)
        create_pidfile_mock = mock.Mock()
        with mock.patch('redirect_checker.parse_cmd_args', parse_mock, create=True):
            with mock.patch('redirect_checker.create_pidfile', create_pidfile_mock, create=True):
                with mock.patch('redirect_checker.load_config_from_pyfile', redirect_checker_mock, create=True):
                    with mock.patch('os.path', mock.Mock(), create=True):
                        with mock.patch('redirect_checker.dictConfig', mock.Mock(), create=True):
                            with mock.patch('redirect_checker.main_loop', mock.Mock(), create=True):
                                self.assertEqual(redirect_checker.main([]), config_mock.EXIT_CODE)
                                create_pidfile_mock.assert_called_once_with(args_mock.pidfile)

    def test_main_loop_with_good_network_status(self):
        config_mock = mock.Mock()

        config_mock.WORKER_POOL_SIZE = 10

        child = mock.Mock()
        child.terminate = mock.Mock()

        spawn_mock = mock.Mock()
        worker_mock = mock.Mock()

        with mock.patch('redirect_checker.logger', mock.Mock(), create=True):
            with mock.patch('os.getpid', mock.Mock(return_value=0), create=True):
                with mock.patch('redirect_checker.condition_is_true', mock.Mock(side_effect=[True, False]), create=True):
                    with mock.patch('redirect_checker.check_network_status', mock.Mock(return_value=True), create=True):
                        with mock.patch('redirect_checker.active_children', mock.Mock(return_value=[child, child])):
                            with mock.patch('redirect_checker.spawn_workers', spawn_mock, create=True):
                                with mock.patch('redirect_checker.worker', worker_mock, create=True):
                                    with mock.patch('redirect_checker.sleep', mock.Mock(), create=True):
                                        redirect_checker.main_loop(config_mock)
                                        self.assertTrue(spawn_mock.called)

    def test_main_loop_with_good_network_status_without_workers(self):
        config_mock = mock.Mock()

        config_mock.WORKER_POOL_SIZE = 0

        child = mock.Mock()
        child.terminate = mock.Mock()

        spawn_mock = mock.Mock()
        worker_mock = mock.Mock()

        with mock.patch('redirect_checker.logger', mock.Mock(), create=True):
            with mock.patch('os.getpid', mock.Mock(return_value=0), create=True):
                with mock.patch('redirect_checker.condition_is_true', mock.Mock(side_effect=[True, False]), create=True):
                    with mock.patch('redirect_checker.check_network_status', mock.Mock(return_value=True), create=True):
                        with mock.patch('redirect_checker.active_children', mock.Mock(return_value=[child, child])):
                            with mock.patch('redirect_checker.spawn_workers', spawn_mock, create=True):
                                with mock.patch('redirect_checker.worker', worker_mock, create=True):
                                    with mock.patch('redirect_checker.sleep', mock.Mock(), create=True):
                                        redirect_checker.main_loop(config_mock)
                                        self.assertFalse(spawn_mock.called)

    def test_main_loop_with_bad_network_status(self):
        config_mock = mock.Mock()

        config_mock.WORKER_POOL_SIZE = 10

        child = mock.Mock()
        child.terminate = mock.Mock()

        spawn_mock = mock.Mock()
        worker_mock = mock.Mock()

        with mock.patch('redirect_checker.logger', mock.Mock(), create=True):
            with mock.patch('os.getpid', mock.Mock(return_value=0), create=True):
                with mock.patch('redirect_checker.condition_is_true', mock.Mock(side_effect=[True, False]), create=True):
                    with mock.patch('redirect_checker.check_network_status', mock.Mock(return_value=False), create=True):
                        with mock.patch('redirect_checker.active_children', mock.Mock(return_value=[child, child])):
                            with mock.patch('redirect_checker.spawn_workers', spawn_mock, create=True):
                                with mock.patch('redirect_checker.worker', worker_mock, create=True):
                                    with mock.patch('redirect_checker.sleep', mock.Mock(), create=True):
                                        redirect_checker.main_loop(config_mock)
                                        self.assertTrue(child.terminate.called)

