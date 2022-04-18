from sys import argv as a

if len(a) <= 3:
    print("usage: genbind <LIBNAME> <BIND> <OUT>")
    quit(1)
lib = a[1]
bnd = a[2]
outfile = a[3]

file_ = open(bnd).read().split()

out = ''
cur = ''
inclass = False
idclass = ''

for i in file_:
    if i == 'end':
        if not inclass:
            print('error: unmatched end')
        out += '\n\n'+cur+'\n\n'
        cur = ''
        inclass = False
    elif i == 'do':
        inclass = True
    else:
        if inclass:
            cur += f'\tdef {i}(self, *args):\n\t\treturn __lua__("{lib}.{idclass}.{i}(...)")\n\n'
        else:
            cur += f'class {i}:\n'
            idclass = i

with open(outfile, 'w') as f:
    f.write(out)