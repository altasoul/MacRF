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
        mm = self.mm = mmap.mmap(f.fileno(), 0, prot=mmap.PROT_READ)
        self.o_data, self.o_map, self.l_data, self.l_map = unpack('>IIII', mm[:16])
        # OTTA: consistency checks
        self.app_data = memoryview(mm[128:256])
        
        d = self.resource_data = memoryview(mm[self.o_data:self.o_data+self.l_data])
        m = self.resource_map = memoryview(mm[self.o_map:self.o_map+self.l_map])

        self.file_reference_number = unpack('>H', m[20:22])[0]
        self.resource_file_attributes = unpack('2s', m[22:24])
        o_tl = self.o_type_list = unpack('>H', m[24:26])[0]
        o_nl = self.o_name_list = unpack('>H', m[26:28])[0]

        n = self.n_types = unpack('>H', m[o_tl:o_tl+2])[0]+1
        tv = memoryview(self.resource_map[o_tl+2:o_tl+2+8*n])
        Type = namedtuple('Type', ['name', 'n', 'offset'])
        #Wish this worked:
        #tv.cast('B', shape=[n, 8])
        #types = [Type(unpack('>4sHH', tv[i])) for i in range(n)]
        types = []
        for i in range(n):
            code, p, offset = unpack('>4sHH', tv[8*i:8*(i+1)])
            types.append(Type(code, p+1, offset))




        import pdb
        pdb.set_trace()



        f.seek(self.o_map)
        m = self.resource_map = f.read(self.l_map)
        self.file_reference_number = unpack('>H', m[20:22])[0]
        self.resource_file_attributes = m[22:24]
        o_tl = self.o_type_list = unpack('>H', m[24:26])[0]
        o_nl = self.o_name_list = unpack('>H', m[26:28])[0]
        n = self.n_types = unpack('>H', m[28:30])[0]+1



        tv = memoryview(self.resource_map[30:30+8*n])
        tv.cast('B', shape=[n, 8])
        Type = namedtuple('Type', ['name', 'n', 'offset'])
        types = [Type(unpack('>4sHH', tv[i])) for i in range(n)]
        return self

    def close(self):
        self.f.close()


def main():
    import pdb
    name = '/Users/soul/Projects/Nova-decode/various/One outfit'
    rf = ResourceFork()
    f = rf.open(name)
    pdb.set_trace()
    f.close()
    
if __name__ == '__main__':
    main()
