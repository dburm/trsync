#-*- coding: utf-8 -*-

import re
import utils


logger = utils.logger.getChild('RsyncUrl')


class RsyncUrl(object):

    def __init__(self, remote_url):

        self._url = remote_url
        self._url_type = False

        self.regexps = {
            # ssh: [USER@]HOST:SRC
            'ssh': re.compile(
                r'^'
                r'(?P<user>[-\w]+@)?'
                r'(?P<host>[-\.\w]+){1}'
                r':'
                r'(?P<path>(~{0,1}[\w/-]*)){1}'
                r'$'
            ),
            # rsync: [USER@]HOST::SRC
            'rsync1': re.compile(
                r'^'
                r'(?P<user>[-\w]+@)?'
                r'(?P<host>[-\.\w]+){1}'
                r'::'
                r'(?P<module>[\w-]+){1}'
                r'(?P<path>[\w/-]*)?'
                r'$'
            ),
            # rsync://[USER@]HOST[:PORT]/SRC
            'rsync2': re.compile(
                r'^rsync://'
                r'(?P<user>[-\w]+@)?'
                r'(?P<host>[-\.\w]+){1}'
                r'(?P<port>:[\d]+)?'
                r'(?P<module>/[\w-]*)?'
                r'(?P<path>[\w/-]*)?'
                r'$'
            ),
            # local/path/to/directory
            'path': re.compile(
                r'^'
                r'(?P<path>(~{0,1}[\w/-]+)){1}'
                r'$'
            ),
        }

        self._match = self._get_matching_regexp()
        if self.match is None:
            self.user, self.host, self.module, self.port, self.path = \
                None, None, None, None, None
        else:
            self._parse_rsync_url(self.match)

    def _get_matching_regexp(self):
        regexps = self._get_all_matching_regexps()
        regexps_len = len(regexps)
        #if regexps_len > 1:
        #    raise Exception('Rsync location {} matches with {} regexps {}'
        #                    ''.format(self.url, len(regexps), str(regexps)))
            # TODO: Possible may be better remove this raise and keep
            # only warning with request to fail bug. rsync will parse this
            # remote later
        if regexps_len != 1:
            logger.warn('Rsync location "{}" matches with {} regexps: {}.'
                        'Please fail a bug on {} if it is wrong.'
                        ''.format(self.url, len(regexps), str(regexps), '...'))
        if regexps_len == 0:
            self._url_type = None
            return None
        else:
            return regexps[0]

    def _get_all_matching_regexps(self):
        regexps = list()
        for url_type, regexp in self.regexps.items():
            match = regexp.match(self.url)
            if match is not None:
                if self.url_type is False:
                    self._url_type = url_type
                regexps.append(regexp)
        return regexps

    def _parse_rsync_url(self, regexp):
        # parse remote url

        for match in re.finditer(regexp, self._url):

            self.path = match.group('path')
            if self.path is None:
                self.path = ''

            try:
                self.host = match.group('host')
            except IndexError:
                self.host = None

            try:
                self.user = match.group('user')
            except IndexError:
                self.user = None
            else:
                if self.user is not None:
                    self.user = self.user.strip('@')

            try:
                self.port = match.group('port')
            except IndexError:
                self.port = None
            else:
                if self.port is not None:
                    self.port = int(self.port.strip(':'))

            try:
                self.module = match.group('module')
            except IndexError:
                self.module = None
            else:
                if self.module is not None:
                    self.module = self.module.strip('/')
                if not self.module:
                    self.module = None

    @property
    def match(self):
        return self._match

    @property
    def url_type(self):
        return self._url_type

    @property
    def is_valid(self):
        if self.match is None:
            return False
        if self.path in (None, False):
            return False
        if self.url_type != 'path':
            if self.host in ('', None, False):
                return False
        if self.url_type.startswith('rsync'):
            if self.module is None:
                return False
        return True

    @property
    def url(self):
        return self._url
