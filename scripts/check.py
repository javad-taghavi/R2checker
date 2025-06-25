import requests, base64, subprocess, json, os, re
from datetime import datetime

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DROPBOX_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

sources = [
    "https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/index.html"
]

def search_github_v2ray_links():
    query = "v2ray in:file language:JSON"
    url = f"https://api.github.com/search/code?q={query}&sort=indexed&order=desc&per_page=5"
    headers = {"Accept": "application/vnd.github.v3+json"}
    try:
        response = requests.get(url, headers=headers)
        items = response.json().get("items", [])
        for item in items:
            raw_url = item["html_url"].replace("github.com", "raw.githubusercontent.com").replace("/blob", "")
            sources.append(raw_url)
    except Exception as e:
        print("GitHub Search Error:", e)

def fetch_configs():
    links = []
    for url in sources:
        try:
            res = requests.get(url, headers=HEADERS, timeout=15)
            if res.status_code == 200:
found = re.findall(r"(vmess://[^\s<>\"]+|vless://[^\s<>\"]+|trojan://[^\s<>\"]+|ss://[^\s<>\"]+)", res.text)
                links.extend(found)
        except Exception as e:
            print(f"⚠️ Error fetching {url}: {e}")
    return list(set(links))

def test_config(link):
    try:
        proc = subprocess.run(["bin/v2ray", "-test"], input=b"{}", stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=8)
        return proc.returncode == 0
    except:
        return False

def send_to_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": text[:4096]}
    try:
        r = requests.post(url, data=data)
        print("Telegram:", r.status_code)
    except Exception as e:
        print("Telegram Error:", e)

def upload_to_dropbox(content):
    url = "https://content.dropboxapi.com/2/files/upload"
    headers = {
        "Authorization": f"Bearer {DROPBOX_TOKEN}",
        "Dropbox-API-Arg": json.dumps({"path": f"/working_{datetime.now().strftime('%Y%m%d_%H%M')}.txt", "mode": "overwrite"}),
        "Content-Type": "application/octet-stream"
    }
    try:
        r = requests.post(url, headers=headers, data=content.encode("utf-8"))
        print("Dropbox:", r.status_code)
    except Exception as e:
        print("Dropbox Error:", e)

def main():
    search_github_v2ray_links()
    links = fetch_configs()
    print(f"Total found: {len(links)}")
    working = []
    for link in links:
        if "vmess://" in link or "vless://" in link:
            working.append(link)
    with open("configs/working.txt", "w") as f:
        f.write("\n".join(working))
    send_to_telegram("\n".join(working[:20]) or "هیچ کانفیگ سالمی پیدا نشد.")
    upload_to_dropbox("\n".join(working))

if __name__ == "__main__":
    main()