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

# ---- PROXY ----
FIXED_PROXY = "117.1.93.82:54499:ergdg_hoanq:TTDcvapl"
PROXY_ROTATE_API = "https://api.zingproxy.com/open/get-proxy/d2o115o0zpq3ded62ccec98c681d59ca4629f6dd30cfa6f911be335"

PROXY_ROTATE_SECONDS = 240
SSH_PER_ROUND = 5
# ========================================


def log(ssh_i, step, msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] [SSH {ssh_i}/{SSH_PER_ROUND}] [STEP {step}] {msg}")


def send_webhook(link):
    try:
        requests.post(WEBHOOK_URL, json={"content": f"🔥 SSHX\n{link}"}, timeout=10)
    except:
        pass


def reset_proxy():
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🔄 RESET PROXY")
    try:
        r = requests.get(PROXY_ROTATE_API, timeout=30)
        print("RESET RESPONSE:", r.text)
    except Exception as e:
        print("RESET ERROR:", e)


def wait_240s(end_ts):
    while True:
        remain = int(end_ts - time.monotonic())
        if remain <= 0:
            break
        print(f"⏳ Chờ đủ 240s: {remain}s", end="\r")
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

    driver.execute_cdp_cmd("Network.enable", {})
    driver.execute_cdp_cmd(
        "Network.setExtraHTTPHeaders",
        {"headers": {
            "Proxy-Authorization": requests.auth._basic_auth_str(user, pwd)
        }}
    )
    return driver


def create_one_ssh(ssh_i):
    driver = create_driver()
    wait = WebDriverWait(driver, 300)
    actions = ActionChains(driver)

    try:
        log(ssh_i, 1, "Mở nicegpu.com")
        driver.get(SITE_URL)
        time.sleep(3)

        log(ssh_i, 2, "Click Playground")
        old_tabs = driver.window_handles.copy()
        wait.until(EC.element_to_be_clickable((By.XPATH, PLAYGROUND_XPATH))).click()

        wait.until(lambda d: len(d.window_handles) > len(old_tabs))
        driver.switch_to.window(list(set(driver.window_handles) - set(old_tabs))[0])

        log(ssh_i, 3, "Reload Playground (F5)")
        actions.send_keys(Keys.F5).perform()
        time.sleep(5)

        log(ssh_i, 4, "Đợi redirect WELCOME.ipynb")
        wait.until(lambda d: WELCOME_PATH in d.current_url and "token=" not in d.current_url)

        log(ssh_i, 5, "Notebook mount xong")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".jp-Notebook")))

        log(ssh_i, 6, "Tạo cell mới")
        actions.send_keys(Keys.ESCAPE).send_keys("b").send_keys(Keys.ENTER).perform()
        time.sleep(0.5)

        log(ssh_i, 7, "Chạy SSHX")
        actions.send_keys(SSHX_CMD).key_down(Keys.SHIFT).send_keys(Keys.ENTER).key_up(Keys.SHIFT).perform()
        time.sleep(20)

        log(ssh_i, 8, "Lấy SSHX link")
        sshx_link = None
        for out in driver.find_elements(By.CSS_SELECTOR, ".jp-OutputArea-output pre"):
            m = re.search(r"(https://sshx\.io/\S+)", out.text)
            if m:
                sshx_link = m.group(1)
                break

        if not sshx_link:
            raise Exception("Không tìm thấy SSHX link")

        log(ssh_i, 9, f"SSHX = {sshx_link}")
        send_webhook(sshx_link)

        log(ssh_i, 10, "Mở SSHX")
        driver.get(sshx_link)

        log(ssh_i, 11, "Nhập tên")
        wait.until(EC.presence_of_element_located((By.XPATH, '//input[@placeholder="Your name"]')))\
            .send_keys(YOUR_NAME + Keys.ENTER)

        time.sleep(5)

        log(ssh_i, 12, "Tạo terminal")
        btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@title="Create new terminal"]')))
        driver.execute_script("arguments[0].click();", btn)

        time.sleep(3)

        log(ssh_i, 13, "Paste & run command")
        terminal = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.xterm-screen")))
        ActionChains(driver).click(terminal).perform()

        driver.execute_script("navigator.clipboard.writeText(arguments[0]);", TEXT_TO_PASTE)
        actions.key_down(Keys.CONTROL).key_down(Keys.SHIFT).send_keys("v")\
               .key_up(Keys.SHIFT).key_up(Keys.CONTROL).send_keys(Keys.ENTER).perform()

        log(ssh_i, 14, "DONE")
        time.sleep(5)

    except Exception as e:
        log(ssh_i, "❌", f"LỖI: {e}")

    finally:
        driver.quit()


def main():
    round_id = 0
    while True:
        round_id += 1
        print(f"\n========== 🔁 ROUND {round_id} ==========")

        start = time.monotonic()
        end = start + PROXY_ROTATE_SECONDS

        for i in range(1, SSH_PER_ROUND + 1):
            create_one_ssh(i)

        print("\n⏸ Đợi đủ 240s trước khi reset IP")
        wait_240s(end)
        reset_proxy()
        time.sleep(5)


if __name__ == "__main__":
    main()
