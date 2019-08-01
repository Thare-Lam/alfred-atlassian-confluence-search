import os
import json

AUTH_FILE = '.alfred_atlassian_confluence_search'


class Config:

    def __init__(self):
        self.host = None
        self.login_url = None
        self.search_url = None
        self.login_data = None
        self.success = False
        self.error_msg = None
        try:
            r = open(os.path.join(os.environ['HOME'], AUTH_FILE), 'r')
            cfg = json.load(r)
            self.host = cfg.get('host')
            self.login_url = self.host + '/dologin.action'
            self.search_url = self.host + '/dosearchsite.action'
            self.login_data = {
                'os_username': cfg.get('username'),
                'os_password': cfg.get('password')
            }
            self.success = True
        except IOError as e:
            self.error_msg = e