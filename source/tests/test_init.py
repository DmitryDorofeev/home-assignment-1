__author__ = 'dmitry'
import unittest
import mock
import lib


class InitTestCase(unittest.TestCase):

    def test_to_unicode_ansi(self):
        self.assertEqual(lib.to_unicode(chr(88)), 'X')

    def test_to_unicode_from_unicode(self):
        self.assertEqual(lib.to_unicode(unichr(88)), 'X')

    def test_prepare_url_none(self):
        self.assertIsNone(lib.prepare_url(None))

    def test_prepare_url_str(self):
        with mock.patch('lib.urlunparse', mock.Mock(return_value='somevalue')):
            self.assertEqual(lib.prepare_url('url'), 'somevalue')