__author__ = 'dmitry'

import unittest
import mock
from lib.worker import get_redirect_history_from_task, worker


class WorkerTestCase(unittest.TestCase):

    def test_get_redirect(self):
        to_unicode_mock = mock.Mock(return_value=u'url')
        logger_mock = mock.Mock()
        task_mock = mock.Mock()
        task_mock.data = {'url': 'url', 'url_id': 7}
        with mock.patch('lib.worker.to_unicode', to_unicode_mock, create=True):
            with mock.patch('lib.worker.logger', logger_mock, create=True):
                is_input, data = get_redirect_history_from_task(task_mock, 10)
                self.assertEqual(True, is_input)

