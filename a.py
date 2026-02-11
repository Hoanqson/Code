import time
import requests
import sys

# ================== CONFIG ==================
PROXY_API = "https://api.zingproxy.com/getProxy"  # thay URL thật của bạn
PROXY_DELAY = 240  # giây
IP_CHECK_API = "https://api.ipify.org?format=json"
TIMEOUT = 15

# ================== GLOBAL ==================
last_proxy_time = 0
current_proxy = None

# ================== FUNCTIONS ==================

def get_proxy():
    r = requests.get(PROXY_API, timeout=TIMEOUT).json()

    if r.get("status") != "success":
        raise Exception(f"❌ Proxy API lỗi: {r}")

    proxy_data = r.get("proxy")
    if not proxy_data:
        raise Exception(f"❌ Không có field proxy: {r}")

    # httpProxy format: ip:port:user:pass
    http_proxy = proxy_data.get("httpProxy")
    if not http_proxy:
        raise Exception(f"❌ Không có httpProxy: {proxy_data}")

    try:
        ip, port, user, pwd = http_proxy.split(":")
    except ValueError:
        raise Exception(f"❌ Sai format proxy: {http_proxy}")

    print(f"🌐 Proxy mới: {ip}:{port} | user={user}")
    return ip, port, user, pwd


def wait_proxy_ready():
    global last_proxy_time
    now = time.time()
    elapsed = now - last_proxy_time

    if elapsed < PROXY_DELAY:
        wait_time = int(PROXY_DELAY - elapsed)
        print(f"⏳ Đợi đủ 240s để xoay proxy: {wait_time}s")
        time.sleep(wait_time)


def check_real_ip():
    try:
        r = requests.get(IP_CHECK_API, timeout=10).json()
        ip = r.get("ip")
        print(f"🧪 IP thực tế hiện tại: {ip}")
        return ip
    except Exception as e:
        print(f"⚠️ Check IP lỗi: {e}")
        return None


def get_proxy_safe():
    global last_proxy_time, current_proxy

    wait_proxy_ready()

    ip, port, user, pwd = get_proxy()
    last_proxy_time = time.time()
    current_proxy = (ip, port, user, pwd)

    return current_proxy


# ================== MAIN ==================
if __name__ == "__main__":
    round_count = 1

    while True:
        print(f"\n🚀 RUN {round_count}")

        try:
            proxy = get_proxy_safe()
            check_real_ip()

            # === chỗ này bạn gắn selenium / code khác vào ===
            print("✅ Proxy sẵn sàng, chạy task...")
            time.sleep(5)

        except Exception as e:
            print(f"💥 Lỗi: {e}")
            time.sleep(10)

        round_count += 1
