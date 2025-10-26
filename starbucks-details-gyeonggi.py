from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from datetime import datetime
import os, re, time, json

# ==============================
# 1️⃣ 기본 설정
# ==============================
current_date = datetime.now().strftime("%Y-%m-%d")
current_year = datetime.now().strftime("%Y")
base_folder_path = os.path.join("details", current_year, "gyeonggi")
os.makedirs(base_folder_path, exist_ok=True)

def safe_extract(soup, dt_string, default=""):
    """dt 텍스트로 dd 내용 추출"""
    try:
        el = soup.find("dt", string=re.compile(dt_string))
        if el:
            dd = el.find_next_sibling("dd")
            if dd:
                return dd.get_text(strip=True)
    except Exception:
        pass
    return default

def safe_extract_images(soup, dt_string):
    """dt 제목으로 이미지 URL 리스트 추출 (https 처리)"""
    try:
        el = soup.find("dt", string=re.compile(dt_string))
        if el:
            dd = el.find_next_sibling("dd")
            if dd:
                imgs = dd.find_all("img")
                urls = []
                for img in imgs:
                    src = img.get("src", "")
                    if not src:
                        continue
                    if src.startswith("//"):
                        src = "https:" + src
                    elif not src.startswith("http"):
                        src = "https://" + src
                    urls.append(src)
                return urls
    except Exception:
        pass
    return []

# ==============================
# 2️⃣ WebDriver 설정
# ==============================
options = ChromeOptions()
# options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--disable-infobars")
options.add_argument("--disable-notifications")
options.add_argument("--disable-software-rasterizer")
options.add_argument("--disable-extensions")
options.add_argument("--no-first-run")
options.add_argument("--no-default-browser-check")
options.add_argument("--disable-blink-features=AutomationControlled")

options.add_experimental_option("prefs", {
    "profile.default_content_setting_values.geolocation": 2,
    "profile.default_content_setting_values.notifications": 2
})

browser = webdriver.Chrome(options=options)
wait = WebDriverWait(browser, 15)

# ==============================
# 3️⃣ 지역 선택 (경기 전체)
# ==============================
browser.get("https://www.starbucks.co.kr/store/store_map.do")
time.sleep(8)

browser.find_element(By.CSS_SELECTOR, "#container .loca_search h3 > a").click()
time.sleep(2)
browser.find_element(By.CSS_SELECTOR, ".loca_step1_cont .sido_arae_box li:nth-child(2)").click()  # 경기
time.sleep(2)
browser.find_element(By.CSS_SELECTOR, "#mCSB_2_container > ul > li:nth-child(1) > a").click()  # 전체
time.sleep(3)

stores = browser.find_elements(By.CSS_SELECTOR, ".quickSearchResultBoxSidoGugun .quickResultLstCon")
print(f"🔍 경기 매장 {len(stores)}개 감지됨\n")

store_data_list = []

# ==============================
# 4️⃣ 매장별 상세 추출 (중간저장 없음)
# ==============================
for index, store in enumerate(stores):
    try:
        browser.execute_script("arguments[0].click();", store)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".map_marker_pop header")))
        time.sleep(0.8)

        store_name = browser.find_element(By.CSS_SELECTOR, ".map_marker_pop header").text.strip()
        store_address = browser.find_element(By.CSS_SELECTOR, ".map_marker_pop .addr").text.strip()

        # 상세 보기 클릭
        detail_btn = browser.find_element(By.CSS_SELECTOR, ".map_marker_pop .btn_marker_detail")
        browser.execute_script("arguments[0].click();", detail_btn)

        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".shopArea_pop01_inner")))
        time.sleep(1.2)

        # BeautifulSoup으로 정보 파싱
        soup = BeautifulSoup(browser.page_source, "html.parser")

        store_description = soup.select_one(".shopArea_pop01 .asm_stitle p")
        store_description = store_description.get_text(strip=True) if store_description else ""

        store_parking = safe_extract(soup, "주차정보")
        store_directions = safe_extract(soup, "오시는 길")
        store_services = safe_extract_images(soup, "서비스")
        store_facilities = safe_extract_images(soup, "위치 및 시설")

        # 이미지 추출
        image_urls = []
        for img in soup.select(".shopArea_left .s_img li img"):
            src = img.get("src", "")
            if not src:
                continue
            if src.startswith("//"):
                src = "https:" + src
            elif not src.startswith("http"):
                src = "https://" + src
            image_urls.append(src)

        # 영업시간 추출
        store_hours = []
        try:
            hours_elems = browser.find_elements(By.CSS_SELECTOR, ".date_time dl")
            for dl in hours_elems:
                dts = dl.find_elements(By.TAG_NAME, "dt")
                dds = dl.find_elements(By.TAG_NAME, "dd")
                for dt, dd in zip(dts, dds):
                    text = f"{dt.text.strip()} {dd.text.strip()}"
                    if text.strip():
                        store_hours.append(text)
            store_hours = list(dict.fromkeys(store_hours))
        except Exception as e:
            print(f"⏰ 시간 파싱 실패: {e}")

        # 데이터 저장
        store_data = {
            "number": index + 1,
            "name": store_name,
            "description": store_description,
            "address": store_address,
            "parking": store_parking,
            "directions": store_directions,
            "phone": "1522-3232",
            "services": store_services,
            "facilities": store_facilities,
            "images": image_urls,
            "hours": store_hours
        }

        store_data_list.append(store_data)
        print(f"✅ {index + 1}/{len(stores)}: {store_name} ({len(store_hours)}시간)")

    except Exception as e:
        print(f"⚠️ {index + 1}번째 매장 오류: {e}")

    finally:
        # 팝업 닫기
        try:
            close_btn = browser.find_element(By.CSS_SELECTOR, ".isStoreViewClosePop")
            browser.execute_script("arguments[0].click();", close_btn)
            wait.until_not(EC.presence_of_element_located((By.CSS_SELECTOR, ".shopArea_pop01_inner")))
            time.sleep(0.5)
        except:
            pass

# ==============================
# 5️⃣ 최종 저장 (한 번만)
# ==============================
output_path = os.path.join(base_folder_path, f"gyeonggi_{current_date}_all.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump({
        "kind": "Korea Starbucks",
        "date": current_date,
        "location": "경기(gyeonggi)",
        "count": len(store_data_list),
        "item": store_data_list
    }, f, ensure_ascii=False, indent=4)

print(f"\n💾 전체 {len(store_data_list)}개 매장 저장 완료 → {output_path}")

browser.quit()
print("\n✅ [경기도] 전체 크롤링 완료 (한 번에 완전 저장판)")
