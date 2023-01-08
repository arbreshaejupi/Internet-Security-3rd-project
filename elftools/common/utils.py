
from contextlib import contextmanager
from .exceptions import ELFParseError, ELFError, DWARFError
from ..construct import ConstructError, ULInt8
import os


def merge_dicts(*dicts):
    "Given any number of dicts, merges them into a new one."""
    result = {}
    for d in dicts:
        result.update(d)
    return result

def bytes2str(b):
    """Decode a bytes object into a string."""
    return b.decode('latin-1')

def bytelist2string(bytelist):
    """ Convert a list of byte values (e.g. [0x10 0x20 0x00]) to a bytes object
        (e.g. b'\x10\x20\x00').
    """
    return b''.join(bytes((b,)) for b in bytelist)


def struct_parse(struct, stream, stream_pos=None):
    
    try:
        if stream_pos is not None:
            stream.seek(stream_pos)
        return struct.parse_stream(stream)
    except ConstructError as e:
        raise ELFParseError(str(e))


def parse_cstring_from_stream(stream, stream_pos=None):
 
    if stream_pos is not None:
        stream.seek(stream_pos)
    CHUNKSIZE = 64
    chunks = []
    found = False
    while True:
        chunk = stream.read(CHUNKSIZE)
        end_index = chunk.find(b'\x00')
        if end_index >= 0:
            chunks.append(chunk[:end_index])
            found = True
            break
        else:
            chunks.append(chunk)
        if len(chunk) < CHUNKSIZE:
            break
    return b''.join(chunks) if found else None


def elf_assert(cond, msg=''):
    """ Assert that cond is True, otherwise raise ELFError(msg)
    """
    _assert_with_exception(cond, msg, ELFError)


def dwarf_assert(cond, msg=''):
    """ Assert that cond is True, otherwise raise DWARFError(msg)
    """
    _assert_with_exception(cond, msg, DWARFError)


@contextmanager
def preserve_stream_pos(stream):
   
    saved_pos = stream.tell()
    yield
    stream.seek(saved_pos)


def roundup(num, bits):
    """ Round up a number to nearest multiple of 2^bits. The result is a number
        where the least significant bits passed in bits are 0.
    """
    return (num - 1 | (1 << bits) - 1) + 1

def read_blob(stream, length):
    """Read length bytes from stream, return a list of ints
    """
    return [struct_parse(ULInt8(''), stream) for i in range(length)]

def save_dwarf_section(section, filename):
    """Debug helper: dump section contents into a file
    Section is expected to be one of the debug_xxx_sec elements of DWARFInfo
    """
    stream = section.stream
    pos = stream.tell()
    stream.seek(0, os.SEEK_SET)
    section.stream.seek(0)
    with open(filename, 'wb') as file:
        data = stream.read(section.size)
        file.write(data)
    stream.seek(pos, os.SEEK_SET)

def iterbytes(b):
    """Return an iterator over the elements of a bytes object.

    For example, for b'abc' yields b'a', b'b' and then b'c'.
    """
    for i in range(len(b)):
        yield b[i:i+1]

def bytes2hex(b, sep=''):
    if not sep:
        return b.hex()
    return sep.join(map('{:02x}'.format, b))

#------------------------- PRIVATE -------------------------

def _assert_with_exception(cond, msg, exception_type):
    if not cond:
        raise exception_type(msg)
