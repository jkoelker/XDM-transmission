# -*- coding: utf-8 -*-

# Author: Jason Kölker <jason@koelker.net>
# URL: https://github.com/jkoelker/XDM-transmission
#
# XDM-transmission: Transmisstion Downloader plugin for XDM.
# Copyright (C) 2013 Jason Kölker
#
# XDM-transmission is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# XDM-transmission is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.

from xdm import plugins

from .lib import shifter


class Transmission(plugins.Downloader):
    version = '0.2'
    identifier = 'net.koelker.jason.xdm.transmission'
    _config = {'port': 9091,
               'host': 'http://localhost',
               'username': '',
               'password': '',
               'download_path': '',
               'category_folders': True,
               }
    types = ['de.lad1337.torrent']

    def addDownload(self, download):
        client = self._client()
        cat = self._getCategory(download.element)

        kwargs = {}
        if self.c.download_path:
            path = self.c.download_path

            if self.c.category_folders and cat is not None:
                path = '%s/%s' % (path, cat)

            kwargs['download-dir'] = path

        try:
            r = client.torrent.add(filename=download.url, **kwargs)
        except:
            msg = ('Unable to connect to Transmission. Most likely a timout.'
                   'Is Transmission running?')
            plugins.log.error(msg)
            return False

        if not r:
            msg = ('Unable to add torrent to Transmission. Is it a dupe?')
            plugins.log.error(msg)
            return False

        plugins.log('Transmission ID: %s' % r['id'])
        plugins.log('Transmission Name: %s' % r['name'])
        plugins.log('Transmission Hash: %s' % r['hash_string'])
        plugins.log.info('Torrent added to Transmission')

        download.external_id = r['id']
        return True

    def getElementStaus(self, element):
        """Get the staus of element that it has in this downloader

        Arguments:
        element -- an Element object

        return:
        tuple of Status, Download and a path (str)
        >>>> (common.UNKNOWN, Download(), '')
        """
        download = plugins.Download()
        download.status = plugins.common.UNKNOWN
        if not hasattr(element, 'downloads'):
            return (plugins.common.UNKNOWN, download, '')

        return (plugins.common.UNKNOWN, plugins.Download(), '')

    def getDownloadPercentage(self, element):
        """"this should return a int betwen 0 and 100 as the percentage"""
        return 0

    def _client(self, username=None, password=None, host=None, port=0,
                **kwargs):
        # TODO(jkoelker) cache the client (possibly port to requests)
        url = self._url(host, port)

        if username is None:
            username = self.c.username

        if password is None:
            password = self.c.password

        return shifter.Client(address=url, username=username,
                              password=password, **kwargs)

    def _url(self, host=None, port=0):
        if not host:
            host = self.c.host

            if not host.startswith('http'):
                plugins.log('Fixing url. Adding http://')
                self.c.host = 'http://%s' % host

            host = self.c.host

        else:
            if not host.startswith('http'):
                host = 'http://%s' % host

        if not port:
            port = self.c.port

        return '%s:%s/transmission/rpc' % (host, port)

    def _test(self, host, port, username, password):
        url = self._url(host, port)
        try:
            client = self._client(username, password, host, port, timeout=10)
            response = client.session.get()

        except shifter.urllib2.socket.timeout:
            return (False, {},
                    'Connetion failure: Timeout. Check host and port.')

        except shifter.urllib2.URLError as e:
            msg = 'Connetion failure: %s. Check host and port.'
            return (False, {}, msg % e.reason)

        except shifter.TransmissionRPCError:
            msg = 'Connetion failure: %s. Check username and password.'
            return (False, {}, msg % e.message)

        plugins.log('Transmission test url %s' % url,
                    censor={self.c.password: 'password'})

        if response:
            return (True, {}, 'Connetion Established!')

        return (False, {}, 'Unknown response from Transmisstion')

    _test.args = ['host', 'port', 'username', 'password']

    config_meta = {
        'plugin_desc': 'Transmission downloader. Send torrents and '
                       'check for status',
        'plugin_buttons':  {'test_connection': {'action': _test,
                                                'name': 'Test connection'}},
        'host': {'on_live_change': _test},
        'port': {'on_live_change': _test},
        'username': {'on_live_change': _test},
        'password': {'on_live_change': _test},
    }
