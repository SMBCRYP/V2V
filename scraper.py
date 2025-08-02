import requests
import base64
import os
import json
import socket
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, unquote

# === CONFIGURATION ===
# لیست منابع پایه و معتبر ما
BASE_SOURCES = [
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/All_Configs_Sub.txt","https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub1.txt","https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub2.txt","https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub3.txt","https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub4.txt","https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub5.txt","https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub6.txt","https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub7.txt","https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub8.txt","https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt","https://raw.githubusercontent.com/MrPooyaX/V2Ray/main/sub/mix","https://raw.githubusercontent.com/yebekhe/Configura/main/Sub/Normal/Sub.txt","https://raw.githubusercontent.com/soroushmirzaei/V2Ray-configs/main/All-Configs-base64","https://raw.githubusercontent.com/mrvcoder/V2rayCollector/main/sub/mix_base64","https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/all.txt","https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/mixed_iran.txt","https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/main/All-Configs-for-V2Ray.txt","https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/sub/subscription_base64.txt","https://raw.githubusercontent.com/Argh94/V2RayAutoConfig/main/sub/sub_merge.txt","https://raw.githubusercontent.com/NiREvil/vless/main/sub/vless.txt","https://raw.githubusercontent.com/NiREvil/vless/main/XRAY/vless.txt","https://raw.githubusercontent.com/4n0nymou3/multi-proxy-config-fetcher/main/configs/proxy_configs.txt","https://raw.githubusercontent.com/MahsaNetConfigTopic/config/main/xray_final.txt"
]
# کلمات کلیدی برای جستجوی منابع جدید در گیت‌هاب
GITHUB_SEARCH_KEYWORDS = ['v2ray subscription', 'vless subscription', 'vmess subscription', 'iran v2ray']
# تعداد کانفیگ‌های برتر برای ذخیره نهایی
TOP_N_CONFIGS = 500
# نام فایل خروجی
OUTPUT_FILE = 'configs.txt'
# پیشوندهای معتبر
VALID_PREFIXES = ('vless://', 'vmess://', 'trojan://', 'ss://')

# === SECRET KEYS ===
GITLAB_SNIPPET_ID = os.environ.get('GITLAB_SNIPPET_ID')
GITLAB_API_TOKEN = os.environ.get('GITLAB_API_TOKEN')
GITHUB_PAT = os.environ.get('GH_PAT')


# === HELPER FUNCTIONS ===
def get_content_from_url(url: str) -> str | None:
    try:
        response = requests.get(url, timeout=10, headers={'User-Agent': 'V2V-Scraper/3.0'})
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        return None

def decode_content(content: str) -> list[str]:
    try:
        return base64.b64decode(content).decode('utf-8').strip().splitlines()
    except Exception:
        return content.strip().splitlines()

def discover_github_sources() -> set[str]:
    print("\n🔍 Discovering new sources from GitHub...")
    if not GITHUB_PAT:
        print("⚠️ GitHub PAT not found. Skipping discovery.")
        return set()

    headers = {'Authorization': f'token {GITHUB_PAT}'}
    discovered_urls = set()
    
    for keyword in GITHUB_SEARCH_KEYWORDS:
        params = {'q': keyword, 'sort': 'updated', 'per_page': 10}
        try:
            response = requests.get("https://api.github.com/search/repositories", headers=headers, params=params, timeout=20)
            response.raise_for_status()
            repos = response.json().get('items', [])
            
            for repo in repos:
                repo_name = repo['full_name']
                print(f"  -> Scanning repo: {repo_name}")
                # Simple heuristic: check for common filenames
                for filename in ['sub.txt', 'all.txt', 'vless.txt', 'vmess.txt']:
                    raw_url = f"https://raw.githubusercontent.com/{repo_name}/{repo['default_branch']}/{filename}"
                    discovered_urls.add(raw_url)
        except requests.RequestException as e:
            print(f"  -> Error searching GitHub for '{keyword}': {e}")
            
    print(f"✅ Discovered {len(discovered_urls)} potential new source URLs.")
    return discovered_urls

