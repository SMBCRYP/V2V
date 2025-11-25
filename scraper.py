import requests
import base64
import os
import json
import re
import time
import socket
import ssl
import random
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, parse_qs, unquote
from github import Github, Auth
from typing import Set, List, Dict, Tuple, Optional
from collections import defaultdict
import signal

def timeout_handler(signum, frame):
    print("⏰ TIMEOUT: Exceeded 48min")
    exit(1)

signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(48 * 60)

print("🚀 V2V Professional Scraper v10.0 - TUIC OPTIMIZED")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCES_FILE = os.path.join(BASE_DIR, "sources.json")
OUTPUT_JSON = os.path.join(BASE_DIR, "all_live_configs.json")
OUTPUT_CLASH = os.path.join(BASE_DIR, "clash_subscription.yml")
CACHE_VERSION = os.path.join(BASE_DIR, "cache_version.txt")

XRAY_PROTOCOLS = {'vless', 'vmess', 'trojan', 'ss'}
SINGBOX_PROTOCOLS = {'vless', 'vmess', 'trojan', 'ss', 'hy2', 'tuic'}

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
GITHUB_PAT = os.environ.get('GH_PAT')
MAX_CONFIGS_TO_TEST = 12000
MAX_CONFIGS_PER_PROTOCOL = 500
MAX_WORKERS = 120
TCP_TIMEOUT = 4.5
UDP_TIMEOUT = 5.0
MAX_LATENCY = 6000
GITHUB_LIMIT = int(os.environ.get('GITHUB_SEARCH_LIMIT', 200))
RETRY_FAILED = 2

def get_hash(cfg: str) -> str:
    """Generate unique hash for config deduplication"""
    try:
        u = urlparse(cfg)
        key = f"{u.scheme}:{u.hostname}:{u.port}:{u.username}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]
    except:
        return hashlib.sha256(cfg.encode()).hexdigest()[:16]

def b64d(s: str) -> Optional[str]:
    """Safe base64 decode with multiple methods"""
    if not s: return None
    methods = [
        lambda x: base64.b64decode(x).decode('utf-8', 'ignore'),
        lambda x: base64.urlsafe_b64decode(x + '===').decode('utf-8', 'ignore'),
        lambda x: base64.b64decode(x + '===').decode('utf-8', 'ignore'),
    ]
    s = s.strip().replace('\n', '').replace('\r', '').replace(' ', '')
    for method in methods:
        try: return method(s)
        except: continue
    return None

def norm_proto(p: str) -> str:
    """Normalize protocol names"""
    p = p.lower().strip()
    if p in ['shadowsocks']: return 'ss'
    if p in ['hysteria2', 'hysteria']: return 'hy2'
    return p

def parse_tuic(cfg: str) -> Optional[Dict]:
    """Advanced TUIC parser with comprehensive validation"""
    try:
        if not cfg or not cfg.startswith('tuic://'):
            return None
        
        u = urlparse(cfg)
        if not u.hostname or not u.port:
            return None
        
        port = int(u.port)
        if port <= 0 or port > 65535:
            return None
        
        q = parse_qs(u.query)
        
        uuid = None
        password = None
        
        if u.username:
            if ':' in u.username:
                uuid, password = u.username.split(':', 1)
            else:
                uuid = u.username
        
        if not uuid:
            uuid = q.get('uuid', [''])[0] or q.get('user', [''])[0]
        if not password:
            password = q.get('password', [''])[0] or q.get('pass', [''])[0]
        
        if not uuid and not password:
            return None
        
        return {
            'hostname': u.hostname,
            'port': port,
            'uuid': uuid or '',
            'password': password or '',
            'sni': q.get('sni', [u.hostname])[0],
            'alpn': q.get('alpn', ['h3'])[0],
            'congestion': q.get('congestion_control', ['bbr'])[0],
            'udp_relay_mode': q.get('udp_relay_mode', ['native'])[0],
        }
    except:
        return None

