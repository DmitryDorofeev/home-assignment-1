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

    def prepare_url_err(self):
        with mock.patch("lib.urlparse", mock.Mock(return_value=(None, u'.', None, None, None, None))):
            with mock.patch("lib.quote", mock.Mock()):
                with mock.patch("lib.quote_plus", mock.Mock()):
                    with mock.patch("lib.urlunparse", mock.Mock(return_value='somevalue')):
                        self.assertEqual(lib.prepare_url('url'), 'somevalue')

    def test_make_pycurl_req(self):
        curl_mock = mock.Mock()
        curl_mock.getinfo.return_value = 'url'
        with mock.patch('lib.pycurl.Curl', mock.Mock(return_value=curl_mock)):
            self.assertEqual(lib.make_pycurl_request('url', None), ('', 'url'))

    def test_get_counters(self):
        self.assertEqual(lib.get_counters('google-analytics.com/ga.js'), ['GOOGLE_ANALYTICS'])
        self.assertEqual(lib.get_counters('google-analytics.com/ga.js mc.yandex.ru/metrika/watch.js'), ['GOOGLE_ANALYTICS', 'YA_METRICA'])
        self.assertEqual(lib.get_counters('lal'), [])

    def test_fix_market_url(self):
        self.assertEqual(lib.fix_market_url('market://sampleapp'), 'http://play.google.com/store/apps/sampleapp')
        self.assertEqual(lib.fix_market_url('shop://sampleapp'), 'http://play.google.com/store/apps/shop://sampleapp')
        self.assertEqual(lib.fix_market_url(''), 'http://play.google.com/store/apps/')