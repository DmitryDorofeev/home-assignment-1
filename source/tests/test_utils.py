__author__ = 'dmitry'
import unittest
import mock
from lib import utils


class UtilsTestCase(unittest.TestCase):
    def test_parse_cmd_args(self):
        args = ['-c', 'test']
        parsed_arguments = utils.parse_cmd_args(args)

        self.assertEqual(parsed_arguments.config, 'test')
        self.assertFalse(parsed_arguments.daemon)
        self.assertIsNone(parsed_arguments.pidfile)

        args2 = ['-c', 'test', '-d']
        parsed_arguments2 = utils.parse_cmd_args(args2)

        self.assertEqual(parsed_arguments2.config, 'test')
        self.assertTrue(parsed_arguments2.daemon)
        self.assertIsNone(parsed_arguments.pidfile)

    def test_daemonize(self):
        pid = 7
        with mock.patch('os.fork', mock.Mock(return_value=pid)):
            with mock.patch('os._exit', mock.Mock()) as mock_exit:
                with mock.patch('os.setsid', mock.Mock()):
                    utils.daemonize()
                    self.assertTrue(mock_exit.called)

    def test_create_pidfile(self):
        pid = 42
        m_open = mock.mock_open()
        with mock.patch('lib.utils.open', m_open, create=True):
            with mock.patch('os.getpid', mock.Mock(return_value=pid)):
                utils.create_pidfile('/some/path')

        m_open.assert_called_once_with('/some/path', 'w')
        m_open().write.assert_called_once_with(str(pid))

    def test_parse_config(self):
        cfg = utils.load_config_from_pyfile('./source/config/checker_config.py')  # TODO: MOCK!!
        self.assertEqual(cfg.SLEEP, 10)
        self.assertEqual(cfg.INPUT_QUEUE_HOST, 'localhost')

    def test_get_tube(self):
        name_str = 'name'

        class Queue():
            def tube(self, name):
                return name

        queue = Queue()
        with mock.patch('lib.utils.tarantool_queue.Queue', mock.Mock(return_value=queue)):
            self.assertEqual(utils.get_tube(None, None, None, name_str), name_str)