import unittest
import mock
import redirect_checker

__author__ = "leshiy1295"

class RedirectCheckerTestCase(unittest.TestCase):
    def test_main_without_parameters(self):
        config_mock = mock.Mock()
        config_mock.EXIT_CODE = 0

        args = mock.Mock()
        args.daemon = None
        args.pidfile = None
        parse_mock = mock.Mock(return_value=args)

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

        args = mock.Mock()
        args.daemon = True
        args.pidfile = None
        parse_mock = mock.Mock(return_value=args)

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

        args = mock.Mock()
        args.daemon = None
        args.pidfile = True
        parse_mock = mock.Mock(return_value=args)

        redirect_checker_mock = mock.Mock(return_value=config_mock)
        create_pidfile_mock = mock.Mock()
        with mock.patch('redirect_checker.parse_cmd_args', parse_mock, create=True):
            with mock.patch('redirect_checker.create_pidfile', create_pidfile_mock, create=True):
                with mock.patch('redirect_checker.load_config_from_pyfile', redirect_checker_mock, create=True):
                    with mock.patch('os.path', mock.Mock(), create=True):
                        with mock.patch('redirect_checker.dictConfig', mock.Mock(), create=True):
                            with mock.patch('redirect_checker.main_loop', mock.Mock(), create=True):
                                self.assertEqual(redirect_checker.main([]), config_mock.EXIT_CODE)
                                create_pidfile_mock.assert_called_once_with(args.pidfile)
