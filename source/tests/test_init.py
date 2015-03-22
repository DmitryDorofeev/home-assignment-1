__author__ = 'dmitry'
import unittest
import mock
import lib


class InitTestCase(unittest.TestCase):
    def test_to_unicode_ansi(self):
        res = lib.to_unicode('Xss')
        self.assertEqual(res, u'Xss')
        self.assertTrue(isinstance(res, unicode))

    def test_to_unicode_from_unicode(self):
        res = lib.to_unicode(u'TEsT')
        self.assertEqual(res, u'TEsT')
        self.assertTrue(isinstance(res, unicode))

    def test_to_str_from_unicode(self):
        res = lib.to_str(u'sample')
        self.assertEqual(res, 'sample')
        self.assertTrue(isinstance(res, str))

    def test_prepare_url_none(self):
        self.assertIsNone(lib.prepare_url(None))

    def test_prepare_url_str(self):
        with mock.patch('lib.urlunparse', mock.Mock(return_value='somevalue')):
            self.assertEqual(lib.prepare_url('url'), 'somevalue')

    def test_prepare_url_err(self):
        with mock.patch("lib.urlparse", mock.Mock(return_value=(None, u'.', None, None, None, None))):
            with mock.patch("lib.quote", mock.Mock()):
                with mock.patch("lib.quote_plus", mock.Mock()):
                    with mock.patch("lib.urlunparse", mock.Mock(return_value='somevalue')):
                        self.assertEqual(lib.prepare_url('url'), 'somevalue')

    def test_prepare_url_exception(self):
        netloc = mock.Mock()
        netloc.encode.side_effect = UnicodeError
        with mock.patch("lib.urlparse", mock.Mock(return_value=(None, netloc, None, None, None, None))):
            with mock.patch("lib.quote", mock.Mock()):
                with mock.patch("lib.quote_plus", mock.Mock()):
                    with mock.patch("lib.urlunparse", mock.Mock(return_value='somevalue')):
                        self.assertEqual(lib.prepare_url('url'), 'somevalue')

    def test_make_pycurl_req(self):
        curl_mock = mock.Mock()
        curl_mock.getinfo.return_value = 'url'
        with mock.patch('lib.pycurl.Curl', mock.Mock(return_value=curl_mock)):
            self.assertEqual(lib.make_pycurl_request('url', None), ('', 'url'))

    def test_make_pycurl_req_user_agent(self):
        def ret(param):
            return param

        curl_mock = mock.Mock()
        curl_mock.REDIRECT_URL = 'url'
        curl_mock.getinfo.side_effect = ret
        with mock.patch('lib.pycurl.Curl', mock.Mock(return_value=curl_mock)):
            self.assertEqual(lib.make_pycurl_request('url', None, 'user_agent'), ('', 'url'))

    def test_make_pycurl_req_redirect_url_is_None(self):
        def ret(param):
            return param

        curl_mock = mock.Mock()
        curl_mock.REDIRECT_URL = None
        curl_mock.getinfo.side_effect = ret
        with mock.patch('lib.pycurl.Curl', mock.Mock(return_value=curl_mock)):
            self.assertEqual(lib.make_pycurl_request('url', None), ('', None))

    def test_make_pycurl_req_timeout(self):
        curl_mock = mock.Mock()
        curl_mock.getinfo.return_value = 'url'
        with mock.patch('lib.pycurl.Curl', mock.Mock(return_value=curl_mock)):
            self.assertEqual(lib.make_pycurl_request('url', 7), ('', 'url'))
            curl_mock.setopt.assert_called_with(curl_mock.TIMEOUT, 7)

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
                self.assertEqual(lib.get_url(None, None, None), ('url', lib.REDIRECT_HTTP, None))

    def test_get_url_new_url_meta(self):
        with mock.patch('lib.make_pycurl_request',
                        mock.Mock(return_value=(None, None))):
            with mock.patch('lib.logger', mock.Mock()):
                with mock.patch('lib.check_for_meta', mock.Mock(return_value='url')):
                    self.assertEqual(lib.get_url(None, None, None), ('url', lib.REDIRECT_META, None))

    def test_get_url_meta_false(self):
        with mock.patch('lib.make_pycurl_request',
                        mock.Mock(return_value=(None, None))):
            with mock.patch('lib.logger', mock.Mock()):
                with mock.patch('lib.check_for_meta', mock.Mock(return_value=None)):
                    self.assertEqual(lib.get_url(None, None, None), (None, None, None))

    def test_get_url_market(self):
        def check(content, url):
            return url

        with mock.patch('lib.make_pycurl_request',
                        mock.Mock(return_value=(None, None))):
            with mock.patch('lib.logger', mock.Mock()):
                with mock.patch('lib.check_for_meta', mock.Mock(side_effect=check)):
                    self.assertEqual(lib.get_url('market://someurl.com/', None, None),
                                     ('http://play.google.com/store/apps/someurl.com/', lib.REDIRECT_META, None))

    def test_check_for_meta_len(self):
        html = '<meta content="" http-equiv="refresh">'
        self.assertEqual(lib.check_for_meta(html, 'http://localhost'), None)

    def test_check_for_meta_all(self):
        html = '<meta content=";url=test.php" http-equiv="refresh">'
        self.assertEqual(lib.check_for_meta(html, 'http://localhost/'), 'http://localhost/test.php')

    def test_check_for_meta_not_m(self):
        html = '<meta content=";" http-equiv="refresh">'
        self.assertEqual(lib.check_for_meta(html, 'http://localhost/'), None)

    def test_check_for_meta_none(self):
        html = '<>'
        self.assertEqual(lib.check_for_meta(html, 'http://localhost/'), None)

    def test_get_redirect_history_MM_url(self):
        self.assertEqual(lib.get_redirect_history('https://my.mail.ru/apps/', None), ([], [u'https://my.mail.ru/apps/'], []))

    def test_get_redirect_history_OK_url(self):
        self.assertEqual(lib.get_redirect_history(u'http://odnoklassniki.ru/', None),
                         ([], [u'http://odnoklassniki.ru/'], []))

    def test_get_redirect_history_not_redirect_url(self):
        with mock.patch('lib.get_url', mock.Mock(return_value=(None, None, None))):
            self.assertEqual(lib.get_redirect_history('url', None), ([], ['url'], []))

    def test_get_redirect_history_redirect_type_error(self):
        with mock.patch('lib.get_counters', mock.Mock(return_value=[])):
            with mock.patch('lib.get_url', mock.Mock(return_value=('url', 'ERROR', True))):
                self.assertEqual(lib.get_redirect_history('url', None), (['ERROR'], ['url', 'url'], []))

    def test_get_redirect_history(self):
        with mock.patch('lib.get_counters', mock.Mock(return_value=[])):
            with mock.patch('lib.get_url', mock.Mock(return_value=('url', None, None))):
                self.assertEqual(lib.get_redirect_history('url', None), ([None], ['url', 'url'], []))

    def test_get_redirect_history_with_content(self):
        with mock.patch('lib.get_counters', mock.Mock(return_value=['ga', 'ym'])):
            with mock.patch('lib.get_url', mock.Mock(return_value=('url', None, 'somecontent'))):
                self.assertEqual(lib.get_redirect_history('url', None), ([None], ['url', 'url'], ['ga', 'ym']))

    def test_get_redirect_history_with_some_iterations(self):  #
        with mock.patch('lib.get_url', mock.Mock(return_value=('new_url', 'type', None))):
            self.assertEqual(lib.get_redirect_history('url', None),
                             (['type', 'type'], ['url', 'new_url', 'new_url'], []))
