import requests
import base64
from typing import List, Set

# لیست کامل منابع ما در اینجا قرار دارد
SOURCES = [
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/All_Configs_Sub.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub1.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub2.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub3.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub4.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub5.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub6.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub7.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub8.txt",
    "https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/MrPooyaX/V2Ray/main/sub/mix",
    "https://raw.githubusercontent.com/yebekhe/Configura/main/Sub/Normal/Sub.txt",
    "https://raw.githubusercontent.com/soroushmirzaei/V2Ray-configs/main/All-Configs-base64",
    "https://raw.githubusercontent.com/mrvcoder/V2rayCollector/main/sub/mix_base64",
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/all.txt",
    "https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/mixed_iran.txt",
    "https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/main/All-Configs-for-V2Ray.txt",
    "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/sub/subscription_base64.txt",
    "https://raw.githubusercontent.com/Argh94/V2RayAutoConfig/main/sub/sub_merge.txt",
    "https://raw.githubusercontent.com/NiREvil/vless/main/sub/vless.txt",
    "https://raw.githubusercontent.com/NiREvil/vless/main/XRAY/vless.txt",
    "https://raw.githubusercontent.com/4n0nymou3/multi-proxy-config-fetcher/refs/heads/main/configs/proxy_configs.txt",
    "https://raw.githubusercontent.com/MahsaNetConfigTopic/config/refs/heads/main/xray_final.txt"
]

OUTPUT_FILE = 'configs.txt'
VALID_PREFIXES = ('vless://', 'vmess://', 'trojan://', 'ss://')

def get_content_from_url(url: str) -> str | None:
    """Fetches content from a URL with a timeout."""
    try:
        response = requests.get(url, timeout=10, headers={'User-Agent': 'V2V-Scraper'})
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Could not fetch {url}: {e}")
        return None

def decode_content(content: str) -> List[str]:
    """Decodes content (tries base64 first, then falls back to plain text)."""
    try:
        decoded_bytes = base64.b64decode(content)
        return decoded_bytes.decode('utf-8').strip().splitlines()
    except Exception:
        return content.strip().splitlines()

def main():
    """Main function to fetch, process, and save all configs."""
    all_configs: Set[str] = set()
    total_sources = len(SOURCES)
    
    print(f"Starting to process {total_sources} sources...")

    for i, url in enumerate(SOURCES):
        print(f"[{i+1}/{total_sources}] Processing: {url}")
        content = get_content_from_url(url)
        if content:
            configs = decode_content(content)
            for config in configs:
                clean_config = config.strip()
                if clean_config and clean_config.startswith(VALID_PREFIXES):
                    all_configs.add(clean_config)

    print(f"\nFound a total of {len(all_configs)} unique configs.")

    if not all_configs:
        print("No configs found, not updating the file.")
        return

    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            for config in sorted(list(all_configs)):
                f.write(config + '\n')
        print(f"Successfully saved all configs to {OUTPUT_FILE}")
    except IOError as e:
        print(f"Error writing to file: {e}")

if __name__ == "__main__":
    main()
