# coding: utf-8
from StringIO import StringIO
from logging import getLogger, NullHandler
import re
from urllib import quote, quote_plus
from urlparse import urljoin, urlsplit, urlparse, urlunparse

from bs4 import BeautifulSoup
import pycurl

logger = getLogger('redirect_checker')
logger.addHandler(NullHandler())

REDIRECT_META = 'meta_tag'
REDIRECT_HTTP = 'http_status'

OK_REDIRECT = re.compile(r'http://(www\.)?odnoklassniki\.ru/.*st\.redirect', re.I)
OK_URL = re.compile(r'http(?:s)?://(www\.)?odnoklassniki\.ru/', re.I)
MM_URL = re.compile(r'http(?:s)?://my\.mail\.ru/apps/', re.I)

COUNTER_TYPES = (
    ('GOOGLE_ANALYTICS', re.compile(r'.*google-analytics\.com/ga\.js.*', re.I+re.S)),
    ('YA_METRICA', re.compile(r'.*mc\.yandex\.ru/metrika/watch\.js.*', re.I+re.S)),
    ('TOP_MAIL_RU', re.compile(r'.*top-fwz1\.mail\.ru/counter.*', re.I+re.S)),
    ('TOP_MAIL_RU', re.compile(r'.*top\.mail\.ru/jump\?from.*', re.I+re.S)),
    ('DOUBLECLICK', re.compile(r'.*//googleads\.g\.doubleclick\.net/pagead/viewthroughconversion.*', re.I+re.S)),
    ('VISUALDNA', re.compile(r'.*//a1\.vdna-assets\.com/analytics\.js.*', re.I+re.S)),
    ('LI_RU', re.compile(r'.*/counter\.yadro\.ru/hit.*', re.I+re.S)),
    ('RAMBLER_TOP100', re.compile(r'.*counter\.rambler\.ru/top100.*', re.I+re.S))
)


def to_unicode(val, errors='strict'):
    return val if isinstance(val, unicode) else val.decode('utf8', errors=errors)


def to_str(val, errors='strict'):
    return val.encode('utf8', errors=errors) if isinstance(val, unicode) else val


def get_counters(content):
    """
    Ищет в хтмл-странице счетичик и возвращает массив типов найденных
    """
    counters = []
    for counter_name, regexp in COUNTER_TYPES:
        if re.match(regexp, content):
            counters.append(counter_name)
    return counters


def check_for_meta(content, url):
    """
    Ищет в хтмл-странице мета-редирект теги и возраещет урл редиректа
    """
    soup = BeautifulSoup(content, "html.parser")
    result = soup.find("meta")
    if result and 'content' in result.attrs:
        for attr, value in result.attrs.items():
            if attr == 'http-equiv' and value.lower() == 'refresh':
                splitted = result['content'].split(";")
                if len(splitted) != 2:
                    return
                wait, text = splitted
                text = text.strip()
                m = re.search(r"url\s*=\s*['\"]?([^'\"]+)", text, re.I)
                if m:
                    meta_url = m.groups()[0]
                    return urljoin(url, to_unicode(meta_url, 'ignore'))


def fix_market_url(url):
    """Преобразует market:// урлы в http://"""
    return 'http://play.google.com/store/apps/' + url.lstrip("market://")


def make_pycurl_request(url, timeout, useragent=None):
    """Делает http запрос (без перехода по редиректам)
    Возвращает контент ответа и возможный редирект
    :return: содержимое ответа, урл редиректа

    """
    prepared_url = to_str(prepare_url(url), 'ignore')
    buff = StringIO()
    curl = pycurl.Curl()
    curl.setopt(curl.URL, prepared_url)
    if useragent:
        curl.setopt(curl.USERAGENT, useragent)
    curl.setopt(curl.WRITEDATA, buff)
    curl.setopt(curl.FOLLOWLOCATION, False)
    # curl.setopt(curl.CONNECTTIMEOUT, timeout)
    curl.setopt(curl.TIMEOUT, timeout)
    curl.perform()
    content = buff.getvalue()
    redirect_url = curl.getinfo(curl.REDIRECT_URL)
    curl.close()
    if redirect_url is not None:
        redirect_url = to_unicode(redirect_url, 'ignore')
    return content, redirect_url


def get_url(url, timeout, user_agent=None):
    """
    :return: урл, тип редиректа, содержимое страницы (если есть)
    """
    content = None
    try:
        content, new_redirect_url = make_pycurl_request(url, timeout, user_agent)
    except (pycurl.error, ValueError) as e:
        logger.error(u'error in url {} {}'.format(url, e))
        return url, 'ERROR', content  # TODO add exception in ERROR

    redirect_type = None

    # ignoring ok login redirects
    if new_redirect_url and OK_REDIRECT.match(new_redirect_url):
        return None, redirect_type, content

    if new_redirect_url:
        redirect_type = REDIRECT_HTTP
    else:
        new_redirect_url = check_for_meta(content, url)
        if new_redirect_url:
            redirect_type = REDIRECT_META

    if new_redirect_url and urlsplit(new_redirect_url).scheme == 'market':
        new_redirect_url = fix_market_url(new_redirect_url)

    return prepare_url(new_redirect_url), redirect_type, content


def get_redirect_history(url, timeout, max_redirects=30, user_agent=None):
    """
    Входные параметры:

    + url - урл для которого необходимо получить редиректы
    + timeout - таймаут на проверку *одного* урла
    + max_redirects - максимальное количество редиректов, после превышения проверка останавливается
    + user_agent - юзер-агент, если не передает, то будет дефолтный из pycurl


    Выходные параметры:
    Массив из трех элементов

    1. типы найденных редиректов (варианты: meta_tag, http_status, ERROR)
    2. урлы редиректов (включая конечный)
    3. установленные счетчики на конечном урле

    """
    url = prepare_url(url)
    history_types = []
    history_urls = [url]
    redirect_url = url

    # ignore mm / ok domains
    if re.match(MM_URL, url) or re.match(OK_URL, url):
        return history_types, history_urls, []

    content = None
    while True:
        redirect_url, redirect_type, content = get_url(
            url=redirect_url,
            timeout=timeout,
            user_agent=user_agent
        )
        if not redirect_url:
            break

        history_types.append(redirect_type)
        history_urls.append(redirect_url)

        if redirect_type == 'ERROR':
            break

        if len(history_urls) > max_redirects or (redirect_url in history_urls[:-1]):
            break

    counters = get_counters(content) if content else []

    return history_types, history_urls, counters


def prepare_url(url):
    """Нормализация урла"""
    if url is None:
        return url
    scheme, netloc, path, qs, anchor, fragments = urlparse(
        to_unicode(url),
        allow_fragments=False
    )
    try:
        netloc = netloc.encode('idna')
    except UnicodeError:
        pass
    path = quote(to_str(path, 'ignore'), safe='/%+$!*\'(),')
    qs = quote_plus(to_str(qs, 'ignore'), safe=':&%=+$!*\'(),')
    return urlunparse((scheme, netloc, path, qs, anchor, fragments))
