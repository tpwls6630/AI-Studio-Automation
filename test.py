import subprocess
from playwright.sync_api import sync_playwright, Playwright, Browser, BrowserContext, expect
import os
import requests
import datetime
import time
import pickle
import dotenv
import pyperclip

COMMON_PROMPT = open("common_prompt.txt", "r", encoding="utf-8").read()
PDF_PATH = os.path.abspath("2015수학과_성취기준-51-122.pdf")

# 브라우저 열기
def open_browser(user_data_dir: str = "C:/dev space/math project/data/",
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


def get_answer(context: BrowserContext, image_path: str):
    page = context.new_page()

    page.goto("https://aistudio.google.com/prompts/new_chat")
    page.get_by_role("textbox", name="Type something or pick one").fill(COMMON_PROMPT)
    
    

    # 파일 업로드 처리
    with page.expect_file_chooser() as fc_info:
        page.get_by_role("button", name="Insert assets such as images").click()
        page.get_by_role("menuitem", name="Upload File").click()
    file_chooser = fc_info.value
    file_chooser.set_files(image_path)  # 이미지 파일 경로 지정

    file_chooser = fc_info.value
    file_chooser.set_files(PDF_PATH)  # 이미지 파일 경로 지정
    
    # 파일 업로드가 UI에 반영되고 Run 버튼이 활성화될 때까지 대기
    run_button = page.get_by_role("button", name="Run", exact=True)
    expect(run_button).to_be_enabled(timeout=30000)

    # Run 버튼 클릭
    run_button.click()
    
    # Gemini AI 응답 대기
    spinner = page.locator("circle.stoppable-spinner")
    spinner.wait_for(state="detached", timeout=0) # 0은 무한 대기를 의미할 수 있으나, Playwright 기본 타임아웃 적용됨
    time.sleep(2)  # 추가 대기 시간
    
    # 응답이 완료된 후 마크다운 복사
    page.locator("ms-chat-turn").last.get_by_label("Open options").click()
    page.get_by_role("menuitem", name="Copy markdown").click()
    answer = pyperclip.paste()
    page.close()
    return answer

def main():
    # CDP 브라우저 열기
    open_browser()
    wait_for_cdp_ready()

    with sync_playwright() as p:
        # 브라우저에 연결
        browser=p.chromium.connect_over_cdp("http://localhost:9222/", timeout=10000)
        context = browser.contexts[0]
        
        # 입출력 폴더 경로 설정
        images_dir = os.path.abspath("images")
        solutions_dir = os.path.abspath("solutions")
        os.makedirs(solutions_dir, exist_ok=True) # solutions 폴더가 없으면 생성

        # images 폴더에 있는 모든 사진들에 대해 get_answer 호출
        for image_filename in os.listdir(images_dir):
            image_path = os.path.join(images_dir, image_filename)
            answer = get_answer(context, image_path)
            print(f"답변 수신: {image_filename}")

            # 답변을 텍스트 파일로 저장
            base_filename, _ = os.path.splitext(image_filename)
            solution_filename = f"{base_filename}.txt"
            solution_filepath = os.path.join(solutions_dir, solution_filename)
            
            with open(solution_filepath, "w", encoding="utf-8") as f:
                f.write(answer)
            print(f"답변 저장 완료: {solution_filepath}")

main()



