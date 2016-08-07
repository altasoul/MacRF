#
# MacRF - Access to Mac OSX resource forks
import os
from collections import namedtuple
import mmap
from struct import unpack

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

        # Parse the resource map
        self.file_reference_number = unpack('>H', rmap[20:22])[0]
        self.resource_file_attributes = unpack('2s', rmap[22:24])[0]
        o_tl = self.o_type_list = unpack('>H', rmap[24:26])[0]
        o_nl = self.o_name_list = unpack('>H', rmap[26:28])[0]

        n = self.n_types = unpack('>H', rmap[o_tl:o_tl+2])[0] + 1
        #type_list_v = memoryview(self.resource_map[o_tl:o_tl+2+8*n])
        type_list_v = memoryview(self.resource_map[o_tl:o_nl])
        name_list_v = memoryview(self.resource_map[o_nl:])
        Type = namedtuple('Type', ['code', 'n', 'id', 'attrs', 'name', 'data'])
        types = []
        for i in range(n):
            code, p, offset = unpack('>4sHH', type_list_v[2+8*i:2+8*(i+1)])
            rid, o_name, attrs, tmsb, t = unpack('>HHBBH', type_list_v[offset:offset+8])
            o_rdat = tmsb<<16 + t
            l_rdat = unpack('>L', rdata[o_rdat:o_rdat+4])[0]
            rdat = rdata[o_rdat+4:o_rdat+4+l_rdat]
            if o_name == 0xffff:
                name = b''
            else:
                name_len = name_list_v[o_name]
                name = name_list_v[o_name+1:o_name+1+name_len].tobytes()
            types.append(Type(code, p + 1, rid, attrs, name, rdat))
        self.types = types
        return self

    def close(self):
        self.mappedRF.close()
        self.f.close()


def main():
    import pdb
    from pprint import pprint
    name = '/Users/soul/Projects/Nova-decode/various/One outfit'
    rf = ResourceFork()
    f = rf.open(name)
    pprint(f.__dict__)
    pdb.set_trace()
    f.close()
    
if __name__ == '__main__':
    main()