def parse_hy2(cfg: str) -> Optional[Dict]:
    """Advanced Hysteria2 parser"""
    try:
        if not cfg or not cfg.startswith(('hysteria2://', 'hy2://')):
            return None
        
        u = urlparse(cfg)
        if not u.hostname or not u.port:
            return None
        
        port = int(u.port)
        if port <= 0 or port > 65535:
            return None
        
        q = parse_qs(u.query)
        password = u.username or q.get('password', [''])[0] or q.get('auth', [''])[0]
        
        return {
            'hostname': u.hostname,
            'port': port,
            'password': password,
            'sni': q.get('sni', [u.hostname])[0],
            'obfs': q.get('obfs', [''])[0],
            'obfs_password': q.get('obfs-password', [''])[0],
        }
    except:
        return None

def is_valid(cfg: str) -> bool:
    """Comprehensive config validation"""
    if not cfg or not isinstance(cfg, str):
        return False
    
    cfg = cfg.strip()
    
    try:
        u = urlparse(cfg)
        p = norm_proto(u.scheme)
        
        if p not in SINGBOX_PROTOCOLS:
            return False
        
        if p == 'vmess':
            try:
                vmess_data = cfg.replace("vmess://", "").strip()
                decoded = b64d(vmess_data)
                if not decoded:
                    return False
                d = json.loads(decoded)
                return bool(d.get('add') and d.get('port') and d.get('id'))
            except:
                return False
        
        if p == 'tuic':
            info = parse_tuic(cfg)
            return info is not None
        
        if p == 'hy2':
            info = parse_hy2(cfg)
            return info is not None
        
        if not u.hostname or not u.port:
            return False
        
        port = int(u.port)
        if port <= 0 or port > 65535:
            return False
        
        if p in ['vless', 'trojan', 'ss']:
            return bool(u.username)
        
        return True
        
    except:
        return False

def extract(content: str) -> Set[str]:
    """Extract configs with enhanced pattern matching"""
    cfgs = set()
    if not content:
        return cfgs
    
    protocols = [
        'vless', 'vmess', 'trojan', 
        'ss', 'shadowsocks',
        'hysteria2', 'hy2', 'hysteria',
        'tuic'
    ]
    
    for p in protocols:
        pattern = rf'{p}://[^\s<>"\'`\n\r\[\]{{}}\|\\^~]+'
        matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            clean = match.strip()
            if is_valid(clean):
                cfgs.add(clean)
    
    base64_patterns = [
        r'[A-Za-z0-9+/=]{100,}',
        r'[A-Za-z0-9\-_=]{100,}',
    ]
    
    for pattern in base64_patterns:
        for b64_block in re.findall(pattern, content)[:30]:
            try:
                decoded = b64d(b64_block)
                if decoded:
                    for line in decoded.splitlines()[:150]:
                        line = line.strip()
                        if is_valid(line):
                            cfgs.add(line)
            except:
                continue
    
    return cfgs

def fetch_static(sources: List[str]) -> Set[str]:
    """Fetch from static sources with retry"""
    all_cfgs = set()
    print(f"📡 Fetching from {len(sources)} static sources...")
    
    def fetch_url(url: str, retry: int = 0) -> Set[str]:
        if retry >= RETRY_FAILED:
            return set()
        try:
            time.sleep(random.uniform(0.2, 1.0))
            response = requests.get(url, headers=HEADERS, timeout=25)
            response.raise_for_status()
            cfgs = extract(response.text)
            if cfgs:
                print(f"  ✓ {len(cfgs)} configs from {url[:60]}")
            return cfgs
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429 and retry < RETRY_FAILED:
                time.sleep(30)
                return fetch_url(url, retry + 1)
            return set()
        except:
            if retry < RETRY_FAILED:
                return fetch_url(url, retry + 1)
            return set()
    
    with ThreadPoolExecutor(max_workers=12) as ex:
        futures = {ex.submit(fetch_url, url): url for url in sources}
        for future in as_completed(futures, timeout=700):
            try:
                all_cfgs.update(future.result(timeout=35))
            except:
                continue
    
    print(f"  ✅ Total from static: {len(all_cfgs)}")
    return all_cfgs

