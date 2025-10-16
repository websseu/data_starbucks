from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from datetime import datetime
import os
import re
import time
import json

# 현재 날짜를 문자열로 저장
current_date = datetime.now().strftime("%Y-%m-%d")

# 안전한 데이터 추출 함수
def safe_extract(soup, dt_string, default=""):
    """안전하게 dt 태그를 찾아 다음 dd 태그의 텍스트를 추출"""
    try:
        element = soup.find("dt", string=dt_string)
        if element and element.find_next_sibling("dd"):
            return element.find_next_sibling("dd").text.strip()
        return default
    except:
        return default

def safe_extract_images(soup, dt_string):
    """안전하게 이미지 URL 리스트를 추출"""
    try:
        element = soup.find("dt", string=dt_string)
        if element and element.find_next_sibling("dd"):
            imgs = element.find_next_sibling("dd").find_all("img")
            return [f"https:{img['src']}" for img in imgs]
        return []
    except:
        return []

# details 폴더 생성
current_year = datetime.now().strftime("%Y")
base_folder_path = os.path.join("details", current_year, "jeju")
os.makedirs(base_folder_path, exist_ok=True)

# 웹드라이버 설정 및 페이지 로드
options = ChromeOptions()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage") 
options.add_argument("--disable-gpu")
options.add_argument("--disable-infobars")
options.add_argument("--disable-notifications")
options.add_experimental_option("prefs", {
    "profile.default_content_setting_values.geolocation": 2,  
    "profile.default_content_setting_values.notifications": 2  
})
browser = webdriver.Chrome(options=options)
browser.get("https://www.starbucks.co.kr/store/store_map.do")
time.sleep(10)


# 클릭 및 이동
browser.find_element(By.CSS_SELECTOR, "#container > div > form > fieldset > div > section > article.find_store_cont > article > header.loca_search > h3 > a").click()
time.sleep(3)
print("지역검색 버튼을 클릭했습니다.")
browser.find_element(By.CSS_SELECTOR, ".loca_step1_cont .sido_arae_box li:nth-child(16)").click()
time.sleep(3) 
print("제주 버튼을 클릭했습니다.")
browser.find_element(By.CSS_SELECTOR, "#mCSB_2_container > ul > li:nth-child(1) > a").click()
time.sleep(3) 
print("전체선택 버튼을 클릭했습니다.")

# 전체 점포 리스트 가져오기
stores = browser.find_elements(By.CSS_SELECTOR, ".quickSearchResultBoxSidoGugun .quickResultLstCon")

# 모든 점포 데이터를 저장할 리스트
store_data_list = []

# 모든 점포에 대해 순차적으로 작업
for index, store in enumerate(stores):
    try:
        # JavaScript를 사용하여 요소 클릭
        browser.execute_script("arguments[0].click();", store)
        time.sleep(2)

        # 점포 이름과 주소 추출
        store_name = browser.find_element(By.CSS_SELECTOR, ".map_marker_pop header").text.strip()
        store_address = browser.find_element(By.CSS_SELECTOR, ".map_marker_pop .addr").text.strip()

        # "상세 정보 보기" 버튼 클릭
        detail_button = browser.find_element(By.CSS_SELECTOR, ".map_marker_pop .btn_marker_detail")
        browser.execute_script("arguments[0].click();", detail_button)
        time.sleep(2) 
        print(f"상세 정보 보기 버튼을 클릭했습니다. ({index + 1}/{len(stores)})")

        # 상세 정보 페이지의 HTML 가져오기
        detail_page_html = browser.page_source
        soup = BeautifulSoup(detail_page_html, 'html.parser')

        # 각종 정보 추출 (안전하게)
        try:
            store_description = soup.select_one(".shopArea_pop01 .asm_stitle p").text.strip()
        except:
            store_description = ""

        store_parking_info = safe_extract(soup, "주차정보", "")
        store_directions = safe_extract(soup, "오시는 길", "")

        # 서비스 이미지 URL 리스트 추출 (안전하게)
        store_services = safe_extract_images(soup, "서비스")

        # 위치 및 시설 이미지 URL 리스트 추출 (안전하게)
        store_facilities = safe_extract_images(soup, "위치 및 시설")

        # 이미지 URL 리스트 추출
        try:
            image_urls = [
                f"https:{img['src']}" for img in soup.select(".shopArea_left .s_img li img")
            ]
        except:
            image_urls = []

        # 영업 시간 추출
        store_hours = []
        try:
            hours_sections = soup.select(".date_time dl")
            for dl in hours_sections:
                dt_tags = dl.select("dt")
                dd_tags = dl.select("dd")
                store_hours.extend([
                    ' '.join(f"{dt.text} {dd.text}".split()) for dt, dd in zip(dt_tags, dd_tags)
                ])
        except:
            store_hours = []

        # JSON 데이터 생성
        store_data = {
            "number": index + 1, 
            "name": store_name,
            "description": store_description,
            "address": store_address,
            "parking": store_parking_info,
            "directions": store_directions,
            "phone": "1522-3232",
            "services": store_services,
            "facilities": store_facilities,
            "images": image_urls,
            "hours": store_hours, 
        }
        store_data_list.append(store_data)

        # 상세 정보 창 닫기
        close_button = browser.find_element(By.CSS_SELECTOR, ".btn_pop_close .isStoreViewClosePop")
        browser.execute_script("arguments[0].click();", close_button)
        time.sleep(2)
        
    except Exception as e:
        print(f"매장 {index + 1} 처리 중 오류 발생: {str(e)}")
        continue
# JSON 파일 구조화
final_data = {
    "kind": "Korea Starbucks",
    "date": current_date,
    "location": "제주(jeju)",
    "count": len(store_data_list),
    "item": store_data_list
}

# JSON 파일 저장
output_file_path = os.path.join(base_folder_path, f"jeju_{current_date}.json")
with open(output_file_path, 'w', encoding='utf-8') as f:
    json.dump(final_data, f, ensure_ascii=False, indent=4)

print(f"파일이 저장되었습니다: {output_file_path}")
print(f"총 {len(store_data_list)}개 매장 정보 수집 완료")

# 브라우저 닫기
browser.quit()

