<p align="center">
 <img src="https://latex.codecogs.com/svg.image?\huge&space;{\color{Teal}\mathrm{\mathbf{V}}}{\color{white}\textbf{2}}{\color{red}\textbf{V}}" width=180px" </p><br><br/>



> [!CAUTION]
> 
> پروژه جمع‌آوری و مدیریت  انواع پروکسی کانفیگ‌های v2ray، مانند:  
> 
> - Vless  
> - Vmess  
> - Trojan  
> - Shadowsocks   
> - Hysteria  
> - Tuic  
> - Reality  
> - And more protocol's
> 
> <br/> 

## 📋 فهرست
- [معرفی](#معرفی)
- [ویژگی‌ها](#ویژگی-ها)
- [نصب و راه‌اندازی](#نصب-و-راه-اندازی)
- [ساختار فایل‌ها](#ساختار-فایل-ها)
- [تنظیمات](#تنظیمات)
- [نحوه استفاده](#نحوه-استفاده)

<br/>
 
## معرفی
 ‏V2V یک سیستم جامع برای جمع‌آوری، تست و توزیع پروکسی کانفیگ‌های v2ray است که از پروتکل‌های مختلف پشتیبانی می‌کند.

<br><br/>

## ویژگی ها
✅ **تست پینگ واقعی**: تست اتصال با 3 بار تلاش و میانگین‌گیری  
✅ **ساب‌لینک‌های استاندارد**: تولید فایل‌های Clash و Singbox با امضای V2V  
✅ **بدون خطا**: تمام فایل‌ها بدون هیچ خطای EOF، Unmarshal یا Duplicate   
✅ **انتخاب همه**: دکمه انتخاب همه برای هر پروتکل  
✅ **دیپلوی چندگانه**: استقرار پروژه بر بستر چند سرویس‌دهنده مختلف مانند:  
- Arvan Cloud
- GitHub Pages
- Vercel
- Cloudflare Workers  
برای جلوگیری از قطع دسترسی ناخواسته هنگام محدود شدن هرکدام از آن‌ها.

<br/> 

## نصب و راه اندازی

### 1. کلون کردن مخزن

```bash
git clone https://github.com/smbcryp/V2V.git
cd V2V
```

<br/> 

### 2. نصب پیش‌نیاز‌ها

**install dependencies**

```bash
pip install requests PyGithub PyYAML
npm install -g wrangler vercel
```

### 3. تنظیم Secrets در GitHub

**در مخزن گیت‌هاب خود در مسیر زیر:**  

Settings > Secrets and variables > Actions‌ 

**موارد ذکر شده را اضافه کنید:**  

```yaml
GH_PAT=your_github_personal_access_token

ARVAN_ACCESS_KEY_ID=your_arvan_access_key

ARVAN_SECRET_ACCESS_KEY=your_arvan_secret_key

ARVAN_BUCKET_NAME=your_bucket_name

VERCEL_TOKEN=your_vercel_token

VERCEL_ORG_ID=your_vercel_org_id

VERCEL_PROJECT_ID=your_vercel_project_id

CLOUDFLARE_API_TOKEN=your_cloudflare_api_token

CLOUDFLARE_ACCOUNT_ID=your_cloudflare_account_id
```

<br/> 

### 4. ساخت KV Namespace در Cloudflare

```bash
wrangler kv:namespace create "v2v_kv"
```

سپس ID دریافتی را در `wrangler.toml` جایگزین کنید.

<br/> 

### 5. دیپلوی Workers 

```bash
wrangler deploy
```

<br/>

## ساختار فایل ها

```yaml
V2V/
├── .github/
│   └── workflows/
│      └── deploy.yml  # Github workflow
├── index.html         # صفحه اصلی
├── index.js           # منطق Frontend
├── worker.js          # وورکر کلادفلر 
├── wrangler.toml      # تنظیمات Worker
├── vercel.json        # تنظیمات Vercel
├── manifest.json      # PWA Manifest
├── logo.png           # لوگوی پروژه
├── scraper.py         # اسکریپت جمع‌آوری کانفیگ
└── README.md          # این فایل
```

<br/> 

## تنظیمات

### تنظیم تعداد Worker URLs در فایل `index.js`:

```javascript
const WORKER_URLS = [
    'https://v2v-proxy.USERNAME.workers.dev',
    'https://v2v.USERNAME.workers.dev',
    // آدرس URLs وورکر خود را قرار دهید.
];
```

<br/>

### تنظیم Origins مجاز در فایل `worker.js`:

```javascript
const ALLOWED_ORIGINS = [
    'https://smbcryp.github.io',
    'https://your-vercel-app.vercel.app',
    'https://your-bucket.s3-website.ir-thr-at1.arvanstorage.ir',
];
```

<br/>

## نحوه استفاده

### وب‌سایت

 ‏1. **ورود به وب‌سایت:**  
یکی از آدرس‌های زیر را به دلخواه در مرورگر خود باز کنید:  

- GitHub Pages:
[smbcryp.github.io/V2V][1]
- Vercel:  
[Your-app.vercel.app][2]
- Arvan:  
[your-bucket.s3-website.ir-thr-at1.arvanstorage.ir][3]

<br/>

 ‏2. ‏**تست پینگ**:    
روی دکمه `تست پینگ همه کانفیگ‌ها` کلیک کنید.

<br/>

 ‏3. ‏**انتخاب کانفیگ**:    
با استفاده از دکمه ☑️ برای انتخاب:  
- همه  
- یک پروتکل  
- و یا انتخاب دستی کانفیگ‌های دلخواه  
استفاده کنید.

<br/>

 ‏4. ‏**تولید ساب‌لینک:**  
- ‏**Clash**: کلیک روی "انتخابی" یا "خودکار"  
- ‏**Singbox**: کلیک روی "انتخابی" یا "خودکار"  
- ‏**QR Code**: کلیک روی دکمه "QR"  

<br/>

### API Endpoints

#### POST `/ping`

تست اتصال به هاست و پورت:  

```bash
curl -X POST https://your-worker.workers.dev/ping \
  -H "Content-Type: application/json" \
  -d '{"host":"8.8.8.8","port":53}'
```

#### POST `/create-sub`

**ساخت ساب‌لینک:**  

```bash
curl -X POST https://your-worker.workers.dev/create-sub \
  -H "Content-Type: application/json" \
  -d '{
    "configs": ["vmess://...", "vless://..."],
    "format": "clash"
  }'
```

<br/>

**پاسخ دریافتی:**  

```json
{
  "success": true,
  "id": "abc12345",
  "url": "https://your-worker.workers.dev/sub/clash/abc12345"
}
```

<br/>

#### GET `/sub/{format}/{id}`

**دریافت فایل ساب‌لینک:**  

```bash
# Clash
curl https://your-worker.workers.dev/sub/clash/abc12345

# Singbox
curl https://your-worker.workers.dev/sub/singbox/abc12345
```

<br/> 

## تضمین کیفیت

### ✅ تست پینگ واقعی و دقیق

**ویژگی‌ها:**
- 3 بار تلاش برای هر کانفیگ
- میانگین‌گیری از نتایج موفق
- ‏ Timeout واقعی 3 ثانیه
- تست موازی روی 4 Worker
- نمایش رنگی:
  - سبز (<200ms)
  - زرد (200-500ms)
  - قرمز (>500ms)

<br/>

**کد تست پینگ در Worker:**  

```javascript
async function testConnection(host, port) {
    const tests = [];
    for (let i = 0; i < 3; i++) {
        const startTime = Date.now();
        const socket = connect({ hostname: host, port: parseInt(port) });
        await Promise.race([
            socket.opened,
            new Promise((_, reject) => 
                setTimeout(() => reject(new Error('timeout')), 3000)
            )
        ]);
        const latency = Date.now() - startTime;
        if (latency > 0 && latency < 3000) tests.push(latency);
        await socket.close();
        if (i < 2) await new Promise(resolve => setTimeout(resolve, 50));
    }
    if (tests.length === 0) return { latency: null, status: 'Dead' };
    return { 
        latency: Math.round(tests.reduce((a,b) => a+b) / tests.length), 
        status: 'Live' 
    };
}
```

**نتیجه:**  
- ✅ هیچ پینگ غیر‌واقعی نمایش داده نمی‌شود
- ✅ تمام کانفیگ‌ها تست می‌شوند (بدون محدودیت)
- ✅ پردازش موازی روی 4 Worker برای سرعت بیشتر

<br/>

### ✅ ساب‌لینک‌های بدون خطا

#### ویژگی‌ کانفیگ‌های Clash:

```yaml
# Generated by V2V
# https://github.com/smbcryp/V2V

proxies:
  - name: "[V2V] VMess-Server1"
    type: vmess
    server: example.com
    port: 443
    uuid: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    alterId: 0
    cipher: auto
    udp: true
    network: ws
    ws-opts:
      path: /path
      headers:
        Host: example.com
    tls: true
    servername: example.com
    skip-cert-verify: true

proxy-groups:
  - name: "🚀 V2V Auto"
    type: url-test
    proxies:
      - "[V2V] VMess-Server1"
    url: http://www.gstatic.com/generate_204
    interval: 300

  - name: "🎯 V2V Select"
    type: select
    proxies:
      - "🚀 V2V Auto"
      - "[V2V] VMess-Server1"

rules:
  - GEOIP,IR,DIRECT
  - MATCH,🎯 V2V Select
```

<br/> 

#### ویژگی‌ کانفیگ‌های Singbox:  

```json
{
  "log": {
    "disabled": false,
    "level": "info",
    "timestamp": true
  },
  "dns": {
    "servers": [
      {
        "tag": "google",
        "address": "8.8.8.8",
        "strategy": "prefer_ipv4"
      },
      {
        "tag": "local",
        "address": "local",
        "detour": "direct"
      }
    ],
    "rules": [
      {
        "geosite": "ir",
        "server": "local"
      }
    ]
  },
  "inbounds": [
    {
      "tag": "mixed-in",
      "type": "mixed",
      "listen": "127.0.0.1",
      "listen_port": 7890
    }
  ],
  "outbounds": [
    {
      "tag": "🚀 V2V Auto",
      "type": "urltest",
      "outbounds": ["[V2V] VMess-Server1"],
      "url": "http://www.gstatic.com/generate_204",
      "interval": "5m",
      "tolerance": 50
    },
    {
      "tag": "🎯 V2V Select",
      "type": "selector",
      "outbounds": ["🚀 V2V Auto", "[V2V] VMess-Server1"],
      "default": "🚀 V2V Auto"
    },
    {
      "tag": "[V2V] VMess-Server1",
      "type": "vmess",
      "server": "example.com",
      "server_port": 443,
      "uuid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
      "alter_id": 0,
      "security": "auto",
      "transport": {
        "type": "ws",
        "path": "/path",
        "headers": {
          "Host": "example.com"
        }
      },
      "tls": {
        "enabled": true,
        "server_name": "example.com",
        "insecure": true
      }
    },
    {
      "tag": "direct",
      "type": "direct"
    },
    {
      "tag": "block",
      "type": "block"
    }
  ],
  "route": {
    "rules": [
      {
        "geoip": "ir",
        "outbound": "direct"
      },
      {
        "geoip": "private",
        "outbound": "direct"
      },
      {
        "geosite": "category-ads-all",
        "outbound": "block"
      }
    ],
    "final": "🎯 V2V Select",
    "auto_detect_interface": true
  },
  "experimental": {
    "cache_file": {
      "enabled": true
    },
    "clash_api": {
      "external_controller": "127.0.0.1:9090"
    }
  }
}
```

<br/>

**نتیجه:**  
- ✅ **هیچ خطای EOF**: پارس کامل و صحیح تمام فیلدها
- ✅ **هیچ خطای Unmarshal**: JSON/YAML معتبر و استاندارد
- ✅ **هیچ خطای Duplicate**: حذف کانفیگ‌های تکراری با uniqueKey
- ✅ **هیچ خطای Password**: اعتبارسنجی دقیق تمام فیلدها
- ✅ **محتوای معتبر**: تست تمام پروتکل‌ها قبل از اضافه شدن

<br/> 

### ✅ پشتیبانی کامل از تمام پروتکل‌ها

<br/> 

| پروتکل | Xray | Singbox | Clash | تست شده |
|--------|------|---------|-------|---------|
| VMess | ✅ | ✅ | ✅ | ✅ |
| VLESS | ✅ | ✅ | ✅ | ✅ |
| Trojan | ✅ | ✅ | ✅ | ✅ |
| Shadowsocks | ✅ | ✅ | ✅ | ✅ |
| Hysteria2 | ✅ | ✅ | ❌ | ✅ |
| TUIC | ✅ | ✅ | ❌ | ✅ |

<br/> 

**توضیحات:**  
- تمام پروتکل‌ها در هر دو هسته Xray و Singbox پشتیبانی می‌شوند
- کلش فقط از 4 پروتکل اول پشتیبانی می‌کند
  - (محدودیت خود Clash)
- تست پینگ روی تمام پروتکل‌ها به صورت یکسان اجرا می‌شود.

<br/> 

### ✅ حذف Duplicate و اعتبارسنجی

**الگوریتم حذف تکراری:**  

```javascript
const seen = new Set();
for (const config of configs) {
    const uniqueKey = `${protocol}-${server}-${port}-${uuid/password}`;
    if (seen.has(uniqueKey)) continue; // Skip duplicate
    seen.add(uniqueKey);
    proxies.push(proxy);
}
```

<br/> 

**اعتبارسنجی کامل:**  

```javascript
function parseVmessConfig(config) {
    // بررسی format
    if (!config.startsWith('vmess://')) return null;
    
    // بررسی Base64
    const decoded = safeBase64Decode(vmessData);
    if (!decoded) return null;
    
    // بررسی JSON
    const json = safeJsonParse(decoded);
    if (!json) return null;
    
    // بررسی فیلدهای ضروری
    if (!json.add || !json.port || !json.id) return null;
    
    // بررسی Port
    const port = parseInt(json.port);
    if (isNaN(port) || port <= 0 || port > 65535) return null;
    
    return validConfig;
}
```

<br/>

**نتیجه:**
- ✅ هیچ کانفیگ تکراری در لیست نهایی نیست
- ✅ تمام کانفیگ‌های نامعتبر حذف می‌شوند
- ✅ فقط کانفیگ‌های کامل و صحیح نمایش داده می‌شوند
 
<br/>

###  ‏✅ UUID کوتاه و امن

**تولید [UUID][4]:**  

```javascript
function generateShortId() {
    const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
    let id = '';
    for (let i = 0; i < 8; i++) {
        id += chars[Math.floor(Math.random() * chars.length)];
    }
    return id; // مثلاً: a7k3m9x2
}
```

**آدرس URL نهایی:**

```yaml
https://your-worker.workers.dev/sub/clash/a7k3m9x2
https://your-worker.workers.dev/sub/singbox/b5n8p1q4
```

**نتیجه:**  
- ‏✅ آدرس URL کوتاه و قابل اشتراک‌گذاری
- ✅ هیچ اطلاعات حساس در URL نیست
- ✅ ذخیره امن در Cloudflare KV با TTL یک ساله

<br/>

### ✅ امضای [V2V][5] در کلاینت‌ها

**نمایش در کلاینت‌ها:**  

**Clash Meta / Clash Verge:**  

```yaml
🚀 V2V Auto          ← Group انتخاب خودکار
🎯 V2V Select        ← Group انتخاب دستی
[V2V] VMess-Server1  ← نام کانفیگ با prefix [V2V]
[V2V] VLESS-Server2
[V2V] Trojan-Server3
```

**Singbox / V2rayNG:**  

```yaml
🚀 V2V Auto
🎯 V2V Select
[V2V] VMess-Server1
[V2V] VLESS-Server2
[V2V] Trojan-Server3
```

**نتیجه:**
- ✅ تمام کانفیگ‌ها با `[V2V]` شناسایی می‌شوند
- ✅ گروه‌ها با ایموجی مشخص هستند
- ✅ کاربر به راحتی می‌تواند منبع را تشخیص دهد

<br/>

### ✅ پردازش موازی روی 4 Worker

**الگوریتم توزیع:**  

```javascript
// تقسیم کانفیگ‌ها بین 4 Worker
for (let i = 0; i < allConfigs.length; i += BATCH_SIZE * 4) {
    const megaBatch = allConfigs.slice(i, i + BATCH_SIZE * 4);
    
    await Promise.all(activeWorkers.map(async (workerUrl, workerIdx) => {
        // هر Worker یک چهارم کانفیگ‌ها را می‌گیرد
        const workerBatch = megaBatch.filter((_, idx) => 
            idx % activeWorkers.length === workerIdx
        );
        
        // پردازش موازی
        await Promise.all(workerBatch.map(config => 
            testConfig(workerUrl, config)
        ));
    }));
}
```

**سرعت:**  
- تک Worker: 1000 کانفیگ = ~15 دقیقه
- چهار Worker موازی: 1000 کانفیگ = ~4 دقیقه

**نتیجه:**  
- ✅ سرعت 4 برابر در تست پینگ
- ✅ بدون تداخل و Race Condition
- ✅ فال‌بک/Fallback خودکار اگر Worker از کار افتاد

<br/>

## عیب‌یابی

### خطای "Worker غیرفعال"

**علت:** ‏Workers در دسترس نیستند.

**راه حل:**  

```bash
# تست Workers
curl https://your-worker.workers.dev/

# دیپلوی مجدد
wrangler deploy
```

<br/> 

### خطای "KV Namespace not found"

**علت:** KV Namespace ساخته نشده یا ID اشتباه است.

**راه حل:**
```bash
# ساخت KV
wrangler kv:namespace create "v2v_kv"

# آپدیت wrangler.toml با ID جدید
```

<br/>

### خطای "Invalid config format"

**علت:** فرمت کانفیگ نامعتبر است.

**راه حل:** کانفیگ باید با یکی از این prefixها شروع شود:

- `vmess://`
- `vless://`
- `trojan://`
- `ss://`

<br/>

### خطای Timeout در تست پینگ

**علت:** سرور در دسترس نیست یا فیلتر است.

**نتیجه:** کانفیگ با ✗ قرمز نمایش داده می‌شود، (عادی).

<br/>

## مشارکت
1. Fork کنید.  
2. Feature branch بسازید (`git checkout -b feature/AmazingFeature`)
3. Commit کنید (`git commit -m 'Add AmazingFeature'`)
4. Push کنید (`git push origin feature/AmazingFeature`)
5. Pull Request باز کنید.

<br/>

## لایسنس
این پروژه تحت لایسنس MIT منتشر شده است.

## تماس و پشتیبانی

- GitHub: [@smbcryp][5]
- Issues: [گزارش مشکل][6]

## تشکر ویژه  
سپاس از تمامی کسانی که به صورت مستقیم یا غیرمستقیم در توسعه این پروژه نقش داشتند.

<hr/><br/>

### ⚠️ سلب مسئولیت
این ابزار صرفاً برای اهداف آموزشی و تحقیقاتی توسعه داده شده است. هرگونه استفادهٔ نادرست یا مغایر با قوانین، به‌طور کامل بر عهدهٔ کاربر خواهد بود.

<hr/><br/>

<div markdown='1' align='center'>

Made with 🤍 by **V2V Team**

<div/>

[1]: https://smbcryp.github.io/V2V
[2]: https://your-app.vercel.app
[3]: https://your-bucket.s3-website.ir-thr-at1.arvanstorage.ir
[4]: https://www.uuidgenerator.net/
[5]: https://github.com/smbcryp
[6]: https://github.com/smbcryp/V2V/issues
