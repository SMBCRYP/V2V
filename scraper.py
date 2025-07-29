import requests
import base64
from typing import List, Set

# A curated list of raw text and subscription link sources
SOURCES = [
    # Barry-far Subs
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub1.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub2.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub3.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub4.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub5.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub6.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub7.txt",
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub8.txt",
    # Epodonios
    "https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/all.txt",
    # youfoundamin
    "https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/mixed_iran.txt",
    # MatinGhanbari
    "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/sub/subscription_base64.txt",
    # V2rayCollector by mrvcoder
    "https://raw.githubusercontent.com/mrvcoder/V2rayCollector/main/sub/mix_base64",
]

OUTPUT_FILE = 'configs.txt'
VALID_PREFIXES = ('vless://', 'vmess://', 'trojan://', 'ss://')


def get_content_from_url(url: str):
    """Fetches content from a URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Could not fetch {url}: {e}")
        return None


def decode_content(content: str) -> List[str]:
    """Decodes content (tries base64 first, then falls back to plain text)."""
    try:
        decoded_bytes = base64.b64decode(content)
        return decoded_bytes.decode('utf-8').strip().split('\n')
    except (ValueError, TypeError, base64.binascii.Error):
        return content.strip().split('\n')


def main():
    """
    Main function to fetch, process, and save all configs.
    """
    all_configs: Set[str] = set()
    total_sources = len(SOURCES)
    
    print(f"Starting to process {total_sources} sources...")

    for i, url in enumerate(SOURCES):
        print(f"[{i+1}/{total_sources}] Processing: {url}")
        content = get_content_from_url(url)
        if content:
            configs = decode_content(content)
            for config in configs:
                if config and config.startswith(VALID_PREFIXES):
                    all_configs.add(config)

    print(f"\nFound a total of {len(all_configs)} unique configs.")

    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            for config in sorted(list(all_configs)):
                f.write(config + '\n')
        print(f"Successfully saved all configs to {OUTPUT_FILE}")
    except IOError as e:
        print(f"Error writing to file: {e}")


if __name__ == "__main__":
    main()