def parse_config(config_url: str) -> tuple[str, int] | None:
    try:
        if config_url.startswith('vmess://'):
            data = json.loads(base64.b64decode(config_url[8:]).decode())
            return data.get('add'), int(data.get('port', 0))
        parsed_url = urlparse(config_url)
        return parsed_url.hostname, parsed_url.port
    except Exception:
        return None

def tcp_ping(host: str, port: int, timeout: int = 2) -> int | None:
    if not host or not port:
        return None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        start_time = time.time()
        s.connect((host, port))
        end_time = time.time()
        s.close()
        return int((end_time - start_time) * 1000)
    except Exception:
        return None

def test_config_latency(config: str) -> tuple[str, int] | None:
    parsed = parse_config(config)
    if parsed:
        host, port = parsed
        latency = tcp_ping(host, port)
        if latency is not None:
            return (config, latency)
    return None

def upload_to_gitlab(content: str):
    # ... (implementation from previous step, no changes needed)
    if not GITLAB_API_TOKEN:
        print("GitLab API token not found. Skipping upload.")
        return

    headers = {"PRIVATE-TOKEN": GITLAB_API_TOKEN}
    data = {'title': 'V2V Configs Mirror', 'file_name': OUTPUT_FILE, 'content': content, 'visibility': 'public'}
    
    if GITLAB_SNIPPET_ID:
        url = f"https://gitlab.com/api/v4/snippets/{GITLAB_SNIPPET_ID}"
        response = requests.put(url, headers=headers, data=data)
        if response.status_code == 200:
            print(f"✅ Successfully updated GitLab snippet: {response.json()['web_url']}")
        else:
            print(f"❌ Failed to update GitLab snippet: {response.status_code} {response.text}")
    else:
        url = "https://gitlab.com/api/v4/snippets"
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 201:
            snippet_id = response.json()['id']
            print(f"✅ Successfully created GitLab snippet: {response.json()['web_url']}")
            print(f"📌 IMPORTANT: Add this ID to your GitHub secrets as GITLAB_SNIPPET_ID: {snippet_id}")
        else:
            print(f"❌ Failed to create GitLab snippet: {response.status_code} {response.text}")

# === MAIN EXECUTION ===
def main():
    # 1. Discover and combine sources
    all_sources = set(BASE_SOURCES)
    discovered_sources = discover_github_sources()
    all_sources.update(discovered_sources)
    print(f"\n 총 {len(all_sources)} sources to process.")

    # 2. Fetch all configs in parallel
    print("\n🚚 Fetching configs from all sources...")
    all_configs = set()
    with ThreadPoolExecutor(max_workers=20) as executor:
        for result in executor.map(get_content_from_url, all_sources):
            if result:
                for config in decode_content(result):
                    if config.strip().startswith(VALID_PREFIXES):
                        all_configs.add(config.strip())
    print(f"Found {len(all_configs)} unique configs.")

    # 3. Test latency of all configs in parallel
    print("\n⚡️ Testing latency of configs (this may take a while)...")
    working_configs = []
    with ThreadPoolExecutor(max_workers=50) as executor:
        for result in executor.map(test_config_latency, all_configs):
            if result:
                working_configs.append(result)
    print(f"Found {len(working_configs)} responsive configs.")

    # 4. Sort by latency and take the top N
    working_configs.sort(key=lambda x: x[1])
    top_configs = [cfg for cfg, lat in working_configs[:TOP_N_CONFIGS]]
    print(f"🏅 Selected top {len(top_configs)} configs.")

    if not top_configs:
        print("No working configs found. Aborting.")
        return

    final_content = "\n".join(top_configs)

    # 5. Save to local file for GitHub
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(final_content)
    print(f"💾 Successfully saved configs to {OUTPUT_FILE}")

    # 6. Upload to GitLab mirror
    upload_to_gitlab(final_content)

if __name__ == "__main__":
    main()
