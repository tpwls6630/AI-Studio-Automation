import subprocess
from playwright.sync_api import sync_playwright, Playwright, Browser, BrowserContext, expect, TimeoutError
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


def get_answer(context: BrowserContext, image_path: str, max_retries: int = 3):
    for attempt in range(max_retries):
        page = None # page 변수 초기화
        try:
            print(f"{image_path} 처리 시도 {attempt + 1}/{max_retries}...")
            page = context.new_page() # 각 시도마다 새 페이지

            page.goto("https://aistudio.google.com/prompts/new_chat", timeout=60000) # goto에도 타임아웃 설정
            
            # 프롬프트 입력
            textbox = page.get_by_role("textbox", name="Type something or tab to")
            expect(textbox).to_be_visible(timeout=30000) # 텍스트 박스가 보일 때까지 대기
            textbox.fill(COMMON_PROMPT)
            
            # 파일 업로드 처리
            # expect_file_chooser의 타임아웃은 파일 선택 대화상자가 나타날 때까지의 시간
            with page.expect_file_chooser(timeout=60000) as fc_info: # 파일 선택기 대기 시간 증가
                insert_button = page.get_by_role("button", name="Insert assets such as images")
                expect(insert_button).to_be_enabled(timeout=30000) # 버튼 활성화 대기
                insert_button.click()
                
                upload_button = page.get_by_role("menuitem", name="Upload File")
                expect(upload_button).to_be_visible(timeout=30000) # 업로드 버튼 보일 때까지 대기
                upload_button.click()
                
            file_chooser = fc_info.value
            file_chooser.set_files([PDF_PATH, image_path]) 
            
            # 파일 업로드가 UI에 반영되고 Run 버튼이 활성화될 때까지 대기
            run_button = page.get_by_role("button", name="Run", exact=True)
            expect(run_button).to_be_enabled(timeout=30000) # 기존 5분 유지

            # Run 버튼 클릭
            run_button.click()
            
            # Gemini AI 응답 대기
            spinner = page.locator("circle.stoppable-spinner")
            # 응답 생성에 매우 긴 시간이 걸릴 수 있으므로, 타임아웃을 충분히 길게 설정 (예: 10분)
            spinner.wait_for(state="detached", timeout=600000) 
            
            time.sleep(2)  # 추가 대기 시간 (UI 안정화 목적)
            
            # 응답이 완료된 후 코드 추출
            code_element_locator = page.locator("ms-chat-turn").last.locator("code").last
            expect(code_element_locator).to_be_visible(timeout=60000) # 코드가 보일 때까지 대기 시간 증가
            code_text = code_element_locator.inner_text()

            if page and not page.is_closed():
                page.close()
            return code_text # 성공

        except TimeoutError as e: # Playwright의 TimeoutError 명시
            print(f"시도 {attempt + 1}/{max_retries} 중 타임아웃 발생: {e}")
            if page and not page.is_closed():
                try:
                    page.close()
                except Exception as close_err:
                    print(f"페이지 닫기 중 오류 발생: {close_err}")
            
            if attempt + 1 == max_retries:
                print(f"최대 재시도 횟수({max_retries}) 도달. {image_path} 처리 실패.")
                raise  
            
            print(f"{image_path} 재시도합니다...")
            time.sleep(1) # 재시도 전 5초 대기

        except Exception as e: # TimeoutError 외 다른 예외 처리
            print(f"시도 {attempt + 1}/{max_retries} 중 예상치 못한 오류 발생: {e}")
            if page and not page.is_closed():
                try:
                    page.close()
                except Exception as close_err:
                    print(f"페이지 닫기 중 오류 발생: {close_err}")

            if attempt + 1 == max_retries:
                print(f"최대 재시도 횟수({max_retries}) 도달. {image_path} 처리 실패.")
                raise
            
            print(f"{image_path} 재시도합니다...")
            time.sleep(1) # 재시도 전 5초 대기

    # 루프를 모두 돌았는데도 성공하지 못한 경우 (이론적으로는 위에서 raise 되어야 함)
    if page and not page.is_closed():
        try:
            page.close()
        except Exception as close_err:
            print(f"최종 페이지 닫기 중 오류 발생: {close_err}")
    raise Exception(f"{image_path} 처리에 최종 실패했습니다 (모든 재시도 실패).")

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
            
            # 답변 파일 경로 생성 및 존재 여부 확인
            base_filename, _ = os.path.splitext(image_filename)
            solution_filename = f"{base_filename}.json"
            solution_filepath = os.path.join(solutions_dir, solution_filename)

            if os.path.exists(solution_filepath):
                print(f"이미 답변이 존재합니다: {solution_filepath}, 건너뜁니다.")
                continue # 이미 파일이 존재하면 다음 이미지로 넘어감

            answer = get_answer(context, image_path)
            print(f"답변 수신: {image_filename}")

            # 답변을 텍스트 파일로 저장
            with open(solution_filepath, "w", encoding="utf-8") as f:
                f.write(answer)
            print(f"답변 저장 완료: {solution_filepath}")

        # 모든 작업 완료 후 브라우저 닫기
        print("모든 이미지 처리가 완료되었습니다. 브라우저를 닫습니다.")
        browser.close()

main()



