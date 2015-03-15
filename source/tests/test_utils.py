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
        pid = 0
        with mock.patch('os.fork', mock.Mock(return_value=pid)):
            with mock.patch('os._exit', mock.Mock()):
                with mock.patch('os.setsid', mock.Mock()):
                    utils.daemonize()

    def test_create_pidfile(self):
        pid = 42
        m_open = mock.mock_open()
        with mock.patch('lib.utils.open', m_open, create=True):
            with mock.patch('os.getpid', mock.Mock(return_value=pid)):
                utils.create_pidfile('/some/path')

        m_open.assert_called_once_with('/some/path', 'w')
        m_open().write.assert_called_once_with(str(pid))
