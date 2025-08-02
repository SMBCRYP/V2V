import requests
import base64
import os
from typing import List, Set

# لیست منابع ثابت ما
SOURCES = [
    "https://raw.githubusercontent.com/barry-far/V2ray-Config/main/All_Configs_Sub.txt","https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub1.txt","https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub2.txt","https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub3.txt","https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub4.txt","https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub5.txt","https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub6.txt","https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub7.txt","https://raw.githubusercontent.com/barry-far/V2ray-Config/main/Sub8.txt","https://raw.githubusercontent.com/mahdibland/V2RayAggregator/master/sub/sub_merge.txt","https://raw.githubusercontent.com/MrPooyaX/V2Ray/main/sub/mix","https://raw.githubusercontent.com/yebekhe/Configura/main/Sub/Normal/Sub.txt","https://raw.githubusercontent.com/soroushmirzaei/V2Ray-configs/main/All-Configs-base64","https://raw.githubusercontent.com/mrvcoder/V2rayCollector/main/sub/mix_base64","https://raw.githubusercontent.com/Epodonios/v2ray-configs/main/all.txt","https://raw.githubusercontent.com/youfoundamin/V2rayCollector/main/mixed_iran.txt","https://raw.githubusercontent.com/SoliSpirit/v2ray-configs/main/All-Configs-for-V2Ray.txt","https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/sub/subscription_base64.txt","https://raw.githubusercontent.com/Argh94/V2RayAutoConfig/main/sub/sub_merge.txt","https://raw.githubusercontent.com/NiREvil/vless/main/sub/vless.txt","https://raw.githubusercontent.com/NiREvil/vless/main/XRAY/vless.txt","https://raw.githubusercontent.com/4n0nymou3/multi-proxy-config-fetcher/main/configs/proxy_configs.txt","https://raw.githubusercontent.com/MahsaNetConfigTopic/config/main/xray_final.txt"
]

OUTPUT_FILE = 'configs.txt'
GITLAB_SNIPPET_ID = os.environ.get('GITLAB_SNIPPET_ID')
GITLAB_API_TOKEN = os.environ.get('GITLAB_API_TOKEN')
VALID_PREFIXES = ('vless://', 'vmess://', 'trojan://', 'ss://')

def get_content_from_url(url: str) -> str | None:
    try:
        response = requests.get(url, timeout=10, headers={'User-Agent': 'V2V-Scraper'})
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Could not fetch {url}: {e}")
        return None

def decode_content(content: str) -> List[str]:
    try:
        decoded_bytes = base64.b64decode(content)
        return decoded_bytes.decode('utf-8').strip().splitlines()
    except Exception:
        return content.strip().splitlines()

def upload_to_gitlab(content: str):
    if not GITLAB_API_TOKEN:
        print("GitLab API token not found. Skipping upload.")
        return

    headers = {"PRIVATE-TOKEN": GITLAB_API_TOKEN}
    
    # Data for creating a new snippet or updating an existing one
    data = {
        'title': 'V2V Configs Mirror',
        'file_name': OUTPUT_FILE,
        'content': content,
        'visibility': 'public',
    }
    
    if GITLAB_SNIPPET_ID:
        # Update existing snippet
        url = f"https://gitlab.com/api/v4/snippets/{GITLAB_SNIPPET_ID}"
        response = requests.put(url, headers=headers, data=data)
        if response.status_code == 200:
            print(f"Successfully updated GitLab snippet: {response.json()['web_url']}")
        else:
            print(f"Failed to update GitLab snippet: {response.status_code} {response.text}")
    else:
        # Create new snippet
        url = "https://gitlab.com/api/v4/snippets"
        response = requests.post(url, headers=headers, data=data)
        if response.status_code == 201:
            snippet_id = response.json()['id']
            print(f"Successfully created GitLab snippet: {response.json()['web_url']}")
            print(f"IMPORTANT: Add this ID to your GitHub secrets as GITLAB_SNIPPET_ID: {snippet_id}")
        else:
            print(f"Failed to create GitLab snippet: {response.status_code} {response.text}")


def main():
    all_configs: Set[str] = set()
    for url in SOURCES:
        content = get_content_from_url(url)
        if content:
            configs = decode_content(content)
            for config in configs:
                clean_config = config.strip()
                if clean_config and clean_config.startswith(VALID_PREFIXES):
                    all_configs.add(clean_config)

    if not all_configs:
        print("No configs found. Aborting.")
        return

    final_content = "\n".join(sorted(list(all_configs)))

    # Save to local file for GitHub auto-commit
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(final_content)
    print(f"Successfully saved {len(all_configs)} configs to {OUTPUT_FILE}")

    # Upload to GitLab
    upload_to_gitlab(final_content)

if __name__ == "__main__":
    main()
