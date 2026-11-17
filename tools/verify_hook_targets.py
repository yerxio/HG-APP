"""Verify hook names and descriptors against original DEX definitions, not JADX aliases."""
import hashlib, json, pathlib, struct, zipfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
APK = next((ROOT/'resource/APK').glob('*.apk'))
BASE = 'com.dragon.read.component.shortvideo.impl.v2.view.adapter.a'
TARGETS = {
 BASE: {'I2':'(IILjava/lang/Object;)Z', 'Y0':'(IILjava/lang/String;Ljava/lang/Object;)Z',
        'P4':'(ILjava/lang/Object;)Z','Q0':'(ILjava/lang/Object;)V'},
 'com.dragon.read.component.shortvideo.impl.fullscreen.d': {'P4':'(ILjava/lang/Object;)Z'},
 'tx4.f': {'getData':'(I)Ljava/lang/Object;'},
 'j84.r': {'onBind':'(Ljava/lang/Object;I)V'},
}
rows=[]
with zipfile.ZipFile(APK) as z:
 for dn in z.namelist():
  if '/' in dn or not dn.endswith('.dex'): continue
  b=z.read(dn)
  def u32(p): return struct.unpack_from('<I',b,p)[0]
  def uleb(p):
   v=s=0
   while True:
    c=b[p];p+=1;v|=(c&127)<<s
    if not c&128:return v,p
    s+=7
  strings=[]
  for i in range(u32(56)):
   _,p=uleb(u32(u32(60)+4*i))
   strings.append(b[p:b.index(b'\0',p)].decode('utf-8','replace'))
  types=[strings[u32(u32(68)+4*i)] for i in range(u32(64))]
  for ci in range(u32(96)):
   off=u32(100)+32*ci
   name=types[u32(off)][1:-1].replace('/','.')
   if name not in TARGETS:continue
   p=u32(off+24)
   counts=[]
   for _ in range(4):v,p=uleb(p);counts.append(v)
   for _ in range(counts[0]+counts[1]):
    _,p=uleb(p);_,p=uleb(p)
   found={}
   for count in counts[2:]:
    mi=0
    for _ in range(count):
     delta,p=uleb(p);mi+=delta
     flags,p=uleb(p);code,p=uleb(p)
     mo=u32(92)+8*mi
     _,proto,ni=struct.unpack_from('<HHI',b,mo)
     mn=strings[ni]
     if mn not in TARGETS[name]:continue
     po=u32(76)+12*proto
     ret=types[u32(po+4)];params=u32(po+8)
     ts=[] if not params else [types[struct.unpack_from('<H',b,params+4+i*2)[0]] for i in range(u32(params))]
     desc='('+''.join(ts)+')'+ret
     found.setdefault(mn,[]).append(desc)
   for mn,expected in TARGETS[name].items():
    rows.append({'class':name,'method':mn,'expected':expected,'actual':found.get(mn,[]),
                 'dex':dn,'verified':expected in found.get(mn,[])})
result={'apk_sha256':hashlib.sha256(APK.read_bytes()).hexdigest(),'checks':rows,
        'all_passed':len(rows)==sum(map(len,TARGETS.values())) and all(r['verified'] for r in rows),
        'scope':'Static DEX verification only; not runtime LSPosed execution.'}
(ROOT/'analysis/reports/hook_signatures.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
raise SystemExit(0 if result['all_passed'] else 1)
