import unittest
import mock
import redirect_checker

__author__ = "leshiy1295"

class RedirectCheckerTestCase(unittest.TestCase):
    def test_main(self):
        args_mock = mock.Mock()
        parse_mock = mock.Mock(return_value=args_mock)
        config_mock = mock.Mock()
        config_mock.EXIT_CODE = 0
        get_config_mock = mock.Mock(return_value=config_mock)

        with mock.patch('redirect_checker.parse_cmd_args', parse_mock, create=True):
            with mock.patch('redirect_checker.utils.get_config_with_args', get_config_mock, create=True):
                with mock.patch('redirect_checker.main_loop', mock.Mock(), create=True):
                    self.assertEqual(redirect_checker.main([]), config_mock.EXIT_CODE)

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
                                        self.assertEqual(spawn_mock.call_count, 1)

    def test_main_loop_with_good_network_status_without_workers(self):
        config_mock = mock.Mock()

        config_mock.WORKER_POOL_SIZE = 0

        child = mock.Mock()

        spawn_mock = mock.Mock()

        with mock.patch('redirect_checker.logger', mock.Mock(), create=True):
            with mock.patch('os.getpid', mock.Mock(return_value=0), create=True):
                with mock.patch('redirect_checker.condition_is_true', mock.Mock(side_effect=[True, False]), create=True):
                    with mock.patch('redirect_checker.check_network_status', mock.Mock(return_value=True), create=True):
                        with mock.patch('redirect_checker.active_children', mock.Mock(return_value=[child, child])):
                            with mock.patch('redirect_checker.spawn_workers', spawn_mock, create=True):
                                with mock.patch('redirect_checker.worker', mock.Mock(), create=True):
                                    with mock.patch('redirect_checker.sleep', mock.Mock(), create=True):
                                        redirect_checker.main_loop(config_mock)
                                        self.assertFalse(spawn_mock.called)

    def test_main_loop_with_bad_network_status(self):
        config_mock = mock.Mock()

        config_mock.WORKER_POOL_SIZE = 10

        child = mock.Mock()
        child.terminate = mock.Mock()

        spawn_mock = mock.Mock()

        with mock.patch('redirect_checker.logger', mock.Mock(), create=True):
            with mock.patch('os.getpid', mock.Mock(return_value=0), create=True):
                with mock.patch('redirect_checker.condition_is_true', mock.Mock(side_effect=[True, False]), create=True):
                    with mock.patch('redirect_checker.check_network_status', mock.Mock(return_value=False), create=True):
                        with mock.patch('redirect_checker.active_children', mock.Mock(return_value=[child, child])):
                            with mock.patch('redirect_checker.spawn_workers', spawn_mock, create=True):
                                with mock.patch('redirect_checker.worker', mock.Mock(), create=True):
                                    with mock.patch('redirect_checker.sleep', mock.Mock(), create=True):
                                        redirect_checker.main_loop(config_mock)
                                        self.assertEqual(child.terminate.call_count, 2)
