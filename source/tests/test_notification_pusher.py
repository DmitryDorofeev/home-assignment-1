import unittest
import mock
from notification_pusher import notification_worker, done_with_processed_tasks, install_signal_handlers


class NotificationPusherTestCase(unittest.TestCase):
    def test_notification_worker(self):
        data_mock = mock.Mock()
        task_mock = mock.Mock()

        task_mock.data.copy.return_value = {'id': 1, 'callback_url': 2}
        queue_mock = mock.Mock()
        with mock.patch('notification_pusher.current_thread', mock.Mock(), create=True):
            with mock.patch('notification_pusher.logger', mock.Mock(), create=True):
                with mock.patch('notification_pusher.json', mock.Mock(), create=True):
                    with mock.patch('notification_pusher.requests', mock.Mock(), create=True):
                        notification_worker(task_mock, queue_mock)
                        self.assertEqual(queue_mock.put.call_count, 1)

    def test_done_with_proceed_tasks(self):
        size = 7
        queue_mock = mock.Mock()
        task_mock = mock.Mock()
        queue_mock.qsize.return_value = size
        queue_mock.get_nowait.return_value = (task_mock, 'someaction')
        with mock.patch('notification_pusher.logger', mock.Mock(), create=True):
            done_with_processed_tasks(queue_mock)
            self.assertEqual(task_mock.someaction.call_count, size)

    def test_install_signal_handlers(self):
        gevent_mock = mock.Mock()
        gevent_mock.signal.return_value = None
        with mock.patch('gevent.signal', gevent_mock, create=True):
            install_signal_handlers()
            self.assertEqual(4, gevent_mock.call_count)