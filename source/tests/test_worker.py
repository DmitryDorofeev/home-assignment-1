__author__ = 'leshiy1295'

import unittest
import mock
from lib.worker import get_redirect_history_from_task, worker


class WorkerTestCase(unittest.TestCase):

    def test_get_redirect(self):
        to_unicode_mock = mock.Mock(return_value=u'url')
        task_mock = mock.Mock()
        task_mock.data = {'url': 'url', 'url_id': 7}
        with mock.patch('lib.worker.to_unicode', to_unicode_mock, create=True):
            with mock.patch('lib.worker.logger', mock.Mock(), create=True):
                with mock.patch('lib.worker.get_redirect_history', mock.Mock(return_value=([], [], []))):
                    is_input, data = get_redirect_history_from_task(task_mock, 10)
                    self.assertEqual(False, is_input)

    def test_get_redirect_with_suspicious(self):
        to_unicode_mock = mock.Mock(return_value=u'url')
        task_mock = mock.Mock()
        task_mock.data = {'url': 'url', 'url_id': 7, 'suspicious': 'some text'}
        with mock.patch('lib.worker.to_unicode', to_unicode_mock, create=True):
            with mock.patch('lib.worker.logger', mock.Mock(), create=True):
                with mock.patch('lib.worker.get_redirect_history', mock.Mock(return_value=([], [], []))):
                    is_input, data = get_redirect_history_from_task(task_mock, 10)
                    self.assertEqual(False, is_input)

    def test_get_redirect_with_error(self):
        to_unicode_mock = mock.Mock(return_value=u'url')
        task_mock = mock.Mock()
        task_mock.data = {'url': 'url', 'url_id': 7}
        with mock.patch('lib.worker.to_unicode', to_unicode_mock, create=True):
            with mock.patch('lib.worker.logger', mock.Mock(), create=True):
                with mock.patch('lib.worker.get_redirect_history', mock.Mock(return_value=(['ERROR'], [], []))):
                    is_input, data = get_redirect_history_from_task(task_mock, 10)
                    self.assertEqual(True, is_input)
