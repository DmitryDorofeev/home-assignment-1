import unittest
import mock
import redirect_checker

__author__ = "leshiy1295"

class RedirectCheckerTestCase(unittest.TestCase):
    def test_condition_is_true(self):
        self.assertTrue(redirect_checker.condition_is_true())

    def test_create_workers(self):
        config_mock = mock.Mock()

        config_mock.WORKER_POOL_SIZE = 10

        child = mock.Mock()

        spawn_mock = mock.Mock()
        worker_mock = mock.Mock()

        ppid = 0
        current_len = 1
        with mock.patch('redirect_checker.active_children', mock.Mock(return_value=[child] * current_len)):
            with mock.patch('redirect_checker.logger', mock.Mock(), create=True):
                with mock.patch('redirect_checker.spawn_workers', spawn_mock, create=True):
                    with mock.patch('redirect_checker.worker', worker_mock, create=True):
                        redirect_checker.create_workers(config_mock, ppid)
                        spawn_mock.assert_called_once_with(num=config_mock.WORKER_POOL_SIZE - current_len,
                                                           target=worker_mock,
                                                           args=(config_mock,),
                                                           parent_pid=ppid)

    def test_create_workers_with_full_pool(self):
        config_mock = mock.Mock()

        config_mock.WORKER_POOL_SIZE = 10

        child = mock.Mock()

        ppid = 0
        current_len = 10
        mocked_method = mock.Mock()
        with mock.patch('redirect_checker.active_children', mock.Mock(return_value=[child] * current_len)):
            with mock.patch('redirect_checker.my_mocked_method_for_test', mocked_method, create=True):
                redirect_checker.create_workers(config_mock, ppid)
                mocked_method.assert_called_once_with('full_pool')

    def test_remove_workers(self):
        child = mock.Mock()
        child.terminate = mock.Mock()

        current_len = 5
        with mock.patch('redirect_checker.logger', mock.Mock(), create=True):
            with mock.patch('redirect_checker.active_children', mock.Mock(return_value=[child] * current_len)):
                redirect_checker.remove_workers()
                self.assertEqual(child.terminate.call_count, current_len)

    def test_main_loop_with_good_network_status(self):
        config_mock = mock.Mock()
        config_mock.SLEEP = 10

        child = mock.Mock()
        child.terminate = mock.Mock()

        create_workers_mock = mock.Mock()

        ppid = 0
        sleep_mock = mock.Mock()
        with mock.patch('redirect_checker.logger', mock.Mock(), create=True):
            with mock.patch('os.getpid', mock.Mock(return_value=ppid), create=True):
                with mock.patch('redirect_checker.condition_is_true', mock.Mock(side_effect=[True, False]), create=True):
                    with mock.patch('redirect_checker.check_network_status', mock.Mock(return_value=True), create=True):
                        with mock.patch('redirect_checker.create_workers', create_workers_mock, create=True):
                            with mock.patch('redirect_checker.sleep', sleep_mock, create=True):
                                redirect_checker.main_loop(config_mock)
                                create_workers_mock.assert_called_once_with(config_mock, ppid)
                                sleep_mock.assert_called_once_with(config_mock.SLEEP)

    def test_main_loop_with_bad_network_status(self):
        config_mock = mock.Mock()
        config_mock.SLEEP = 10

        remove_workers_mock = mock.Mock()

        ppid = 0
        sleep_mock = mock.Mock()
        with mock.patch('redirect_checker.logger', mock.Mock(), create=True):
            with mock.patch('os.getpid', mock.Mock(return_value=ppid), create=True):
                with mock.patch('redirect_checker.condition_is_true', mock.Mock(side_effect=[True, False]), create=True):
                    with mock.patch('redirect_checker.check_network_status', mock.Mock(return_value=False), create=True):
                        with mock.patch('redirect_checker.remove_workers', remove_workers_mock, create=True):
                            with mock.patch('redirect_checker.sleep', sleep_mock, create=True):
                                redirect_checker.main_loop(config_mock)
                                remove_workers_mock.assert_called_once_with()
                                sleep_mock.assert_called_once_with(config_mock.SLEEP)

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
