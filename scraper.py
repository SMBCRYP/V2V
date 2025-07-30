import requests
import base64
import json
from urllib.parse import urlparse
from typing import List, Set, Dict, Any

SOURCES = [
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/MrPooyaX/V2Ray/main/sub/mix",
    "https://raw.githubusercontent.com/yebekhe/Configura/main/Sub/Normal/Sub.txt",
    "https://raw.githubusercontent.com/soroushmirzaei/V2Ray-configs/main/All-Configs-base64",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/All_Configs_Sub.txt",
]

OUTPUT_FILE = 'configs.json'
VALID_PREFIXES = ('vless://', 'vmess://', 'trojan://', 'ss://')

def get_server_info(address: str) -> Dict[str, Any]:
    try:
        response = requests.get(f"http://ip-api.com/json/{address.split(':')[0]}?fields=status,country,countryCode,isp", timeout=3)
        if response.status_code == 200 and response.json().get('status') == 'success':
            data = response.json()
            return {'country': data.get('country', 'N/A'), 'country_code': data.get('countryCode', '').lower(), 'isp': data.get('isp', 'N/A')}
    except Exception: pass
    return {'country': 'Unknown', 'country_code': '', 'isp': 'Unknown'}

def parse_config(uri: str):
    try:
        if not uri or not uri.startswith(VALID_PREFIXES) or not urlparse(uri).hostname: return None
        parsed_uri = urlparse(uri)
        server_info = get_server_info(parsed_uri.hostname)
        return {'protocol': parsed_uri.scheme, 'address': parsed_uri.hostname, 'port': parsed_uri.port or 0, 'remarks': parsed_uri.fragment.strip() or 'Config', **server_info, 'config_str': uri}
    except Exception: return None

def main():
    all_configs: Set[str] = set()
    for url in SOURCES:
        try:
            content = requests.get(url, timeout=10).text
            if "All_Configs_Sub" in url:
                for sub_link in content.strip().splitlines():
                    try:
                        sub_content = requests.get(sub_link, timeout=10).text
                        all_configs.update(base64.b64decode(sub_content).decode('utf-8').strip().splitlines())
                    except Exception: continue
            else:
                try: all_configs.update(base64.b64decode(content).decode('utf-8').strip().splitlines())
                except Exception: all_configs.update(content.strip().splitlines())
        except Exception as e: print(f"Could not process config source {url}: {e}")
            
    parsed_configs = [p for uri in all_configs if (p := parse_config(uri))]
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(parsed_configs, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
