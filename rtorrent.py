import xmlrpclib
import shutil
import os.path
from rtorrent_xmlrpc import SCGIServerProxy

class Torrent(object):
    def __init__(self, server, ident):
        self._server = server
        self.ident   = ident

        self._get_info()

    def _get_info(self):
        mc = xmlrpclib.MultiCall(self._server)

        mc.d.complete(self.ident)
        mc.d.get_directory(self.ident)
        mc.d.base_filename(self.ident)
        mc.d.is_multi_file(self.ident)
        mc.d.get_base_filename(self.ident)

        self.completed, self.path, self.name, self.is_multi_file, self.filename = [value for value in mc()]

        if not self.is_multi_file:
            self.path = os.path.join(self.path, self.filename)

    def remove(self):
        self.close()
        self._server.d.erase(self.ident)

    def close(self):
        self._server.d.close(self.ident)

    def stop(self):
        self._server.d.stop(self.ident)

    def start(self):
        self._server.d.start(self.ident)

    def rehash(self):
        self._server.d.check_hash(self.ident)

    def get_directory(self):
        return self._server.d.get_directory(self.ident)

    def set_directory(self, path):
        self._server.d.set_directory(self.ident, path)

    def move(self, path):
        # close the torrent (and the files)
        self.close()

        # move the contents to the new destination
        shutil.move(self.path, path)

        # set the directory
        self.set_directory(path)

        # rehash the torrent
        self.rehash()

        # update the path reference
        self.path = self.get_directory()

        # start the torrent again
        self.start()

class Client(object):
    def __init__(self, xmlrpc_uri):
        self._server = SCGIServerProxy(xmlrpc_uri)

        self.default_path = self._server.directory.default()
        self.torrents = self._list_torrents()

    def load(self, torrent_file):
        self._server.load(torrent_file)

        self.torrents = self._list_torrents()

    def _list_torrents(self):
        downloads = self._server.download_list()

        return [
           Torrent(self._server, ident) for ident in downloads
        ]
