import sys
from functools import partial
from bs4 import BeautifulSoup
from workflow import Workflow3, ICON_SYNC, web
from config import Config

reload(sys)
sys.setdefaultencoding('utf-8')

COOKIE_CACHE_KEY = 'atlassian-confluence-search-cookie-key'
COOKIE_CACHE_TIMEOUT = 30 * 24 * 60 * 60


def main(wf):
    config = Config()
    partial_get_cookie = partial(get_cookie, config)
    query = ' '.join(wf.args)
    resp = do_search(config, query, wf.cached_data(COOKIE_CACHE_KEY, partial_get_cookie, COOKIE_CACHE_TIMEOUT))
    # invalid session
    if auth_success(resp):
        wf.logger.debug('cached cookie is valid')
    else:
        wf.logger.debug('cached cookie is invalid')
        cookie = partial_get_cookie()
        wf.cache_data(COOKIE_CACHE_KEY, cookie)
        resp = do_search(config, query, cookie)
        if not auth_success(resp):
            wf.add_item(title='Authenticate failed', subtitle='Please check authentication information')
            wf.send_feedback()
            return
    parse_content(config, query, resp.content)


def auth_success(resp):
    return 'os_password' not in resp.content


def do_search(config, query, cookie):
    resp = web.get(config.search_url, headers={'Cookie': cookie}, params={
        'cql': 'siteSearch ~ "{query}" and type = "page"'.format(query=query),
        'queryString': query
    })
    resp.raise_for_status()
    return resp


def get_cookie(config):
    r = web.post(config.login_url, data=config.login_data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    r.raise_for_status()
    wf.logger.debug('login to fetch auth request object')
    return r.headers.get('set-cookie')


def parse_content(config, query, content):
    soup = BeautifulSoup(content, 'html.parser')
    res_ol = soup.select('ol[class="search-results cql"]')
    if len(res_ol) == 0:
        wf.add_item(title='No result found for {query}'.format(query=query))
        wf.send_feedback()
    else:
        for _ in res_ol[0].children:
            info = _.select('a[class="search-result-link visitable"]')[0]
            wf.add_item(title=info.text,
                        subtitle=_.select('div[class="search-result-meta"]')[0].text + ' - ' +
                                 _.select('div[class="highlights"]')[0].text,
                        arg=config.host + '/' + info['href'],
                        valid=True)
        wf.send_feedback()


if __name__ == '__main__':
    wf = Workflow3(help_url='https://github.com/Thare-Lam/alfred-atlassian-confluence-search',
                   update_settings={
                       'github_slug': 'Thare-Lam/alfred-atlassian-confluence-search',
                       'frequency': 1
                   })

    if wf.update_available:
        wf.add_item('New version available', 'Action this item to install the update',
                    autocomplete='workflow:update', icon=ICON_SYNC)

    sys.exit(wf.run(main))
