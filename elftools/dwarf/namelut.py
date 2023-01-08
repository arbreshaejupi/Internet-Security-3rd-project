
import os
import collections
from collections import OrderedDict
from collections.abc import Mapping
from ..common.utils import struct_parse
from bisect import bisect_right
import math
from ..construct import CString, Struct, If

NameLUTEntry = collections.namedtuple('NameLUTEntry', 'cu_ofs die_ofs')

class NameLUT(Mapping):
   

    def __init__(self, stream, size, structs):

        self._stream = stream
        self._size = size
        self._structs = structs
        # entries are lazily loaded on demand.
        self._entries = None
        # CU headers (for readelf).
        self._cu_headers = None

    def get_entries(self):
        """
        Returns the parsed NameLUT entries. The returned object is a dictionary
        with the symbol name as the key and NameLUTEntry(cu_ofs, die_ofs) as
        the value.

        This is useful when dealing with very large ELF files with millions of
        entries. The returned entries can be pickled to a file and restored by
        calling set_entries on subsequent loads.
        """
        if self._entries is None:
            self._entries, self._cu_headers = self._get_entries()
        return self._entries

    def set_entries(self, entries, cu_headers):
        """
        Set the NameLUT entries from an external source. The input is a
        dictionary with the symbol name as the key and NameLUTEntry(cu_ofs,
        die_ofs) as the value.

        This option is useful when dealing with very large ELF files with
        millions of entries. The entries can be parsed once and pickled to a
        file and can be restored via this function on subsequent loads.
        """
        self._entries = entries
        self._cu_headers = cu_headers

    def __len__(self):
        """
        Returns the number of entries in the NameLUT.
        """
        if self._entries is None:
            self._entries, self._cu_headers = self._get_entries()
        return len(self._entries)

    def __getitem__(self, name):
        """
        Returns a namedtuple - NameLUTEntry(cu_ofs, die_ofs) - that corresponds
        to the given symbol name.
        """
        if self._entries is None:
            self._entries, self._cu_headers = self._get_entries()
        return self._entries.get(name)

    def __iter__(self):
        """
        Returns an iterator to the NameLUT dictionary.
        """
        if self._entries is None:
            self._entries, self._cu_headers = self._get_entries()
        return iter(self._entries)

    def items(self):
        """
        Returns the NameLUT dictionary items.
        """
        if self._entries is None:
            self._entries, self._cu_headers = self._get_entries()
        return self._entries.items()

    def get(self, name, default=None):
        """
        Returns NameLUTEntry(cu_ofs, die_ofs) for the provided symbol name or
        None if the symbol does not exist in the corresponding section.
        """
        if self._entries is None:
            self._entries, self._cu_headers = self._get_entries()
        return self._entries.get(name, default)

    def get_cu_headers(self):
        """
        Returns all CU headers. Mainly required for readelf.
        """
        if self._cu_headers is None:
            self._entries, self._cu_headers = self._get_entries()

        return self._cu_headers

    def _get_entries(self):
        """
        Parse the (name, cu_ofs, die_ofs) information from this section and
        store as a dictionary.
        """

        self._stream.seek(0)
        entries = OrderedDict()
        cu_headers = []
        offset = 0
        # According to 6.1.1. of DWARFv4, each set of names is terminated by
        # an offset field containing zero (and no following string). Because
        # of sequential parsing, every next entry may be that terminator.
        # So, field "name" is conditional.
        entry_struct = Struct("Dwarf_offset_name_pair",
                self._structs.Dwarf_offset('die_ofs'),
                If(lambda ctx: ctx['die_ofs'], CString('name')))

        # each run of this loop will fetch one CU worth of entries.
        while offset < self._size:

            # read the header for this CU.
            namelut_hdr = struct_parse(self._structs.Dwarf_nameLUT_header,
                    self._stream, offset)
            cu_headers.append(namelut_hdr)
            # compute the next offset.
            offset = (offset + namelut_hdr.unit_length +
                     self._structs.initial_length_field_size())

            # before inner loop, latch data that will be used in the inner
            # loop to avoid attribute access and other computation.
            hdr_cu_ofs = namelut_hdr.debug_info_offset

            # while die_ofs of the entry is non-zero (which indicates the end) ...
            while True:
                entry = struct_parse(entry_struct, self._stream)

                # if it is zero, this is the terminating record.
                if entry.die_ofs == 0:
                    break
                # add this entry to the look-up dictionary.
                entries[entry.name.decode('utf-8')] = NameLUTEntry(
                        cu_ofs = hdr_cu_ofs,
                        die_ofs = hdr_cu_ofs + entry.die_ofs)

        # return the entries parsed so far.
        return (entries, cu_headers)
