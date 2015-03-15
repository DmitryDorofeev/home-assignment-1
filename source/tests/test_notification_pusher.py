import unittest
import mock
from notification_pusher import create_pidfile, load_config_from_pyfile, parse_cmd_args


class NotificationPusherTestCase(unittest.TestCase):
    def test_create_pidfile_example(self):
        pid = 42
        m_open = mock.mock_open()
        with mock.patch('notification_pusher.open', m_open, create=True):
            with mock.patch('os.getpid', mock.Mock(return_value=pid)):
                create_pidfile('/tmp')

        m_open.assert_called_once_with('/tmp', 'w')
        m_open().write.assert_called_once_with(str(pid))

    def test_parse_config(self):
        cfg = load_config_from_pyfile('./source/config/checker_config.py')  # TODO: MOCK!!
        self.assertEqual(cfg.SLEEP, 10)
        self.assertEqual(cfg.INPUT_QUEUE_HOST, 'localhost')

    def test_parse_cmd_args(self):
        args = ['-c', 'test']
        parsed_arguments = parse_cmd_args(args)

        self.assertEqual(parsed_arguments.config, 'test')
        self.assertFalse(parsed_arguments.daemon)
        self.assertIsNone(parsed_arguments.pidfile)

        args2 = ['-c', 'test', '-d']
        parsed_arguments2 = parse_cmd_args(args2)

        self.assertEqual(parsed_arguments2.config, 'test')
        self.assertTrue(parsed_arguments2.daemon)
        self.assertIsNone(parsed_arguments.pidfile)

    def test_notification_worker(self):
        pass

    def test_done_with_proceed_tasks(self):
        pass