def fetch_github(pat: str, limit: int) -> Set[str]:
    """Fetch from GitHub with optimized queries"""
    if not pat:
        return set()
    
    all_cfgs = set()
    processed = 0
    
    try:
        g = Github(auth=Auth.Token(pat), timeout=30)
        
        queries = [
            "tuic:// protocol config",
            "tuic uuid password",
            "hysteria2 hy2 config",
            "vless vmess trojan ss extension:txt",
            "v2ray subscription proxy",
            "sing-box tuic outbound",
            "clash meta tuic",
        ]
        
        print(f"🔍 Searching GitHub (limit: {limit})")
        start = time.time()
        
        for query in queries:
            if processed >= limit or time.time() - start > 1100:
                break
            try:
                results = g.search_code(query, order='desc', per_page=100)
                for file in results:
                    if processed >= limit:
                        break
                    try:
                        time.sleep(random.uniform(0.15, 0.35))
                        content = file.content.decode('utf-8', 'ignore')
                        cfgs = extract(content)
                        if cfgs:
                            all_cfgs.update(cfgs)
                            processed += 1
                            if processed % 25 == 0:
                                print(f"  📄 Processed {processed} files, found {len(all_cfgs)} configs")
                    except:
                        continue
            except:
                continue
        
        print(f"  ✅ GitHub: {len(all_cfgs)} configs from {processed} files")
        return all_cfgs
    except:
        return set()

def test_conn(cfg: str) -> Optional[Tuple[str, int, str]]:
    """Advanced connection test with protocol-specific handling"""
    try:
        u = urlparse(cfg)
        p = norm_proto(u.scheme)
        
        host, port, tls, sni = None, None, False, None
        
        if p == 'vmess':
            try:
                decoded = b64d(cfg.replace("vmess://", ""))
                d = json.loads(decoded)
                host = d.get('add')
                port = int(d.get('port', 0))
                tls = d.get('tls') in ['tls', 'xtls']
                sni = d.get('sni') or d.get('host') or host
            except:
                return None
        
        elif p == 'tuic':
            info = parse_tuic(cfg)
            if not info:
                return None
            host = info['hostname']
            port = info['port']
            tls = True
            sni = info['sni']
        
        elif p == 'hy2':
            info = parse_hy2(cfg)
            if not info:
                return None
            host = info['hostname']
            port = info['port']
            tls = True
            sni = info['sni']
        
        elif p in ['vless', 'trojan']:
            host = u.hostname
            port = int(u.port or 0)
            q = parse_qs(u.query)
            tls = p == 'trojan' or q.get('security', [''])[0] == 'tls'
            sni = q.get('sni', [host])[0]
        
        elif p == 'ss':
            host = u.hostname
            port = int(u.port or 0)
        
        else:
            return None
        
        if not host or port <= 0 or port > 65535:
            return None
        
        start = time.monotonic()
        
        if p in ['tuic', 'hy2']:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(UDP_TIMEOUT)
                sock.connect((host, port))
                
                if p == 'tuic':
                    sock.send(b'\x00\x00\x00\x01' + b'\x00' * 12)
                else:
                    sock.send(b'\x00' * 16)
                
                try:
                    sock.settimeout(2.0)
                    sock.recv(64)
                except socket.timeout:
                    pass
                except:
                    pass
                
                sock.close()
            except:
                return None
        
        else:
            try:
                sock = socket.create_connection((host, port), timeout=TCP_TIMEOUT)
                
                if tls:
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
                    
                    try:
                        ssock = ctx.wrap_socket(sock, server_hostname=sni or host)
                        ssock.do_handshake()
                        ssock.close()
                    except ssl.SSLError:
                        sock.close()
                else:
                    sock.close()
            except:
                return None
        
        lat = int((time.monotonic() - start) * 1000)
        
        if 0 < lat <= MAX_LATENCY:
            return (cfg, lat, p)
        
        return None
        
    except:
        return None

