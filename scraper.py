import requests
import base64
import json
from urllib.parse import urlparse
from typing import List, Set, Dict, Any

SOURCES = [
    # Add your list of subscription links here
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub1.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub2.txt",
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/all.txt",
    "https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/mixed_iran.txt",
    "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/sub/subscription_base64.txt",
    "https://raw.githubusercontent.com/mrvcoder/V2rayCollector/main/sub/mix_base64",
]

OUTPUT_FILE = 'configs.json'
VALID_PREFIXES = ('vless://', 'vmess://', 'trojan://')

# Cache for server info to avoid repeated API calls
server_info_cache: Dict[str, Dict[str, Any]] = {}

def get_server_info(address: str) -> Dict[str, Any]:
    """Fetches location and ISP info for a server address using a free API."""
    ip = address.split(':')[0]
    if ip in server_info_cache:
        return server_info_cache[ip]
    
    try:
        response = requests.get(f"http://ip-api.com/json/{ip}?fields=status,country,countryCode,isp", timeout=5)
        response.raise_for_status()
        data = response.json()
        if data.get('status') == 'success':
            info = {
                'country': data.get('country', 'Unknown'),
                'country_code': data.get('countryCode', ''),
                'isp': data.get('isp', 'Unknown')
            }
            server_info_cache[ip] = info
            return info
    except Exception as e:
        print(f"GeoIP lookup failed for {ip}: {e}")
    
    return {'country': 'Unknown', 'country_code': '', 'isp': 'Unknown'}

def parse_config(uri: str):
    """Parses a V2Ray URI and extracts its details."""
    try:
        if not uri.startswith(VALID_PREFIXES):
            return None

        parsed_uri = urlparse(uri)
        protocol = parsed_uri.scheme
        address = parsed_uri.hostname or ''
        port = parsed_uri.port or 0
        remarks = parsed_uri.fragment or 'Config'
        
        server_info = get_server_info(address)

        return {
            'protocol': protocol,
            'address': address,
            'port': port,
            'remarks': remarks.strip(),
            'country': server_info['country'],
            'country_code': server_info['country_code'].lower(),
            'isp': server_info['isp'],
            'config_str': uri
        }
    except Exception:
        return None

def main():
    """Main function to fetch, process, and save all configs."""
    all_configs: Set[str] = set()
    print(f"Processing {len(SOURCES)} sources...")

    for url in SOURCES:
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            content = response.text
            
            try:
                decoded = base64.b64decode(content).decode('utf-8')
                all_configs.update(decoded.strip().split('\n'))
            except Exception:
                all_configs.update(content.strip().split('\n'))
        except requests.RequestException as e:
            print(f"Could not fetch {url}: {e}")

    parsed_configs: List[Dict[str, Any]] = []
    print(f"Found {len(all_configs)} total configs, parsing and analyzing...")

    for uri in all_configs:
        parsed_data = parse_config(uri)
        if parsed_data:
            parsed_configs.append(parsed_data)
    
    print(f"Successfully parsed {len(parsed_configs)} valid configs.")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(parsed_configs, f, indent=2, ensure_ascii=False)
    
    print(f"Saved configs to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
