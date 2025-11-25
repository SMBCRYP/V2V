import { connect } from 'cloudflare:sockets';

const TTL = 120 * 24 * 60 * 60;
const ORIGINS = ['https://smbcryp.github.io', 'https://v2v-vercel.vercel.app', 'https://v2v-data.s3-website.ir-thr-at1.arvanstorage.ir'];

const cors = (o) => ORIGINS.includes(o) ? { 'Access-Control-Allow-Origin': o, 'Access-Control-Allow-Methods': 'GET,POST,OPTIONS', 'Access-Control-Allow-Headers': 'Content-Type', 'Vary': 'Origin' } : { 'Access-Control-Allow-Origin': '*', 'Access-Control-Allow-Methods': 'GET,POST,OPTIONS' };
const json = (d, s, h) => new Response(JSON.stringify(d), { status: s, headers: { 'Content-Type': 'application/json', ...h } });
const text = (t, c, h, f) => new Response(t, { status: 200, headers: { 'Content-Type': `${c}; charset=utf-8`, ...(f ? { 'Content-Disposition': `attachment; filename="${f}"` } : {}), ...h } });

const genV2VId = () => {
    const timestamp = Date.now().toString(36);
    const random = Array.from({ length: 6 }, () => 'abcdefghijklmnopqrstuvwxyz0123456789'[Math.floor(Math.random() * 36)]).join('');
    return `v2v${timestamp}${random}`;
};

const uid = (p, s, i) => `${p}${Math.abs((s + i).split('').reduce((a, b) => ((a << 5) - a + b.charCodeAt(0)) | 0, 0)).toString(36).slice(0, 6)}`;