def balance(tested: List[Tuple[str, int, str]], protocols: Set[str]) -> List[str]:
    """Balance protocols with priority for rare ones"""
    groups = defaultdict(list)
    seen = set()
    
    for cfg, lat, proto in tested:
        if proto in protocols:
            h = get_hash(cfg)
            if h not in seen:
                groups[proto].append((cfg, lat, h))
                seen.add(h)
    
    for proto in groups:
        groups[proto].sort(key=lambda x: x[1])
    
    selected = []
    priority_protocols = {'tuic', 'hy2'}
    
    for proto in sorted(protocols):
        if proto in groups:
            if proto in priority_protocols:
                count = min(int(MAX_CONFIGS_PER_PROTOCOL * 1.5), len(groups[proto]))
            else:
                count = min(MAX_CONFIGS_PER_PROTOCOL, len(groups[proto]))
            
            for cfg, _, _ in groups[proto][:count]:
                selected.append(cfg)
    
    return selected

def gen_clash(cfgs: List[str]) -> Optional[str]:
    """Generate Clash YAML"""
    if not cfgs:
        return None
    
    prx = []
    seen = set()
    
    for cfg in cfgs:
        try:
            u = urlparse(cfg)
            p = norm_proto(u.scheme)
            h = get_hash(cfg)
            
            if h in seen or p not in XRAY_PROTOCOLS:
                continue
            seen.add(h)
            
            name = f"{p}{h[:7]}"
            proxy = {'name': name, 'server': u.hostname, 'port': int(u.port), 'skip-cert-verify': True}
            
            if p == 'vmess':
                d = json.loads(b64d(cfg.replace("vmess://", "")))
                proxy.update({
                    'type': 'vmess',
                    'uuid': d.get('id'),
                    'alterId': int(d.get('aid', 0)),
                    'cipher': d.get('scy', 'auto'),
                    'udp': True
                })
                if d.get('net') == 'ws':
                    proxy['network'] = 'ws'
                    proxy['ws-opts'] = {'path': d.get('path', '/'), 'headers': {'Host': d.get('host', u.hostname)}}
                if d.get('tls') == 'tls':
                    proxy['tls'] = True
                    proxy['servername'] = d.get('sni') or d.get('host') or u.hostname
                    
            elif p == 'vless':
                q = parse_qs(u.query)
                proxy.update({'type': 'vless', 'uuid': u.username, 'udp': True})
                if q.get('type', [''])[0] == 'ws':
                    proxy['network'] = 'ws'
                    proxy['ws-opts'] = {'path': q.get('path', ['/'])[0], 'headers': {'Host': q.get('host', [u.hostname])[0]}}
                if q.get('security', [''])[0] == 'tls':
                    proxy['tls'] = True
                    proxy['servername'] = q.get('sni', [u.hostname])[0]
                    if q.get('flow'): proxy['flow'] = q.get('flow')[0]
                        
            elif p == 'trojan':
                q = parse_qs(u.query)
                proxy.update({'type': 'trojan', 'password': u.username, 'udp': True, 'sni': q.get('sni', [u.hostname])[0]})
                
            elif p == 'ss':
                d = b64d(u.username)
                if d and ':' in d:
                    idx = d.index(':')
                    proxy.update({'type': 'ss', 'cipher': d[:idx], 'password': d[idx+1:], 'udp': True})
            
            if proxy.get('type'):
                prx.append(proxy)
        except:
            continue
    
    if not prx:
        return None
    
    names = [x['name'] for x in prx]
    y = 'proxies:\n'
    
    for x in prx:
        y += f"  - name: {x['name']}\n    type: {x['type']}\n    server: {x['server']}\n    port: {x['port']}\n"
        
        if x['type'] == 'vmess':
            y += f"    uuid: {x['uuid']}\n    alterId: {x['alterId']}\n    cipher: {x['cipher']}\n    udp: true\n"
            if x.get('network'):
                y += f"    network: {x['network']}\n"
                if x.get('ws-opts'):
                    y += f"    ws-opts:\n      path: {x['ws-opts']['path']}\n      headers:\n        Host: {x['ws-opts']['headers']['Host']}\n"
            if x.get('tls'):
                y += f"    tls: true\n    servername: {x['servername']}\n"
            y += "    skip-cert-verify: true\n"
            
        elif x['type'] == 'vless':
            y += f"    uuid: {x['uuid']}\n    udp: true\n"
            if x.get('network'):
                y += f"    network: {x['network']}\n"
                if x.get('ws-opts'):
                    y += f"    ws-opts:\n      path: {x['ws-opts']['path']}\n      headers:\n        Host: {x['ws-opts']['headers']['Host']}\n"
            if x.get('tls'):
                y += f"    tls: true\n    servername: {x['servername']}\n"
                if x.get('flow'): y += f"    flow: {x['flow']}\n"
            y += "    skip-cert-verify: true\n"
            
        elif x['type'] == 'trojan':
            y += f"    password: {x['password']}\n    udp: true\n    sni: {x['sni']}\n    skip-cert-verify: true\n"
            
        elif x['type'] == 'ss':
            y += f"    cipher: {x['cipher']}\n    password: {x['password']}\n    udp: true\n"
    
    y += '\nproxy-groups:\n  - name: V2V-Auto\n    type: url-test\n    proxies:\n'
    for n in names: y += f"      - {n}\n"
    y += '    url: http://www.gstatic.com/generate_204\n    interval: 300\n\n'
    y += '  - name: V2V-Select\n    type: select\n    proxies:\n      - V2V-Auto\n'
    for n in names: y += f"      - {n}\n"
    y += '\nrules:\n  - GEOIP,IR,DIRECT\n  - MATCH,V2V-Select\n'
    
    return y

