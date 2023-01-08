from __future__ import print_function
import sys

# If pyelftools is not installed, the example can also run from the root or
# examples/ dir of the source distribution.
sys.path[0:0] = ['.', '..']

from elftools.elf.elffile import ELFFile
from elftools.dwarf.descriptions import (
    describe_DWARF_expr, set_global_machine_arch)
from elftools.dwarf.locationlists import (
    LocationEntry, LocationExpr, LocationParser)

def process_file(filename):
    print('Processing file:', filename)
    with open(filename, 'rb') as f:
        elffile = ELFFile(f)

        if not elffile.has_dwarf_info():
            print('  file has no DWARF info')
            return

        # get_dwarf_info returns a DWARFInfo context object, which is the
        # starting point for all DWARF-based processing in pyelftools.
        dwarfinfo = elffile.get_dwarf_info()

        # The location lists are extracted by DWARFInfo from the .debug_loc
        # section, and returned here as a LocationLists object.
        location_lists = dwarfinfo.location_lists()

        # This is required for the descriptions module to correctly decode
        # register names contained in DWARF expressions.
        set_global_machine_arch(elffile.get_machine_arch())

        # Create a LocationParser object that parses the DIE attributes and
        # creates objects representing the actual location information.
        loc_parser = LocationParser(location_lists)

        for CU in dwarfinfo.iter_CUs():
            # DWARFInfo allows to iterate over the compile units contained in
            # the .debug_info section. CU is a CompileUnit object, with some
            # computed attributes (such as its offset in the section) and
            # a header which conforms to the DWARF standard. The access to
            # header elements is, as usual, via item-lookup.
            print('  Found a compile unit at offset %s, length %s' % (
                CU.cu_offset, CU['unit_length']))

            # A CU provides a simple API to iterate over all the DIEs in it.
            for DIE in CU.iter_DIEs():
                # Go over all attributes of the DIE. Each attribute is an
                # AttributeValue object (from elftools.dwarf.die), which we
                # can examine.
                for attr in DIE.attributes.values():
                    # Check if this attribute contains location information
                    if loc_parser.attribute_has_location(attr, CU['version']):
                        print('   DIE %s. attr %s.' % (DIE.tag, attr.name))
                        loc = loc_parser.parse_from_attribute(attr,
                                                              CU['version'])
                        # We either get a list (in case the attribute is a
                        # reference to the .debug_loc section) or a LocationExpr
                        # object (in case the attribute itself contains location
                        # information).
                        if isinstance(loc, LocationExpr):
                            print('      %s' % (
                                describe_DWARF_expr(loc.loc_expr,
                                                    dwarfinfo.structs, CU.cu_offset)))
                        elif isinstance(loc, list):
                            print(show_loclist(loc,
                                               dwarfinfo,
                                               '      ', CU.cu_offset))

def show_loclist(loclist, dwarfinfo, indent, cu_offset):
    """ Display a location list nicely, decoding the DWARF expressions
        contained within.
    """
    d = []
    for loc_entity in loclist:
        if isinstance(loc_entity, LocationEntry):
            d.append('%s <<%s>>' % (
                loc_entity,
                describe_DWARF_expr(loc_entity.loc_expr, dwarfinfo.structs, cu_offset)))
        else:
            d.append(str(loc_entity))
    return '\n'.join(indent + s for s in d)

if __name__ == '__main__':
    if sys.argv[1] == '--test':
        for filename in sys.argv[2:]:
            process_file(filename)
