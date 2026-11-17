"""Read-only APK inventory and exact DEX class index (no decompiler aliases)."""
import hashlib, json, pathlib, struct, zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
apk = next((ROOT / 'resource/APK').glob('*.apk'))
out = ROOT / 'analysis/static'
out.mkdir(parents=True, exist_ok=True)
rows = []
with zipfile.ZipFile(apk) as z:
    for name in z.namelist():
        if '/' in name or not name.endswith('.dex'):
            continue
        b = z.read(name)
        u32 = lambda off: struct.unpack_from('<I', b, off)[0]
        strings = []
        for i in range(u32(56)):
            p = u32(u32(60) + i * 4)
            while b[p] & 128: p += 1
            p += 1
            strings.append(b[p:b.index(b'\0', p)].decode('utf-8', 'replace'))
        types = [strings[u32(u32(68) + i*4)] for i in range(u32(64))]
        for i in range(u32(96)):
            cls = types[u32(u32(100) + i*32)]
            rows.append((name, cls[1:-1].replace('/', '.')))
    metadata = {'apk': str(apk.relative_to(ROOT)), 'size': apk.stat().st_size,
                'sha256': hashlib.sha256(apk.read_bytes()).hexdigest(),
                'dex_count': len({x[0] for x in rows}), 'class_count': len(rows),
                'native_libraries': [n for n in z.namelist() if n.endswith('.so')]}
(out/'apk_inventory.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
(out/'classes.tsv').write_text('dex\tclass\n' + '\n'.join('\t'.join(x) for x in rows), encoding='utf-8')
print(json.dumps({k:v for k,v in metadata.items() if k != 'native_libraries'}, ensure_ascii=True))
