import struct,sys,zlib,os,collections
d=open(sys.argv[1],'rb').read();out=os.path.realpath(sys.argv[2])
i=0;ok=[];bad=[];entries=[]
while True:
    j=d.find(b'PK\x03\x04',i)
    if j<0:break
    v,fl,m,t,dt,crc,cs,us,nl,el=struct.unpack('<HHHHHIIIHH',d[j+4:j+30])
    name=d[j+30:j+30+nl].decode('utf8','replace');s=j+30+nl+el;i=s+cs
    entries.append(name)
    if name.endswith('/'):continue
    p=os.path.realpath(os.path.join(out,name))
    if not p.startswith(out+'/'):bad.append((name,'path'));continue
    blob=d[s:s+cs]
    try:
        raw=zlib.decompress(blob,-15) if m==8 else blob
        assert len(raw)==us and zlib.crc32(raw)==crc
        os.makedirs(os.path.dirname(p),exist_ok=True);open(p,'wb').write(raw);ok.append(name)
    except Exception as e: bad.append((name,len(blob),cs,repr(e)[:60]))
print('entries',len(entries),'ok',len(ok),'bad',bad)
print('last entry:',entries[-1])
top=collections.Counter('/'.join(n.split('/')[:2]) for n in entries);
for k,v in top.items():print(v,k)
