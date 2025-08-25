import requests
import random
import time

# ================== CONFIG ==================
SHARE_LINK = "https://novelshare-fey3ybur3q-an.a.run.app/dfnow.html?shareDate=20250825&ggc=61715493%257C9%257C1%257C324&t=1"
NUM_VISITS = 999   # số lần muốn vào link (có thể chỉnh)
DELAY = 2         # giây nghỉ giữa mỗi lần
# ============================================

USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 16_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36",
]

def visit_link(url):
    headers = {"User-Agent": random.choice(USER_AGENTS)}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            print(f"[+] Thành công với UA: {headers['User-Agent'][:35]}...")
        else:
            print(f"[-] Lỗi {r.status_code}")
    except Exception as e:
        print("[-] Exception:", e)

if __name__ == "__main__":
    for i in range(NUM_VISITS):
        print(f"[*] Lần {i+1}/{NUM_VISITS}")
        visit_link(SHARE_LINK)
        time.sleep(DELAY)
