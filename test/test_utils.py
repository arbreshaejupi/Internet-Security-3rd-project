
import unittest
from io import BytesIO
from random import randint

from elftools.common.utils import (parse_cstring_from_stream, merge_dicts,
        preserve_stream_pos)


class Test_parse_cstring_from_stream(unittest.TestCase):
    def _make_random_bytes(self, n):
        return b''.join(bytes((randint(32, 127),)) for i in range(n))

    def test_small1(self):
        sio = BytesIO(b'abcdefgh\x0012345')
        self.assertEqual(parse_cstring_from_stream(sio), b'abcdefgh')
        self.assertEqual(parse_cstring_from_stream(sio, 2), b'cdefgh')
        self.assertEqual(parse_cstring_from_stream(sio, 8), b'')

    def test_small2(self):
        sio = BytesIO(b'12345\x006789\x00abcdefg\x00iii')
        self.assertEqual(parse_cstring_from_stream(sio), b'12345')
        self.assertEqual(parse_cstring_from_stream(sio, 5), b'')
        self.assertEqual(parse_cstring_from_stream(sio, 6), b'6789')

    def test_large1(self):
        text = b'i' * 400 + b'\x00' + b'bb'
        sio = BytesIO(text)
        self.assertEqual(parse_cstring_from_stream(sio), b'i' * 400)
        self.assertEqual(parse_cstring_from_stream(sio, 150), b'i' * 250)

    def test_large2(self):
        text = self._make_random_bytes(5000) + b'\x00' + b'jujajaja'
        sio = BytesIO(text)
        self.assertEqual(parse_cstring_from_stream(sio), text[:5000])
        self.assertEqual(parse_cstring_from_stream(sio, 2348), text[2348:5000])


class Test_preserve_stream_pos(unittest.TestCase):
    def test_basic(self):
        sio = BytesIO(b'abcdef')
        with preserve_stream_pos(sio):
            sio.seek(4)
        self.assertEqual(sio.tell(), 0)

        sio.seek(5)
        with preserve_stream_pos(sio):
            sio.seek(0)
        self.assertEqual(sio.tell(), 5)


class Test_merge_dicts(unittest.TestCase):
    def test_basic(self):
        md = merge_dicts({10: 20, 20: 30}, {30: 40, 50: 60})
        self.assertEqual(md, {10: 20, 20: 30, 30: 40, 50: 60})

    def test_keys_resolve(self):
        md = merge_dicts({10: 20, 20: 30}, {20: 40, 50: 60})
        self.assertEqual(md, {10: 20, 20: 40, 50: 60})


if __name__ == '__main__':
    unittest.main()
