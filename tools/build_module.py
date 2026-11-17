"""Build both LSPosed variants without Gradle; record every command/output/status."""
import difflib, hashlib, json, os, pathlib, subprocess, urllib.request, zipfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
MOD = ROOT / 'modules/hongguo-feed-filter'
SDK = pathlib.Path(os.environ.get('ANDROID_HOME', os.environ.get('ANDROID_SDK_ROOT', str(pathlib.Path.home()/'AppData/Local/Android/Sdk'))))
BT = SDK/'build-tools'/os.environ.get('ANDROID_BUILD_TOOLS', '36.0.0')
ANDROID = SDK/'platforms'/os.environ.get('ANDROID_PLATFORM', 'android-36.1')/'android.jar'
API = ROOT/'tools/deps/xposed-api-82.jar'
OUT = MOD/'dist'
OUT.mkdir(parents=True, exist_ok=True)
RECORD = ROOT/'analysis/reports/build_verification.json'
RECORD.parent.mkdir(parents=True, exist_ok=True)
records = []

def sdktool(name):
    suffix = ('.bat' if name in ('d8','apksigner') else '.exe') if os.name == 'nt' else ''
    return BT/(name+suffix)

def run(args, cwd=ROOT):
    args = [str(a) for a in args]
    p = subprocess.run(args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    row = {'command': args, 'cwd': str(cwd), 'exit_code': p.returncode,
           'stdout': p.stdout.decode('utf-8', 'replace'), 'stderr': p.stderr.decode('utf-8', 'replace')}
    records.append(row)
    RECORD.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
    print(pathlib.Path(args[0]).name, 'exit=', p.returncode, flush=True)
    if p.returncode:
        print(row['stdout'].encode('ascii','backslashreplace').decode())
        print(row['stderr'].encode('ascii','backslashreplace').decode())
        raise SystemExit(p.returncode)
    return row

API.parent.mkdir(parents=True, exist_ok=True)
if not API.is_file():
    with urllib.request.urlopen('https://api.xposed.info/de/robv/android/xposed/api/82/api-82.jar', timeout=60) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != 'f48c635f1c7469fdec0e00ad2ea0b7a6b2f5b55065784a35b7ca3a84615e8e25':
        raise SystemExit('Xposed API checksum mismatch')
    API.write_bytes(data)
assert zipfile.is_zipfile(API)
assert hashlib.sha256(API.read_bytes()).hexdigest() == 'f48c635f1c7469fdec0e00ad2ea0b7a6b2f5b55065784a35b7ca3a84615e8e25'
testout = MOD/'build/tests'
testout.mkdir(parents=True, exist_ok=True)
run(['javac', '--release', '8', '-encoding', 'UTF-8', '-d', testout,
     MOD/'src/local/hongguore/feedfilter/Policy.java', *sorted((MOD/'tests').rglob('*.java'))])
for mode in ('observe','block'):
    run(['java', '-cp', testout, 'local.hongguore.feedfilter.PolicyTest', mode])

custom_key = os.environ.get('HG_KEYSTORE')
key = pathlib.Path(custom_key).resolve() if custom_key else MOD/'build/development-signing.p12'
if custom_key and not key.is_file():
    raise SystemExit('HG_KEYSTORE must name an existing signing key')
if custom_key and not os.environ.get('HG_KEYSTORE_PASSWORD'):
    raise SystemExit('Set HG_KEYSTORE_PASSWORD for the supplied signing key')
os.environ.setdefault('HG_KEYSTORE_PASSWORD', 'development-only')
alias = os.environ.get('HG_KEY_ALIAS', 'research' if custom_key else 'development')
if not key.exists():
    run(['keytool', '-genkeypair', '-keystore', key, '-storetype', 'PKCS12', '-storepass:env', 'HG_KEYSTORE_PASSWORD',
         '-keypass:env', 'HG_KEYSTORE_PASSWORD', '-alias', alias, '-keyalg', 'RSA', '-keysize', '2048',
         '-validity', '3650', '-dname', 'CN=HG-APP Local Development', '-noprompt'])

constants = {}
for mode in ('observe','block'):
    build = MOD/'build'/mode
    classes = build/'classes'
    dex = build/'dex'
    generated = build/'generated/local/hongguore/feedfilter/BuildMode.java'
    for d in (classes,dex,generated.parent): d.mkdir(parents=True, exist_ok=True)
    constants[mode] = ('package local.hongguore.feedfilter;\npublic final class BuildMode {\n'
                       '    public static final boolean BLOCK = ' + str(mode=='block').lower() + ';\n}\n')
    generated.write_text(constants[mode], encoding='utf-8')
    run(['javac','--release','8','-encoding','UTF-8','-cp',str(ANDROID)+os.pathsep+str(API),
         '-d',classes,*sorted((MOD/'src').rglob('*.java')),generated])
    jar = build/'classes.jar'
    with zipfile.ZipFile(jar,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(classes.rglob('*.class')): z.write(p,p.relative_to(classes).as_posix())
    run([sdktool('d8'),'--min-api','26','--lib',ANDROID,'--classpath',API,'--output',dex,jar])
    unsigned = build/'unsigned.apk'
    run([sdktool('aapt'),'package','-f','-M',MOD/'AndroidManifest.xml','-S',MOD/'res',
         '-A',MOD/'assets','-I',ANDROID,'-F',unsigned])
    with zipfile.ZipFile(unsigned,'a',zipfile.ZIP_STORED) as z:
        z.write(dex/'classes.dex','classes.dex')
    aligned = build/'aligned.apk'
    run([sdktool('zipalign'),'-f','4',unsigned,aligned])
    apk = OUT/f'hongguo-feed-filter-{mode}.apk'
    run([sdktool('apksigner'),'sign','--ks',key,'--ks-key-alias',alias,'--ks-pass','env:HG_KEYSTORE_PASSWORD',
         '--key-pass','env:HG_KEYSTORE_PASSWORD','--out',apk,aligned])
    run([sdktool('apksigner'),'verify','--verbose','--print-certs',apk])
    run([sdktool('aapt'),'dump','badging',apk])
    with zipfile.ZipFile(apk) as z:
        assert z.testzip() is None
        assert z.read('assets/xposed_init').strip() == b'local.hongguore.feedfilter.Entry'
        assert z.read('classes.dex').startswith(b'dex\n')
    print(apk.name,hashlib.sha256(apk.read_bytes()).hexdigest())

(OUT/'observe-to-block.diff').write_text(''.join(difflib.unified_diff(
    constants['observe'].splitlines(True),constants['block'].splitlines(True),
    fromfile='observe/BuildMode.java',tofile='block/BuildMode.java')),encoding='utf-8')
(OUT/'SHA256SUMS.txt').write_text('\n'.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.name
    for p in sorted(OUT.glob('*.apk')))+'\n',encoding='utf-8')
print('Build + JVM fixture tests + APK signature verification complete. This build does not run device tests.')
