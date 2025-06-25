import requests, base64, subprocess, json, os, re
from datetime import datetime

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DROPBOX_TOKEN = os.getenv("DROPBOX_ACCESS_TOKEN")

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def load_sources():
    try:
        with open("configs/config.txt", "r") as f:
            return [line.strip() for line in f if line.strip()]
    except Exception as e:
        print("Error loading config.txt:", e)
        return []

def fetch_configs(sources):
    links = []
    for url in sources:
        try:
            res = requests.get(url, headers=HEADERS, timeout=15)
            if res.status_code == 200:
                found = re.findall(r"(vmess://[^\s<>\"']+|vless://[^\s<>\"']+|trojan://[^\s<>\"']+|ss://[^\s<>\"']+)", res.text)
                links.extend(found)
        except Exception as e:
            print(f"⚠️ Error fetching {url}: {e}")
    return list(set(links))

def send_to_telegram(text):
    if not text.strip():
        text = "هیچ کانفیگ سالمی پیدا نشد."
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": text[:4096]}
    try:
        r = requests.post(url, data=data)
        print("Telegram:", r.status_code)
    except Exception as e:
        print("Telegram Error:", e)

def upload_to_dropbox(content):
    if not content.strip():
        print("Dropbox: Nothing to upload.")
        return
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
    sources = load_sources()
    links = fetch_configs(sources)
    print(f"Total found: {len(links)}")
    working = links  # (در نسخه‌های بعدی می‌شه اینجا تست واقعی زد)
    with open("configs/working.txt", "w") as f:
        f.write("\n".join(working))
    send_to_telegram("\n".join(working[:20]))
    upload_to_dropbox("\n".join(working))

if __name__ == "__main__":
    main()