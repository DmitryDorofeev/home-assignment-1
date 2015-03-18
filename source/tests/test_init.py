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

    def test_make_pycurl_req_uaer_agent(self):
        curl_mock = mock.Mock()
        curl_mock.getinfo.return_value = 'url'
        with mock.patch('lib.pycurl.Curl', mock.Mock(return_value=curl_mock)):
            self.assertEqual(lib.make_pycurl_request('url', None, 'user_agent'), ('', 'url'))

    def test_get_counters(self):
        self.assertEqual(lib.get_counters('google-analytics.com/ga.js'), ['GOOGLE_ANALYTICS'])
        self.assertEqual(lib.get_counters('google-analytics.com/ga.js mc.yandex.ru/metrika/watch.js'),
                         ['GOOGLE_ANALYTICS', 'YA_METRICA'])
        self.assertEqual(lib.get_counters('lal'), [])

    def test_fix_market_url(self):
        self.assertEqual(lib.fix_market_url('market://sampleapp'), 'http://play.google.com/store/apps/sampleapp')
        self.assertEqual(lib.fix_market_url('sampleapp'), 'http://play.google.com/store/apps/sampleapp')
        self.assertEqual(lib.fix_market_url(''), 'http://play.google.com/store/apps/')

    def test_get_url_err(self):
        with mock.patch('lib.make_pycurl_request', mock.Mock(side_effect=ValueError)):
            with mock.patch('lib.logger', mock.Mock()):
                self.assertEqual(lib.get_url(None, None, None), (None, 'ERROR', None))

    def test_get_url_new(self):
        with mock.patch('lib.make_pycurl_request',
                        mock.Mock(return_value=('content', 'http://odnoklassniki.ru/azazst.redirect'))):
            with mock.patch('lib.logger', mock.Mock()):
                self.assertEqual(lib.get_url('http://odnoklassniki.ru/st.redirect', None, None),
                                 (None, None, 'content'))

    def test_get_url_new_url_empty(self):
        with mock.patch('lib.make_pycurl_request',
                        mock.Mock(return_value=(None, 'url'))):
            with mock.patch('lib.logger', mock.Mock()):
                self.assertEqual(lib.get_url(None, None, None), ('url', 'http_status', None))

    def test_check_for_meta_len(self):
        html = '<meta content="" http-equiv="refresh">'
        self.assertEqual(lib.check_for_meta(html, 'http://localhost'), None)

    def test_check_for_meta_all(self):
        html = '<meta content=";url=index.html" http-equiv="refresh">'
        self.assertEqual(lib.check_for_meta(html, 'http://localhost/'), 'http://localhost/index.html')

    def test_check_for_meta_not_m(self):
        html = '<meta content=";" http-equiv="refresh">'
        self.assertEqual(lib.check_for_meta(html, 'http://localhost/'), None)

    def test_check_for_meta_none(self):
        html = '<>'
        self.assertEqual(lib.check_for_meta(html, 'http://localhost/'), None)