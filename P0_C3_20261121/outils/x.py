import struct,sys,zlib,os,collections
d=open(sys.argv[1],'rb').read();out=sys.argv[2]
i=0;ok=[];bad=[]
while True:
    j=d.find(b'PK\x03\x04',i)
    if j<0:break
    v,fl,m,t,dt,crc,cs,us,nl,el=struct.unpack('<HHHHHIIIHH',d[j+4:j+30])
    name=d[j+30:j+30+nl].decode();s=j+30+nl+el;i=s+cs
    if name.endswith('/'):continue
    blob=d[s:s+cs]
    try:
        raw=zlib.decompress(blob,-15) if m==8 else blob
        assert len(raw)==us and zlib.crc32(raw)==crc
        p=os.path.join(out,os.path.basename(name));open(p,'wb').write(raw);ok.append(name)
    except Exception as e: bad.append((name,len(blob),cs,repr(e)[:60]))
print('ok',len(ok),'bad',bad)
vp=collections.Counter(os.path.basename(n).split('__')[0] for n in ok);print(vp)
pages=collections.defaultdict(set)
for n in ok:
    a,b=os.path.basename(n).split('__');pages[b].add(a)
print(len(pages),'pages')
for p in sorted(pages):print(p,sorted(pages[p]))
