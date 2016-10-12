#
# MacRF - Access to Mac OSX resource forks
import os
from collections import defaultdict, namedtuple
from contextlib import closing
import mmap
from operator import attrgetter
from struct import unpack

class Thing:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class ResourceFork:
    # OTTA: Make it a context manager
    def __init__(self, filename, inData=False):
        self.filename = filename
        if inData:
            name = filename
        else:
            name = os.path.join(filename, '..namedfork/rsrc')
        f = self.f = open(name, 'rb') # OTTA: writing to resource forks        
        mm = self.mappedRF = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
        self.o_data, self.o_map, self.l_data, self.l_map = unpack('>IIII', mm[:16])
        # OTTA: consistency checks
        self.app_data = memoryview(mm[128:256])
        
        rdata = self.resource_data = memoryview(mm[self.o_data:self.o_data+self.l_data])
        rmap = self.resource_map = memoryview(mm[self.o_map:self.o_map+self.l_map])

        resources = self.resources = set()
        rlft = self.resource_list_from_type = {}

        """
        # Collect the Resources
        Resource = namedtuple('Resource', ['offset', 'data'])
        resources = self.resources = []
        rix = 0
        while rix < len(rdata):
            l_res = unpack('>L', rdata[rix:rix+4])[0]
            resource = Resource(rix, rdata[rix+4:rix+4+l_res])
            resources.append(resource)
            rix += 4 + l_res
        """

        # Parse the resource map
        self.file_reference_number = unpack('>H', rmap[20:22])[0]
        self.resource_file_attributes = unpack('2s', rmap[22:24])[0]
        o_tl = self.o_type_list = unpack('>H', rmap[24:26])[0]
        o_nl = self.o_name_list = unpack('>H', rmap[26:28])[0]
        type_list_v = self.resource_map[o_tl:o_nl]
        name_list_v = self.resource_map[o_nl:]

        Resource = namedtuple('Resource', ['type', 'id', 'name', 'data'])

        # Type list
        # "2 bytes Number of resource types in the map minus 1"
        # Watch out for zero resources!
        n_types = self.n_types = (unpack('>H', type_list_v[:2])[0] + 1) & 0xffff
        for i in range(n_types):
            resource_type, p, offset = unpack('>4sHH', type_list_v[2+8*i:2+8*(i+1)])
            qty = p + 1
            assert resource_type not in rlft, \
                "duplicate resource type %s" % resource_type
            #rl = []
            #rd = {}
            #resources[resource_type] = Thing(resource_list = rl, by_name = rd)
            #resources[resource_type] = rd
            # Parse reference list for all the resources of this type
            rl = rlft[resource_type] = []
            for j in range(qty):
                rid, o_name, attrs, tmsb, t = unpack('>HHBBH', type_list_v[offset+12*j:offset+12*j+8])
                o_rdat = (tmsb<<16) + t
                l_rdat = unpack('>L', rdata[o_rdat:o_rdat+4])[0]
                rdat = rdata[o_rdat+4:o_rdat+4+l_rdat]
                # Get resource name if extant
                if o_name == 0xffff:
                    name = b''
                else:
                    name_len = name_list_v[o_name]
                    name = name_list_v[o_name+1:o_name+1+name_len].tobytes()
                res = Resource(resource_type, rid, name, rdat)
                #assert res not in resources, \
                #    "Duplicate resource %r" % res
                #resources.add(res)
                rl.append(res)
        #return self


    def getResources(self, theType):
        return self.resource_list_from_type[theType]

    def getTypes(self):
        return sorted(self.resource_list_from_type.keys())

    def getResource(self, theType, theID):
        try:
            for r in self.getResources(theType):
                assert r.type == theType
                if r.id == theID:
                    return r
            return None
        except KeyError:
            return None

    def getNamedResource(self, theType, name):
        try:
            for r in self.getResources(theType):
                assert r.type == theType
                if r.name == name:
                    return r
            return None
        except KeyError:
            return None

    def close(self):
        self.mappedRF.close()
        self.f.close()

    def rfck(self):
        # Consistency check
        """
        roffs = [r.offset for r in self.resources]
        assert all(t.offset in roffs for t in self.types), \
            "Resource type with bad offset"
        assert sum(t.n for t in self.types) == len(self.resources), \
            "Not the expected number of resources"
        """
        l_tl = self.o_name_list - self.o_type_list

def main():
    import argparse
    from pprint import pprint
    import sys

    parser = argparse.ArgumentParser(description='Mac Resource Fork reading')
    parser.add_argument('-d', '--indata', action='store_true',
                        help='Treat the data fork as the resource fork')
    parser.add_argument('filename')
    args = parser.parse_args()
    pprint(args)

    with closing(ResourceFork(args.filename, args.indata)) as rf:
        rf = ResourceFork(args.filename, args.indata)
        pprint(rf.__dict__)

    
if __name__ == '__main__':
    main()