def main():
    try:
        print("\n" + "="*70)
        print("🚀 V2V PROFESSIONAL SCRAPER - TUIC OPTIMIZED")
        print("="*70)
        
        print("\n📂 1. Loading Sources...")
        with open(SOURCES_FILE, 'r') as f:
            sources = json.load(f).get("static", [])
        print(f"   ✓ Loaded {len(sources)} static sources")
        
        print("\n📥 2. Fetching Configs...")
        all_cfgs = set()
        
        with ThreadPoolExecutor(max_workers=2) as ex:
            static_future = ex.submit(fetch_static, sources)
            github_future = ex.submit(fetch_github, GITHUB_PAT, GITHUB_LIMIT)
            
            try:
                all_cfgs.update(static_future.result(timeout=1000))
                all_cfgs.update(github_future.result(timeout=1300))
            except:
                pass
        
        if not all_cfgs:
            print("   ❌ No configs found!")
            return
        
        print(f"\n   ✅ Total unique configs: {len(all_cfgs)}")
        
        proto_dist = defaultdict(int)
        for cfg in all_cfgs:
            try:
                p = norm_proto(urlparse(cfg).scheme)
                proto_dist[p] += 1
            except:
                pass
        print("\n   📊 Pre-test distribution:")
        for p in sorted(proto_dist.keys()):
            print(f"      {p}: {proto_dist[p]}")
        
        print(f"\n🔬 3. Testing Connections (max: {MAX_CONFIGS_TO_TEST})...")
        tested = []
        to_test = list(all_cfgs)[:MAX_CONFIGS_TO_TEST]
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
            futures = {ex.submit(test_conn, cfg): cfg for cfg in to_test}
            completed = 0
            
            for future in as_completed(futures, timeout=1600):
                try:
                    result = future.result(timeout=10)
                    if result:
                        tested.append(result)
                    completed += 1
                    if completed % 400 == 0:
                        print(f"   📊 {completed}/{len(to_test)} tested ({len(tested)} working)")
                except:
                    pass
        
        print(f"\n   ✅ Working configs: {len(tested)}")
        
        working_dist = defaultdict(int)
        for _, _, p in tested:
            working_dist[p] += 1
        print("\n   📊 Working distribution:")
        for p in sorted(working_dist.keys()):
            print(f"      {p}: {working_dist[p]}")
        
        print("\n🎯 4. Selecting Best Configs...")
        
        xray_tested = [(c, l, pr) for c, l, pr in tested if pr in XRAY_PROTOCOLS]
        xray_cfgs = balance(xray_tested, XRAY_PROTOCOLS)
        
        used_hashes = set(get_hash(c) for c in xray_cfgs)
        remaining = [(c, l, pr) for c, l, pr in tested if get_hash(c) not in used_hashes]
        singbox_cfgs = balance(remaining, SINGBOX_PROTOCOLS)
        
        def group_by_protocol(cfgs: List[str]) -> Dict[str, List[str]]:
            grouped = defaultdict(list)
            seen_per_proto = defaultdict(set)
            
            for cfg in cfgs:
                p = norm_proto(urlparse(cfg).scheme)
                h = get_hash(cfg)
                if h not in seen_per_proto[p]:
                    grouped[p].append(cfg)
                    seen_per_proto[p].add(h)
            
            return dict(grouped)
        
        xray_grouped = group_by_protocol(xray_cfgs)
        singbox_grouped = group_by_protocol(singbox_cfgs)
        
        for p in XRAY_PROTOCOLS:
            if p not in xray_grouped:
                xray_grouped[p] = []
        
        for p in SINGBOX_PROTOCOLS:
            if p not in singbox_grouped:
                singbox_grouped[p] = []
        
        output = {"xray": xray_grouped, "singbox": singbox_grouped}
        
        print("\n📊 5. Final Distribution:")
        xray_total = sum(len(v) for v in xray_grouped.values())
        singbox_total = sum(len(v) for v in singbox_grouped.values())
        
        print(f"\n   Xray ({xray_total} configs):")
        for p in sorted(xray_grouped.keys()):
            count = len(xray_grouped[p])
            print(f"      • {p}: {count}")
        
        print(f"\n   Singbox ({singbox_total} configs):")
        for p in sorted(singbox_grouped.keys()):
            count = len(singbox_grouped[p])
            emoji = "🔥" if p in ['tuic', 'hy2'] else "•"
            print(f"      {emoji} {p}: {count}")
        
        print("\n💾 6. Writing Files...")
        
        with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"   ✓ {OUTPUT_JSON}")
        
        clash = gen_clash(xray_cfgs)
        with open(OUTPUT_CLASH, 'w', encoding='utf-8') as f:
            f.write(clash if clash else "proxies: []\n")
        print(f"   ✓ {OUTPUT_CLASH}")
        
        with open(CACHE_VERSION, 'w') as f:
            f.write(str(int(time.time())))
        print(f"   ✓ {CACHE_VERSION}")
        
        print("\n" + "="*70)
        print("✅ SCRAPER COMPLETED SUCCESSFULLY")
        print("="*70)
        print(f"\n📈 Summary:")
        print(f"   • Total Xray: {xray_total}")
        print(f"   • Total Singbox: {singbox_total}")
        print(f"   • Grand Total: {xray_total + singbox_total}")
        print(f"   • TUIC configs: {len(singbox_grouped.get('tuic', []))}")
        print(f"   • Hy2 configs: {len(singbox_grouped.get('hy2', []))}")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        signal.alarm(0)

if __name__ == "__main__":
    main()
