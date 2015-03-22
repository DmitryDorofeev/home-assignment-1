__author__ = 'dmitry'
import unittest
import mock
from lib import utils


class UtilsTestCase(unittest.TestCase):
    def test_get_config_without_parameters(self):
        config_mock = mock.Mock()
        config_mock.EXIT_CODE = 0

        args_mock = mock.Mock()
        args_mock.daemon = None
        args_mock.pidfile = None

        load_config_mock = mock.Mock(return_value=config_mock)
        daemonize_mock = mock.Mock()
        create_pidfile_mock = mock.Mock()
        with mock.patch('lib.utils.daemonize', daemonize_mock, create=True):
            with mock.patch('lib.utils.create_pidfile', create_pidfile_mock, create=True):
                with mock.patch('lib.utils.load_config_from_pyfile', load_config_mock, create=True):
                    with mock.patch('os.path', mock.Mock(), create=True):
                        with mock.patch('lib.utils.dictConfig', mock.Mock(), create=True):
                            self.assertEqual(utils.get_config_with_args(args_mock), config_mock)
                            self.assertFalse(daemonize_mock.called)
                            self.assertFalse(create_pidfile_mock.called)

    def test_get_config_with_daemon_parameter(self):
        config_mock = mock.Mock()
        config_mock.EXIT_CODE = 0

        args_mock = mock.Mock()
        args_mock.daemon = True
        args_mock.pidfile = None

        load_config_mock = mock.Mock(return_value=config_mock)
        daemonize_mock = mock.Mock()
        with mock.patch('lib.utils.daemonize', daemonize_mock, create=True):
            with mock.patch('lib.utils.load_config_from_pyfile', load_config_mock, create=True):
                with mock.patch('os.path', mock.Mock(), create=True):
                    with mock.patch('lib.utils.dictConfig', mock.Mock(), create=True):
                        utils.get_config_with_args(args_mock)
                        daemonize_mock.assert_called_once_with()

    def test_get_config_with_pidfile_parameter(self):
        config_mock = mock.Mock()
        config_mock.EXIT_CODE = 0

        args_mock = mock.Mock()
        args_mock.daemon = None
        args_mock.pidfile = True

        load_config_mock = mock.Mock(return_value=config_mock)
        create_pidfile_mock = mock.Mock()
        daemonize_mock = mock.Mock()
        with mock.patch('lib.utils.daemonize', daemonize_mock, create=True):
            with mock.patch('lib.utils.create_pidfile', create_pidfile_mock, create=True):
                with mock.patch('lib.utils.load_config_from_pyfile', load_config_mock, create=True):
                    with mock.patch('os.path', mock.Mock(), create=True):
                        with mock.patch('lib.utils.dictConfig', mock.Mock(), create=True):
                            self.assertEqual(utils.get_config_with_args(args_mock), config_mock)
                            self.assertFalse(daemonize_mock.called)
                            create_pidfile_mock.assert_called_once_with(args_mock.pidfile)

    def test_parse_cmd_args_config(self):
        args = ['-c', 'test']
        parsed_arguments = utils.parse_cmd_args(args)

        self.assertEqual(parsed_arguments.config, 'test')
        self.assertFalse(parsed_arguments.daemon)
        self.assertIsNone(parsed_arguments.pidfile)

    def test_parse_cmd_args_daemon(self):
        args = ['-c', 'test', '-d']
        parsed_arguments = utils.parse_cmd_args(args)

        self.assertEqual(parsed_arguments.config, 'test')
        self.assertTrue(parsed_arguments.daemon)
        self.assertIsNone(parsed_arguments.pidfile)

    def test_parse_cmd_args_err(self):
        args = []
        with mock.patch('argparse.ArgumentParser.error', mock.Mock()) as parse_error:
            parsed_arguments = utils.parse_cmd_args(args)
            self.assertTrue(parse_error.called)

    def test_daemonize(self):
        pid = 7
        with mock.patch('os.fork', mock.Mock(return_value=pid)):
            with mock.patch('os._exit', mock.Mock()) as mock_exit:
                with mock.patch('os.setsid', mock.Mock()):
                    utils.daemonize()
                    self.assertEqual(mock_exit.call_count, 1)

    def test_daemonize_exc(self):
        with mock.patch('os.fork', mock.Mock(side_effect=OSError(1, 'Hi!')), create=True):
            with mock.patch('os._exit', mock.Mock()):
                with mock.patch('os.setsid', mock.Mock()):
                    with self.assertRaises(Exception):
                        utils.daemonize()

    def test_daemonize_pid0(self):
        with mock.patch('os.fork', mock.Mock(return_value=0), create=True):
            with mock.patch('os._exit', mock.Mock()) as mock_exit:
                with mock.patch('os.setsid', mock.Mock()):
                    utils.daemonize()
                    self.assertEqual(mock_exit.call_count, 0)

    def test_daemonize_pid0_exc(self):
        with mock.patch('os.fork', mock.Mock(side_effect=[0, OSError(1, 'Bye')]), create=True):
            with mock.patch('os._exit', mock.Mock()) as mock_exit:
                with mock.patch('os.setsid', mock.Mock()):
                    with self.assertRaises(Exception):
                        utils.daemonize()

    def test_daemonize_pid0_pidnot0(self):
        with mock.patch('os.fork', mock.Mock(side_effect=[0, 7]), create=True):
            with mock.patch('os._exit', mock.Mock(), create=True) as mock_exit:
                with mock.patch('os.setsid', mock.Mock()):
                    utils.daemonize()
                    self.assertEqual(mock_exit.call_count, 1)

    def test_create_pidfile(self):
        pid = 42
        m_open = mock.mock_open()
        with mock.patch('lib.utils.open', m_open, create=True):
            with mock.patch('os.getpid', mock.Mock(return_value=pid)):
                utils.create_pidfile('/some/path')

        m_open.assert_called_once_with('/some/path', 'w')
        m_open().write.assert_called_once_with(str(pid))

    def test_parse_config(self):
        def file_mock(filepath, variables):
            variables.update({
                'testvar': 'str',
                'TEST': True
            })

        cfg = utils.Config()
        with mock.patch('__builtin__.execfile', mock.Mock(side_effect=file_mock)):
            self.assertEqual(type(utils.load_config_from_pyfile('filepath')), type(cfg))
            with self.assertRaises(AttributeError):
                utils.load_config_from_pyfile('filepath').testvar
            self.assertEqual(utils.load_config_from_pyfile('filepath').TEST, True)

    def test_get_tube(self):
        name_str = 'name'
        queue_mock = mock.Mock()
        queue_mock.tube.return_value = name_str
        with mock.patch('lib.utils.tarantool_queue.Queue', mock.Mock(return_value=queue_mock)):
            self.assertEqual(utils.get_tube(None, None, None, name_str), name_str)

    def test_spawn_workers(self):
        p_mock = mock.Mock()
        process_mock = mock.Mock(return_value=p_mock)
        with mock.patch('lib.utils.Process', process_mock):
            utils.spawn_workers(7, None, None, 9)
            self.assertEqual(process_mock.call_count, 7)
            self.assertTrue(process_mock.daemon)
            self.assertEqual(p_mock.start.call_count, 7)

    def test_check_network_ok(self):
        with mock.patch('lib.utils.urllib2.urlopen', mock.Mock()):
            self.assertTrue(utils.check_network_status('url', 7))

    def test_check_network_fail(self):
        with mock.patch('lib.utils.urllib2.urlopen', mock.Mock(side_effect=ValueError)):
            self.assertFalse(utils.check_network_status('url', 7))