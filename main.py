import time
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222/")

    # browser = p.chromium.launch_persistent_context(
    #     executable_path="C:/Program Files/Google/Chrome/Application/chrome.exe",
    #     user_data_dir='C:/Users/odumag99/AppData/Local/Google/Chrome/User Data/Default',
    #     headless=False,
        
    #     args=[
    #         "--disable-blink-features=AutomationControlled",  # navigator.webdriver = false 로 설정
    #         # "--disable-web-security",                         # CORS 우회용 (필요시)
    #         "--disable-infobars",                             # "Chrome은 자동화 테스트에 의해 제어되고 있습니다" 제거
    #         # "--no-sandbox",                                   # 권한 문제 피하기 위함
    #         # "--disable-dev-shm-usage"                         # 메모리 공유 문제 우회 (특히 리눅스)
    #     ],
    #     user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    #     locale='ko-KR',  # 언어 설정
    #     timezone_id='Asia/Seoul',  # 시간대   
    # )

    # context = browser.new_context(
    #     user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    #     locale='ko-KR'
    # )
    context = browser.contexts[0]
    page = context.pages[0]
    # page.goto("http://www.google.com")
    # page.goto("https://aistudio.google.com/prompts/new_chat")
    # email_form = page.get_by_label("이메일 또는 휴대전화")
    # email_form.fill("odumag99@gmail.com")
    # login_btn = page.get_by_text("다음")
    # login_btn.click()
    context.storage_state(path="auth.json")
    page.pause()

    # page.evaluate("""
    #     () => {
    #         window.__lastClickPosition = { x: 0, y: 0 };
    #         document.addEventListener('click', e => {
    #             window.__lastClickPosition = { x: e.clientX, y: e.clientY };
    #         });
    #     }
    # """)

    # print("브라우저에서 원하는 위치를 클릭한 뒤 콘솔로 돌아와서 Enter를 누르세요.")
    # input("계속하려면 Enter를 누르세요...")

    # # 마우스 위치 읽기
    # position = page.evaluate("() => window.__lastClickPosition")
    # print(f"👉 클릭한 위치 좌표: {position}")
    # x = position['x']
    # y = position['y']
    page.mouse.click(362, 465)
    with open("system_prompt.txt", "r", encoding='utf-8') as f:
        page.keyboard.insert_text(f.read())
    run_btn = page.get_by_role("button", name="Run", exact=True)
    run_btn.click()

    # spinner는 전역에 존재하므로 page 기준으로 찾음
    spinner = page.locator("circle.stoppable-spinner")

    # spinner가 DOM에서 사라질 때까지 기다림
    spinner.wait_for(state="detached", timeout=0)

    print("spin 끝났음!")

    spans = page.locator("ms-text-chunk span.ng-star-inserted")
    print('locator 잡음!')
    # 텍스트 추출 및 정제
    texts = spans.all_inner_texts()
    final_output = " ".join([t.strip() for t in texts if t.strip()])


    code_element = page.locator("code")
    code_text = code_element.inner_text(timeout=0)  # 무한정 기다림 or 적절한 시간 설정
    print(code_text)

    print(final_output)