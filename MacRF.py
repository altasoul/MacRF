#
# MacRF - Access to Mac OSX resource forks
import pdb
import os
from collections import defaultdict, namedtuple
import mmap
from operator import attrgetter
from struct import unpack

class Thing:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class ResourceFork:
    # OTTA: Make it a context manager
    def __init__(self):
        pass

    def open(self, filename):
        self.filename = filename
        name = os.path.join(filename, '..namedfork/rsrc')
        f = self.f = open(name, 'rb') # OTTA: writing to resource forks        
        mm = self.mappedRF = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
        self.o_data, self.o_map, self.l_data, self.l_map = unpack('>IIII', mm[:16])
        # OTTA: consistency checks
        self.app_data = memoryview(mm[128:256])
        
        rdata = self.resource_data = memoryview(mm[self.o_data:self.o_data+self.l_data])
        rmap = self.resource_map = memoryview(mm[self.o_map:self.o_map+self.l_map])

        resources = self.resources = set()
        

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
        n_types = self.n_types = unpack('>H', type_list_v[:2])[0] + 1
        for i in range(n_types):
            resource_type, p, offset = unpack('>4sHH', type_list_v[2+8*i:2+8*(i+1)])
            qty = p + 1
            assert resource_type not in resources, \
                "duplicate resource type %s" % resource_type
            #rl = []
            #rd = {}
            #resources[resource_type] = Thing(resource_list = rl, by_name = rd)
            #resources[resource_type] = rd
            # Parse reference list for all the resources of this type
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
                assert res not in resources, \
                    "Duplicate resource %r" % res
                resources.add(res)
                #assert name not in rd, \
                #    "Multiple resources of type %d and name %d" % (resource_type, name)
                #rd[name] = rdat
        
        return self

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
        pdb.set_trace()

def main():
    import pdb
    from pprint import pprint
    import sys
    try:
        name = sys.argv[1]
    except IndexError:
        name =  '/Users/soul/Projects/Nova-decode/various/One outfit'
    rf = ResourceFork()
    f = rf.open(name)
    pprint(f.__dict__)

    pdb.set_trace()
    dls = sum(t.n*len(t.data) for t in f.types)
    n = sum(t.n for t in f.types)
    print(f.l_data, dls, f.l_data-dls, n, (f.l_data-dls)/n)

    for i in range(len(f.types)-1):
        this_addr = v_addr(f.types[i].data)
        next_addr = v_addr(f.types[i+1].data)
        t = f.types[i]
        print(t.code, t.n, t.offset, t.data, len(t.data), next_addr-this_addr)

    pdb.set_trace()
    f.close()
    
if __name__ == '__main__':
    main()
