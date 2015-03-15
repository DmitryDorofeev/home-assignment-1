import unittest
import mock
from notification_pusher import load_config_from_pyfile, notification_worker


class NotificationPusherTestCase(unittest.TestCase):

    def test_parse_config(self):
        cfg = load_config_from_pyfile('./source/config/checker_config.py')  # TODO: MOCK!!
        self.assertEqual(cfg.SLEEP, 10)
        self.assertEqual(cfg.INPUT_QUEUE_HOST, 'localhost')


    # def test_notification_worker(self):
    #     returned = 0
    #
    #     def put_to_task(task, text):
    #         returned = text
    #
    #     with mock.patch('requests.post', mock.Mock()):
    #         with mock.patch('task_queue.put', mock.Mock(side_effect=put_to_task)):
    #             notification_worker()

    def test_done_with_proceed_tasks(self):
        pass