import subprocess
from playwright.sync_api import sync_playwright, Playwright, Browser, BrowserContext
import os
import requests
import datetime
import time
import pickle
import dotenv

dotenv.load_dotenv(".env")

USER_DATA_DIR = os.getenv("USER_DATA_DIR")
if USER_DATA_DIR is None:
    raise Exception("USER_DATA_DIR를 불러오지 못함.")

try:
    with open("system_prompt.txt", "r", encoding='utf-8') as f:
        SYSTEM_PROMPT = f.read()
except Exception as e:
    raise Exception("SYSTEM PROMPT를 읽어오는 중 에러 발생: ", str(e))

# 브라우저 열기
def open_browser(user_data_dir: str,
                  chrome_path: str = "C:/Program Files/Google/Chrome/Application/chrome.exe",
):
    subprocess.Popen(f'"{chrome_path}" --remote-debugging-port=9222 --user-data-dir="{user_data_dir}"')

def wait_for_cdp_ready(url="http://localhost:9222/json/version", timeout=10):
    for _ in range(timeout):
        try:
            print("Fetching...")
            res = requests.get(url)
            if res.status_code == 200:
                print("CDP is ready.")
                return True
        except:
            pass
        time.sleep(1)
        print("CDP is not ready.")
    raise Exception("CDP 브라우저가 시간 내에 준비되지 않았습니다.")

def get_exam(context: BrowserContext):
    page = context.new_page()
    

    # AI Studio 페이지 접속
    page.goto("https://aistudio.google.com/prompts/new_chat")
    input_area = page.get_by_role("textbox", name="Type something or pick one")
    input_area.wait_for(state="attached")

    # 프롬프트 입력
    page.mouse.click(362, 465)
    page.keyboard.insert_text(SYSTEM_PROMPT)
    
    # Run 버튼 클릭
    run_btn = page.get_by_role("button", name="Run", exact=True)
    run_btn.click()

    # 응답 대기
    spinner = page.locator("circle.stoppable-spinner")
    spinner.wait_for(state="detached", timeout=0)
    time.sleep(2)

    # 응답 추출
    code_element = page.locator("code")
    code_text = code_element.inner_text(timeout=0) 
    page.close()
    return code_text


def main():
    # CDP 브라우저 열기
    open_browser(USER_DATA_DIR)
    wait_for_cdp_ready()

    with sync_playwright() as p:
        # 브라우저에 연결
        browser=p.chromium.connect_over_cdp("http://localhost:9222/", timeout=10000)
        context = browser.contexts[0]

        # 문제 무한 생성 후 저장
        for _ in range(100):
            question = get_exam(context)
            print(question)
            question_gen_timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            bin_path = question_gen_timestamp + '.bin'
            with open(bin_path, "wb") as f:
                pickle.dump(question, f)

main()