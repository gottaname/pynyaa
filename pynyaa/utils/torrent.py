
import hashlib
from collections import namedtuple
from datetime import datetime

import pytz

from . import bencode


File = namedtuple('File', ['path', 'size'])


class Torrent:

    def __init__(self, data, info_hash):
        self.data = data
        self.hash = info_hash
        self.info = data['info']
        self.encoding = data.get('encoding', b'UTF-8').decode('ascii')

        self.name = self.decode_string(self.info['name'])
        self.created_by = self.decode_string(self.data.get('created by'))
        self.creation_date = self.decode_string(self.data.get('creation date'))
        if self.creation_date:
            self.creation_date = datetime.fromtimestamp(self.creation_date, pytz.utc)
        self.comment = self.decode_string(self.data.get('comment'))

        self._length = None
        self._files = None
        self._trackers = None

    def decode_string(self, s):
        if isinstance(s, bytes):
            s = s.decode(self.encoding)
        return s

    @property
    def trackers(self):
        if self._trackers is None:
            trackers = set()
            if 'announce' in self.data:
                trackers.add(self.decode_string(self.data['announce']))
            if 'announce-list' in self.data:
                for sublist in self.data['announce-list']:
                    if isinstance(sublist, list):
                        for tr in sublist:
                            trackers.add(self.decode_string(tr))
                    else:
                        trackers.add(self.decode_string(sublist))
            self._trackers = sorted(trackers)
        return self._trackers

    @property
    def length(self):
        if self._length is None:
            self._length = 0
            for file in self.files:
                self._length += file.size
        return self._length

    @property
    def files(self):
        if self._files is None:
            self._files = []
            if 'files' in self.info:
                for file in self.info['files']:
                    self._files.append(File('/'.join(self.decode_string(p) for p in file['path']),
                                       int(file['length'])))
            else:
                self._files.append(File(self.decode_string(self.info['name']),
                                   self.info['length']))
        return self._files


def get_info(fp_or_filename):
    if hasattr(fp_or_filename, 'read'):
        torrent_bytes = bencode.bdecode(fp_or_filename.read())
    else:
        with open(fp_or_filename, 'rb') as f:
            torrent_bytes = bencode.bdecode(f.read())

    bencoded_info = bencode.bencode(torrent_bytes['info'])
    info_hash = hashlib.sha1(bencoded_info).hexdigest()
    del bencoded_info

    return Torrent(torrent_bytes, info_hash)
