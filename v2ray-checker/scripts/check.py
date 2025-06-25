import requests, base64, subprocess, json, os, re

TELEGRAM_CONFIG_PATH = "config.txt"

def fetch_from_github_search():
    configs = []
    try:
        search_url = "https://api.github.com/search/code"
        headers = {"Accept": "application/vnd.github.v3+json"}
        query = "v2ray vmess in:file extension:txt language:text"
        params = {"q": query, "sort": "indexed", "order": "desc", "per_page": 5}
        r = requests.get(search_url, headers=headers, params=params, timeout=10)
        items = r.json().get("items", [])
        for item in items:
            raw_url = item["html_url"].replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
            print(f"🔍 GitHub file: {raw_url}")
            res = requests.get(raw_url, timeout=10)
            matches = re.findall(r"(vmess|vless|trojan|ss):\/\/[^\s<>\"']+", res.text)
            configs.extend(matches)
    except Exception as e:
        print("❌ GitHub Search Error:", e)
    return configs

def fetch_configs():
    configs = []

    configs.extend(fetch_from_github_search())

    github_sources = [
        "https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/v2",
        "https://raw.githubusercontent.com/Alvin9999/new-pac/master/v2ray/free-v2ray",
        "https://raw.githubusercontent.com/Pawdroid/Free-servers/main/sub",
    ]

    for url in github_sources:
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            matches = re.findall(r"(vmess|vless|trojan|ss):\/\/[^\s<>\"']+", r.text)
            configs.extend(matches)
        except Exception as e:
            print(f"⚠️ Error fetching {url}: {e}")

    if os.path.exists(TELEGRAM_CONFIG_PATH):
        with open(TELEGRAM_CONFIG_PATH, "r") as f:
            configs.extend([line.strip() for line in f if any(proto in line for proto in ["vmess://", "vless://", "trojan://", "ss://"])])

    return list(set(configs))

def test_config(link):
    if link.startswith("vmess://"):
        try:
            data = base64.b64decode(link[8:] + '==').decode()
            obj = json.loads(data)
            addr = obj["add"]
            port = obj["port"]
            uuid = obj["id"]
            tls = obj.get("tls", "")

            out_config = {
                "protocol": "vmess",
                "settings": {
                    "vnext": [{
                        "address": addr,
                        "port": int(port),
                        "users": [{ "id": uuid, "alterId": 0 }]
                    }]
                },
                "streamSettings": {
                    "security": tls
                } if tls else {}
            }

            base_config = {
                "log": { "loglevel": "warning" },
                "inbounds": [{
                    "port": 10808,
                    "listen": "127.0.0.1",
                    "protocol": "socks",
                    "settings": { "auth": "noauth" }
                }],
                "outbounds": [out_config]
            }

            with open("temp_config.json", "w") as f:
                json.dump(base_config, f)

            v2 = subprocess.Popen(["v2ray", "-config", "temp_config.json"])
            try:
                result = subprocess.run(["curl", "--socks5", "127.0.0.1:10808", "-m", "10", "https://www.google.com"],
                                        capture_output=True, timeout=12)
                v2.kill()
                return result.returncode == 0
            except subprocess.TimeoutExpired:
                v2.kill()
        except:
            pass
    return False

def send_to_telegram(file_path, bot_token, chat_id):
    with open(file_path, 'rb') as f:
        r = requests.post(
            f"https://api.telegram.org/bot{bot_token}/sendDocument",
            data={"chat_id": chat_id},
            files={"document": f}
        )
        print("Telegram:", r.status_code)

def upload_to_dropbox(file_path, token, path):
    with open(file_path, 'rb') as f:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/octet-stream",
            "Dropbox-API-Arg": str({
                "path": path,
                "mode": "overwrite",
                "mute": True
            }).replace("'", '"')
        }
        r = requests.post(
            "https://content.dropboxapi.com/2/files/upload",
            headers=headers,
            data=f.read()
        )
        print("Dropbox:", r.status_code)

def main():
    configs = fetch_configs()
    print(f"Total found: {len(configs)}")

    working = []
    for i, cfg in enumerate(configs[:50]):
        print(f"[{i+1}] Testing: {cfg[:60]}")
        if test_config(cfg):
            print("✅ OK")
            working.append(cfg)
        else:
            print("❌ Fail")

    os.makedirs("configs", exist_ok=True)
    path = "configs/working.txt"
    with open(path, "w") as f:
        f.write("\n".join(working))

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    dropbox_token = os.getenv("DROPBOX_ACCESS_TOKEN")

    if bot_token and chat_id:
        send_to_telegram(path, bot_token, chat_id)

    if dropbox_token:
        upload_to_dropbox(path, dropbox_token, "/configs/working.txt")

if __name__ == "__main__":
    main()