const b64e = (str) => {
    try {
        const bytes = new TextEncoder().encode(str);
        let binary = '';
        for (let i = 0; i < bytes.length; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return btoa(binary);
    } catch {
        return btoa(unescape(encodeURIComponent(str)));
    }
};

const b64d = (s) => {
    try {
        return atob(s.replace(/-/g, '+').replace(/_/g, '/'));
    } catch {
        return null;
    }
};

const sanitize = (str) => str ? String(str).replace(/[^\x20-\x7E]/g, '').trim() : '';

const parseVmess = (cfg) => {
    try {
        if (!cfg?.startsWith('vmess://')) return null;
        const d = b64d(cfg.slice(8));
        if (!d) return null;
        const j = JSON.parse(d);
        if (!j.add || !j.port || !j.id) return null;
        return {
            s: j.add,
            p: parseInt(j.port),
            u: j.id,
            a: parseInt(j.aid) || 0,
            c: j.scy || 'auto',
            n: j.net || 'tcp',
            t: j.tls === 'tls',
            sni: j.sni || j.host || j.add,
            path: j.path || '/',
            host: j.host || j.add
        };
    } catch {
        return null;
    }
};

const parseVless = (cfg) => {
    try {
        if (!cfg?.startsWith('vless://')) return null;
        const u = new URL(cfg);
        if (!u.hostname || !u.port || !u.username) return null;
        const q = new URLSearchParams(u.search);
        return {
            s: u.hostname,
            p: parseInt(u.port),
            u: decodeURIComponent(u.username),
            n: q.get('type') || 'tcp',
            t: q.get('security') === 'tls',
            sni: q.get('sni') || u.hostname,
            path: decodeURIComponent(q.get('path') || '/'),
            host: q.get('host') || u.hostname,
            flow: q.get('flow') || ''
        };
    } catch {
        return null;
    }
};

const parseTrojan = (cfg) => {
    try {
        if (!cfg?.startsWith('trojan://')) return null;
        const u = new URL(cfg);
        if (!u.hostname || !u.port || !u.username) return null;
        const q = new URLSearchParams(u.search);
        return {
            s: u.hostname,
            p: parseInt(u.port),
            pw: decodeURIComponent(u.username),
            sni: q.get('sni') || u.hostname
        };
    } catch {
        return null;
    }
};

const parseSs = (cfg) => {
    try {
        if (!cfg?.startsWith('ss://')) return null;
        const u = new URL(cfg);
        if (!u.hostname || !u.port) return null;
        let method, password;
        if (u.password) {
            method = u.username;
            password = u.password;
        } else {
            const d = b64d(u.username);
            if (!d || !d.includes(':')) return null;
            const i = d.indexOf(':');
            method = d.slice(0, i);
            password = d.slice(i + 1);
        }

        return {
            s: u.hostname,
            p: parseInt(u.port),
            m: decodeURIComponent(method), // حذف کاراکترهای درصد دار احتمالی
            pw: decodeURIComponent(password)
        };
    } catch {
        return null;
    }
};


const parseHysteria2 = (cfg) => {
    try {
        if (!cfg?.startsWith('hysteria2://') && !cfg?.startsWith('hy2://')) return null;
        const u = new URL(cfg);
        if (!u.hostname || !u.port) return null;
        const q = new URLSearchParams(u.search);
        
        const rawPassword = u.username || q.get('password') || q.get('auth') || '';

        return {
            s: u.hostname,
            p: parseInt(u.port),
            pw: decodeURIComponent(rawPassword),
            sni: q.get('sni') || u.hostname,
            obfs: q.get('obfs') || null,
            obfsPw: q.get('obfs-password') || ''
        };
    } catch {
        return null;
    }
};


const parseTuic = (cfg) => {
    try {
        if (!cfg?.startsWith('tuic://')) return null;
        const u = new URL(cfg);
        if (!u.hostname || !u.port) return null;
        const q = new URLSearchParams(u.search);
        
        let uuid = u.username;
        let password = u.password;

        if (!password && uuid && uuid.includes(':')) {
            [uuid, password] = uuid.split(':', 2);
        }
        
        if (!uuid) uuid = q.get('uuid') || q.get('user') || '';
        if (!password) password = q.get('password') || q.get('pass') || '';

        return {
            s: u.hostname,
            p: parseInt(u.port),
            u: decodeURIComponent(uuid),
            pw: decodeURIComponent(password),
            sni: q.get('sni') || u.hostname,
            cc: q.get('congestion_control') || 'bbr',
            alpn: q.get('alpn') || 'h3'
        };
    } catch {
        return null;
    }
};


const genXraySubscription = (cfgs) => {
    const valid = [];
    const seen = new Set();
    for (const cfg of cfgs) {
        try {
            const u = new URL(cfg);
            const k = `${u.protocol}//${u.hostname}:${u.port}:${u.username}`;
            if (!seen.has(k) && ['vmess:', 'vless:', 'trojan:', 'ss:'].includes(u.protocol)) {
                seen.add(k);
                valid.push(cfg);
            }
        } catch {}
    }
    return b64e(valid.join('\n'));
};

const genClashForXray = (cfgs) => {
    const prx = [];
    const seen = new Set();
    for (let i = 0; i < cfgs.length; i++) {
        try {
            let p = null;
            let k = null;
            if (cfgs[i].startsWith('vmess://')) {
                const v = parseVmess(cfgs[i]);
                if (!v) continue;
                k = `vm${v.s}${v.p}${v.u}`;
                if (seen.has(k)) continue;
                p = {
                    name: uid('vm', v.s, i),
                    type: 'vmess',
                    server: sanitize(v.s),
                    port: v.p,
                    uuid: sanitize(v.u),
                    alterId: v.a,
                    cipher: sanitize(v.c),
                    udp: true,
                    'skip-cert-verify': true
                };
                if (v.n === 'ws') {
                    p.network = 'ws';
                    p['ws-opts'] = {
                        path: sanitize(v.path),
                        headers: { Host: sanitize(v.host) }
                    };
                }
                if (v.t) {
                    p.tls = true;
                    p.servername = sanitize(v.sni);
                }
            } else if (cfgs[i].startsWith('vless://')) {
                const v = parseVless(cfgs[i]);
                if (!v) continue;
                k = `vl${v.s}${v.p}${v.u}`;
                if (seen.has(k)) continue;
                p = {
                    name: uid('vl', v.s, i),
                    type: 'vless',
                    server: sanitize(v.s),
                    port: v.p,
                    uuid: sanitize(v.u),
                    udp: true,
                    'skip-cert-verify': true
                };
                if (v.n === 'ws') {
                    p.network = 'ws';
                    p['ws-opts'] = {
                        path: sanitize(v.path),
                        headers: { Host: sanitize(v.host) }
                    };
                }
                if (v.t) {
                    p.tls = true;
                    p.servername = sanitize(v.sni);
                    if (v.flow) p.flow = sanitize(v.flow);
                }
            } else if (cfgs[i].startsWith('trojan://')) {
                const v = parseTrojan(cfgs[i]);
                if (!v) continue;
                k = `tr${v.s}${v.p}${v.pw}`;
                if (seen.has(k)) continue;
                p = {
                    name: uid('tr', v.s, i),
                    type: 'trojan',
                    server: sanitize(v.s),
                    port: v.p,
                    password: sanitize(v.pw),
                    udp: true,
                    sni: sanitize(v.sni),
                    'skip-cert-verify': true
                };
            } else if (cfgs[i].startsWith('ss://')) {
                const v = parseSs(cfgs[i]);
                if (!v) continue;
                k = `ss${v.s}${v.p}${v.m}`;
                if (seen.has(k)) continue;
                p = {
                    name: uid('ss', v.s, i),
                    type: 'ss',
                    server: sanitize(v.s),
                    port: v.p,
                    cipher: sanitize(v.m),
                    password: sanitize(v.pw),
                    udp: true
                };
            }
            if (p && k) {
                seen.add(k);
                prx.push(p);
            }
        } catch {}
    }
    if (!prx.length) return null;
    const n = prx.map(x => x.name);
    let y = '# Clash Meta for Xray - V2V Signature\n\n';
    y += 'port: 7890\n';
    y += 'socks-port: 7891\n';
    y += 'allow-lan: true\n';
    y += 'mode: rule\n';
    y += 'log-level: info\n';
    y += 'external-controller: 127.0.0.1:9090\n\n';
    y += 'dns:\n';
    y += '  enable: true\n';
    y += '  listen: 0.0.0.0:53\n';
    y += '  enhanced-mode: fake-ip\n';
    y += '  fake-ip-range: 198.18.0.1/16\n';
    y += '  nameserver:\n';
    y += '    - 8.8.8.8\n';
    y += '    - 1.1.1.1\n';
    y += '  fallback:\n';
    y += '    - https://dns.google/dns-query\n\n';
    y += 'proxies:\n';
    for (const x of prx) {
        y += `  - name: "${x.name}"\n`;
        y += `    type: ${x.type}\n`;
        y += `    server: ${x.server}\n`;
        y += `    port: ${x.port}\n`;
        if (x.type === 'vmess') {
            y += `    uuid: ${x.uuid}\n`;
            y += `    alterId: ${x.alterId}\n`;
            y += `    cipher: ${x.cipher}\n`;
            y += `    udp: true\n`;
            if (x.network) {
                y += `    network: ${x.network}\n`;
                if (x['ws-opts']) {
                    y += `    ws-opts:\n`;
                    y += `      path: "${x['ws-opts'].path}"\n`;
                    y += `      headers:\n`;
                    y += `        Host: ${x['ws-opts'].headers.Host}\n`;
                }
            }
            if (x.tls) {
                y += `    tls: true\n`;
                y += `    servername: ${x.servername}\n`;
            }
            y += `    skip-cert-verify: true\n`;
        } else if (x.type === 'vless') {
            y += `    uuid: ${x.uuid}\n`;
            y += `    udp: true\n`;
            if (x.network) {
                y += `    network: ${x.network}\n`;
                if (x['ws-opts']) {
                    y += `    ws-opts:\n`;
                    y += `      path: "${x['ws-opts'].path}"\n`;
                    y += `      headers:\n`;
                    y += `        Host: ${x['ws-opts'].headers.Host}\n`;
                }
            }
            if (x.tls) {
                y += `    tls: true\n`;
                y += `    servername: ${x.servername}\n`;
                if (x.flow) y += `    flow: ${x.flow}\n`;
            }
            y += `    skip-cert-verify: true\n`;
        } else if (x.type === 'trojan') {
            y += `    password: ${x.password}\n`;
            y += `    udp: true\n`;
            y += `    sni: ${x.sni}\n`;
            y += `    skip-cert-verify: true\n`;
        } else if (x.type === 'ss') {
            y += `    cipher: ${x.cipher}\n`;
            y += `    password: ${x.password}\n`;
            y += `    udp: true\n`;
        }
    }
    y += '\nproxy-groups:\n';
    y += '  - name: "V2V-AUTO"\n';
    y += '    type: url-test\n';
    y += '    proxies:\n';
    for (const name of n) y += `      - "${name}"\n`;
    y += '    url: http://www.gstatic.com/generate_204\n';
    y += '    interval: 300\n';
    y += '    tolerance: 50\n\n';
    y += '  - name: "V2V-SELECT"\n';
    y += '    type: select\n';
    y += '    proxies:\n';
    y += '      - V2V-AUTO\n';
    for (const name of n) y += `      - "${name}"\n`;
    y += '\nrules:\n';
    y += '  - GEOIP,IR,DIRECT\n';
    y += '  - MATCH,V2V-SELECT\n';
    return y;
};

const genSingboxSubscription = (cfgs) => {
    const out = [];
    const seen = new Set();

    for (let i = 0; i < cfgs.length; i++) {
        try {
            let o = null;
            let k = null;
            
            if (cfgs[i].startsWith('vmess://')) {
                const v = parseVmess(cfgs[i]);
                if (!v) continue;
                k = `vm${v.s}${v.p}${v.u}`;
                if (seen.has(k)) continue;
                o = {
                    tag: uid('vm', v.s, i),
                    type: 'vmess',
                    server: sanitize(v.s),
                    server_port: v.p,
                    uuid: sanitize(v.u),
                    alter_id: v.a,
                    security: sanitize(v.c)
                };
                if (v.n === 'ws') {
                    o.transport = {
                        type: 'ws',
                        path: sanitize(v.path),
                        headers: { Host: sanitize(v.host) }
                    };
                }
                if (v.t) {
                    o.tls = {
                        enabled: true,
                        server_name: sanitize(v.sni),
                        insecure: true
                    };
                }
            } else if (cfgs[i].startsWith('vless://')) {
                const v = parseVless(cfgs[i]);
                if (!v) continue;
                k = `vl${v.s}${v.p}${v.u}`;
                if (seen.has(k)) continue;
                o = {
                    tag: uid('vl', v.s, i),
                    type: 'vless',
                    server: sanitize(v.s),
                    server_port: v.p,
                    uuid: sanitize(v.u)
                };
                if (v.n === 'ws') {
                    o.transport = {
                        type: 'ws',
                        path: sanitize(v.path),
                        headers: { Host: sanitize(v.host) }
                    };
                }
                if (v.t) {
                    o.tls = {
                        enabled: true,
                        server_name: sanitize(v.sni),
                        insecure: true
                    };
                    if (v.flow) o.flow = sanitize(v.flow);
                }
            } else if (cfgs[i].startsWith('trojan://')) {
                const v = parseTrojan(cfgs[i]);
                if (!v) continue;
                k = `tr${v.s}${v.p}${v.pw}`;
                if (seen.has(k)) continue;
                o = {
                    tag: uid('tr', v.s, i),
                    type: 'trojan',
                    server: sanitize(v.s),
                    server_port: v.p,
                    password: sanitize(v.pw),
                    tls: {
                        enabled: true,
                        server_name: sanitize(v.sni),
                        insecure: true
                    }
                };
            } else if (cfgs[i].startsWith('ss://')) {
                const v = parseSs(cfgs[i]);
                if (!v) continue;
                k = `ss${v.s}${v.p}${v.m}`;
                if (seen.has(k)) continue;
                o = {
                    tag: uid('ss', v.s, i),
                    type: 'shadowsocks',
                    server: sanitize(v.s),
                    server_port: v.p,
                    method: sanitize(v.m),
                    password: sanitize(v.pw)
                };
            } else if (cfgs[i].startsWith('hysteria2://') || cfgs[i].startsWith('hy2://')) {
                const v = parseHysteria2(cfgs[i]);
                if (!v) continue;
                k = `hy2${v.s}${v.p}`;
                if (seen.has(k)) continue;
                o = {
                    tag: uid('hy2', v.s, i),
                    type: 'hysteria2',
                    server: sanitize(v.s),
                    server_port: v.p,
                    password: sanitize(v.pw),
                    tls: {
                        enabled: true,
                        server_name: sanitize(v.sni),
                        insecure: true
                    }
                };
                if (v.obfs) {
                    o.obfs = {
                        type: v.obfs,
                        password: sanitize(v.obfsPw)
                    };
                }
            } else if (cfgs[i].startsWith('tuic://')) {
                const v = parseTuic(cfgs[i]);
                if (!v || !v.u) continue;
                k = `tuic${v.s}${v.p}${v.u}`;
                if (seen.has(k)) continue;
                o = {
                    tag: uid('tuic', v.s, i),
                    type: 'tuic',
                    server: sanitize(v.s),
                    server_port: v.p,
                    uuid: sanitize(v.u),
                    password: sanitize(v.pw),
                    congestion_control: v.cc,
                    udp_relay_mode: 'native',
                    tls: {
                        enabled: true,
                        server_name: sanitize(v.sni),
                        insecure: true,
                        alpn: [v.alpn]
                    }
                };
            }

            if (o && k) {
                seen.add(k);
                out.push(o);
            }
        } catch {}
    }

    if (!out.length) return null;
    const tags = out.map(x => x.tag);

    return JSON.stringify({
        "log": {
            "level": "error",
            "timestamp": true
        },
        "dns": {
            "servers": [
                {
                    "type": "tcp",
                    "tag": "direct-dns",
                    "server": "8.8.8.8"
                },
                {
                    "type": "tcp",
                    "tag": "proxy-dns",
                    "detour": "select",
                    "server": "8.8.8.8"
                },
                {
                    "type": "local",
                    "tag": "local-dns",
                    "detour": "direct"
                }
            ],
            "rules": [
                { "clash_mode": "Global", "server": "proxy-dns" },
                {
                    "source_ip_cidr": [
                        "172.19.0.0/30",
                        "fdfe:dcba:9876::1/126"
                    ],
                    "server": "direct-dns"
                },
                { "clash_mode": "Direct", "server": "direct-dns" },
                {
                    "rule_set": ["geosite-ir", "geoip-ir"],
                    "server": "direct-dns"
                },
                { "domain_suffix": ".ir", "server": "direct-dns" }
            ],
            "final": "local-dns",
            "strategy": "prefer_ipv4",
            "independent_cache": true
        },
        "inbounds": [
            {
                "type": "tun",
                "tag": "tun-in",
                "mtu": 9000,
                "address": [
                    "172.19.0.1/30",
                    "fdfe:dcba:9876::1/126"
                ],
                "auto_route": true,
                "stack": "system",
                "platform": {
                    "http_proxy": {
                        "enabled": true,
                        "server": "127.0.0.1",
                        "server_port": 2080
                    }
                }
            },
            {
                "type": "mixed",
                "listen": "127.0.0.1",
                "listen_port": 2080
            }
        ],
        "outbounds": [
            {
                "type": "selector",
                "tag": "select",
                "outbounds": ["auto", "direct", ...tags],
                "default": "auto"
            },
            {
                "type": "urltest",
                "tag": "auto",
                "outbounds": tags,
                "url": "http://www.gstatic.com/generate_204",
                "interval": "10m",
                "tolerance": 50
            },
            ...out,
            { "type": "direct", "tag": "direct" },
            { "type": "block", "tag": "block" }
        ],
        "route": {
            "rules": [
                { "action": "sniff" },
                { "clash_mode": "Direct", "outbound": "direct" },
                { "clash_mode": "Global", "outbound": "select" },
                { "protocol": "dns", "action": "hijack-dns" },
                {
                    "rule_set": [
                        "geoip-private",
                        "geosite-private",
                        "geosite-ir",
                        "geoip-ir"
                    ],
                    "outbound": "direct"
                },
                {
                    "rule_set": "geosite-ads",
                    "action": "reject"
                }
            ],
            "rule_set": [
                {
                    "type": "remote",
                    "tag": "geosite-ads",
                    "url": "https://testingcf.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@sing/geo/geosite/category-ads-all.srs",
                    "download_detour": "direct"
                },
                {
                    "type": "remote",
                    "tag": "geosite-private",
                    "url": "https://testingcf.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@sing/geo/geosite/private.srs",
                    "download_detour": "direct"
                },
                {
                    "type": "remote",
                    "tag": "geosite-ir",
                    "url": "https://testingcf.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@sing/geo/geosite/category-ir.srs",
                    "download_detour": "direct"
                },
                {
                    "type": "remote",
                    "tag": "geoip-private",
                    "url": "https://testingcf.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@sing/geo/geoip/private.srs",
                    "download_detour": "direct"
                },
                {
                    "type": "remote",
                    "tag": "geoip-ir",
                    "url": "https://testingcf.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@sing/geo/geoip/ir.srs",
                    "download_detour": "direct"
                }
            ],
            "final": "select",
            "auto_detect_interface": true,
            "default_domain_resolver": "local-dns"
        }
    }, null, 2);
};


const genClashForSingbox = (cfgs) => {
    const content = genClashForXray(cfgs);
    return content ? content.replace('Xray', 'Singbox') : null;
};

export default {
    async fetch(req, env) {
        const u = new URL(req.url);
        const o = req.headers.get('Origin');
        const h = cors(o);
        if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: h });
        try {
            if (u.pathname === '/' && req.method === 'GET') {
                return json({
                    status: 'V2V Pro v13 - Complete & Fast',
                    signature: 'V2V Signature System Active',
                    features: [
                        'Client-Side Real Testing',
                        'All Protocols Support (VMess, VLESS, Trojan, SS, Hy2, TUIC)',
                        'Smart Deduplication',
                        'Zero Errors Guaranteed',
                        'Batch Processing 50x',
                        'UUID V2V Signature'
                    ],
                    endpoints: {
                        xray: '/sub/xray/{id}',
                        'xray-clash': '/sub/xray-clash/{id}',
                        singbox: '/sub/singbox/{id}',
                        'singbox-clash': '/sub/singbox-clash/{id}'
                    }
                }, 200, h);
            }
            if (u.pathname === '/create-sub' && req.method === 'POST') {
                const { configs, format } = await req.json();
                if (!Array.isArray(configs) || !configs.length) {
                    return json({ error: 'Invalid configs array' }, 400, h);
                }
                const validFormats = ['xray', 'xray-clash', 'singbox', 'singbox-clash'];
                if (!validFormats.includes(format)) {
                    return json({ error: `Invalid format. Valid: ${validFormats.join(', ')}` }, 400, h);
                }
                const id = genV2VId();
                await env.v2v_kv.put(
                    `sub:${id}`,
                    JSON.stringify({ configs, format, created: Date.now() }),
                    { expirationTtl: TTL }
                );
                return json({
                    success: true,
                    id,
                    url: `${u.origin}/sub/${format}/${id}`,
                    total_configs: configs.length,
                    expires_in_days: 120
                }, 200, h);
            }
            const m = u.pathname.match(/^\/sub\/(xray|xray-clash|singbox|singbox-clash)\/(v2v[a-z0-9]+)$/);
            if (m && req.method === 'GET') {
                const [, fmt, id] = m;
                const d = await env.v2v_kv.get(`sub:${id}`, { type: 'json' });
                if (!d?.configs) {
                    return new Response('Subscription not found or expired', { status: 404, headers: h });
                }
                const { configs } = d;
                if (fmt === 'xray') {
                    const content = genXraySubscription(configs);
                    return text(content, 'text/plain', h, `V2V-Xray-${id}.txt`);
                }
                if (fmt === 'xray-clash') {
                    const content = genClashForXray(configs);
                    if (!content) return json({ error: 'No valid configs' }, 500, h);
                    return text(content, 'text/yaml', h, `V2V-Xray-Clash-${id}.yaml`);
                }
                if (fmt === 'singbox') {
                    const content = genSingboxSubscription(configs);
                    if (!content) return json({ error: 'No valid configs' }, 500, h);
                    return text(content, 'application/json', h, `V2V-Singbox-${id}.json`);
                }
                if (fmt === 'singbox-clash') {
                    const content = genClashForSingbox(configs);
                    if (!content) return json({ error: 'No valid configs' }, 500, h);
                    return text(content, 'text/yaml', h, `V2V-Singbox-Clash-${id}.yaml`);
                }
            }
            return new Response('Not Found', { status: 404, headers: h });
        } catch (e) {
            console.error('Worker Error:', e);
            return json({ error: e.message, stack: e.stack }, 500, h);
        }
    }
};
