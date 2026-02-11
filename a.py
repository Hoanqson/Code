import time, re, requests
from datetime import datetime

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


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

# ---- PROXY (TRUNG GIAN CỐ ĐỊNH) ----
FIXED_PROXY = "117.1.93.82:54499:ergdg_hoanq:TTDcvapl"
PROXY_ROTATE_API = "https://api.zingproxy.com/open/get-proxy/d2o115o0zpq3ded62ccec98c681d59ca4629f6dd30cfa6f911be335"

PROXY_ROTATE_SECONDS = 240
SSH_PER_ROUND = 5
# ========================================


def now():
    return datetime.now().strftime("%H:%M:%S")


def send_webhook(link):
    try:
        requests.post(
            WEBHOOK_URL,
            json={"content": f"🔥 **SSHX CREATED**\n{link}"},
            timeout=10
        )
    except:
        pass


def reset_proxy():
    print(f"[{now()}] 🔄 RESET IP PROXY")
    try:
        r = requests.get(PROXY_ROTATE_API, timeout=30)
        print(f"[{now()}] 🔄 RESPONSE:", r.text)
    except Exception as e:
        print(f"[{now()}] ❌ RESET LỖI:", e)


def wait_until(ts_end):
    while True:
        remain = int(ts_end - time.monotonic())
        if remain <= 0:
            break
        print(f"[{now()}] ⏳ Đợi đủ 240s: {remain}s", end="\r")
        time.sleep(1)
    print()


def create_driver():
    ip, port, user, pwd = FIXED_PROXY.split(":")

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--disable-blink-features=AutomationControlled")

    opts.add_argument(f"--proxy-server=http://{ip}:{port}")

    driver = webdriver.Chrome(options=opts)

    # auth proxy
    driver.execute_cdp_cmd(
        "Network.enable", {}
    )
    driver.execute_cdp_cmd(
        "Network.setExtraHTTPHeaders",
        {"headers": {
            "Proxy-Authorization": requests.auth._basic_auth_str(user, pwd)
        }}
    )

    return driver


def create_one_ssh(index):
    print(f"[{now()}] 🚀 Tạo SSH #{index}")
    driver = create_driver()
    wait = WebDriverWait(driver, 300)
    actions = ActionChains(driver)

    try:
        driver.get(SITE_URL)
        time.sleep(3)

        old_tabs = driver.window_handles.copy()
        wait.until(EC.element_to_be_clickable((By.XPATH, PLAYGROUND_XPATH))).click()

        wait.until(lambda d: len(d.window_handles) > len(old_tabs))
        jupyter_tab = list(set(driver.window_handles) - set(old_tabs))[0]
        driver.switch_to.window(jupyter_tab)

        wait.until(lambda d: "/lab" in d.current_url)
        time.sleep(2)

        actions.send_keys(Keys.F5).perform()
        time.sleep(5)

        wait.until(lambda d: WELCOME_PATH in d.current_url and "token=" not in d.current_url)

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".jp-Notebook")))
        time.sleep(2)

        actions.send_keys(Keys.ESCAPE).send_keys("b").send_keys(Keys.ENTER).perform()
        time.sleep(0.5)

        actions.send_keys(SSHX_CMD).key_down(Keys.SHIFT).send_keys(Keys.ENTER).key_up(Keys.SHIFT).perform()
        time.sleep(20)

        sshx_link = None
        for out in driver.find_elements(By.CSS_SELECTOR, ".jp-OutputArea-output pre"):
            m = re.search(r"(https://sshx\.io/\S+)", out.text)
            if m:
                sshx_link = m.group(1)
                break

        if not sshx_link:
            raise Exception("Không lấy được SSHX link")

        print(f"[{now()}] 🔥 SSHX: {sshx_link}")
        send_webhook(sshx_link)

        driver.get(sshx_link)
        name_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Your name"]')))
        name_input.send_keys(YOUR_NAME + Keys.ENTER)
        time.sleep(5)

        btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@title="Create new terminal"]')))
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(3)

        terminal = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.xterm-screen")))
        ActionChains(driver).click(terminal).perform()

        driver.execute_script("navigator.clipboard.writeText(arguments[0]);", TEXT_TO_PASTE)
        actions.key_down(Keys.CONTROL).key_down(Keys.SHIFT).send_keys("v").key_up(Keys.SHIFT).key_up(Keys.CONTROL).send_keys(Keys.ENTER).perform()

        print(f"[{now()}] ✅ SSH #{index} DONE")
        time.sleep(5)

    finally:
        driver.quit()


# ================= MAIN =================
def main():
    round_id = 0

    while True:
        round_id += 1
        print(f"\n========== 🔁 ROUND {round_id} ==========")

        start = time.monotonic()
        end = start + PROXY_ROTATE_SECONDS

        for i in range(1, SSH_PER_ROUND + 1):
            create_one_ssh(i)

        print(f"[{now()}] ⏸ Đã đủ {SSH_PER_ROUND} SSH – chờ reset IP")
        wait_until(end)

        reset_proxy()
        time.sleep(5)


if __name__ == "__main__":
    main()
