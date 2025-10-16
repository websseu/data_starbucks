from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import time
import re
import os
import json
from datetime import datetime

# 현재 날짜 및 연도
current_date = datetime.now().strftime("%Y-%m-%d")
current_year = datetime.now().strftime("%Y")

# 한글 지역명과 영문 지역명 매핑
location_name_mapping = {
    "서울": "seoul",
    "경기": "gyeonggi",
    "광주": "gwangju",
    "대구": "daegu",
    "대전": "daejeon",
    "부산": "busan",
    "울산": "ulsan",
    "인천": "incheon",
    "강원": "gangwon",
    "경남": "gyeongnam",
    "경북": "gyeongbuk",
    "전남": "jeolnam",
    "전북": "jeolbuk",
    "충남": "chungnam",
    "충북": "chungbuk",
    "제주": "jeju",
    "세종": "sejong",
}

# 기본 폴더 구조 생성
base_folder = "location"
count_folder = os.path.join(base_folder, "count")
total_folder = os.path.join(base_folder, "total")
year_folder = os.path.join(base_folder, current_year)
os.makedirs(count_folder, exist_ok=True)
os.makedirs(total_folder, exist_ok=True)
os.makedirs(year_folder, exist_ok=True)

# 웹드라이버 설정
options = ChromeOptions()
options.add_argument("--headless")
# options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage") 
options.add_argument("--disable-gpu")
options.add_argument("--disable-infobars")
options.add_argument("--disable-notifications")
options.add_experimental_option("prefs", {
    "profile.default_content_setting_values.geolocation": 2,
    "profile.default_content_setting_values.notifications": 2
})

browser = webdriver.Chrome(options=options)
wait = WebDriverWait(browser, 10)

region_counts = {}
total_count = 0
all_stores_data = []  # 모든 지역의 매장 데이터를 합칠 리스트

try:
    browser.get("https://www.starbucks.co.kr/store/store_map.do?disp=locale")
    time.sleep(10)
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "store_map_layer_cont"))
    )
    print("페이지가 완전히 로드되었습니다.")
    time.sleep(10)

    for index, (region_name_kor, location_name_eng) in enumerate(location_name_mapping.items(), start=1):
        # 지역 버튼 클릭
        button_selector = f".sido_arae_box li:nth-child({index}) a"
        button = browser.find_element(By.CSS_SELECTOR, button_selector)
        browser.execute_script("arguments[0].click();", button)
        print(f"{region_name_kor} 버튼 클릭 완료.")
        time.sleep(30)

        if region_name_kor != "세종":
            all_button = browser.find_element(By.CSS_SELECTOR, ".gugun_arae_box li:nth-child(1) a")
            browser.execute_script("arguments[0].click();", all_button)
            print("전체 버튼 클릭 완료.")
            time.sleep(60)

        soup = BeautifulSoup(browser.page_source, 'html.parser')

        total_count_element = soup.select_one(".result_num_wrap .sidoSetResult")
        region_count = int(total_count_element.text.strip()) if total_count_element else 0
        print(f"{region_name_kor} 매장 수: {region_count}")

        region_counts[region_name_kor] = region_count
        total_count += region_count

        # 매장 정보 수집
        store_data = []
        stores = soup.select(".quickSearchResultBoxSidoGugun li.quickResultLstCon")
        for store in stores:
            name = store.get("data-name")
            address = store.select_one(".result_details").text.strip() if store.select_one(".result_details") else None
            if address:
                address = re.sub(r'\d{4}-\d{4}', '', address).strip()
            latitude = store.get("data-lat")
            longitude = store.get("data-long")

            store_info = {
                "name": name,
                "address": address,
                "latitude": latitude,
                "longitude": longitude
            }
            store_data.append(store_info)
            all_stores_data.append(store_info)  # 전체 데이터에도 추가

        final_data = {
            "location": region_name_kor,
            "count": len(store_data),
            "date": current_date,
            "item": store_data
        }

        # ✅ 연도 폴더 안에 지역 폴더 생성
        location_folder_path = os.path.join(year_folder, location_name_eng)
        os.makedirs(location_folder_path, exist_ok=True)

        file_name = f"{location_folder_path}/{location_name_eng}_{current_date}.json"
        with open(file_name, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=4)
        print(f"{region_name_kor} 데이터가 '{file_name}' 파일에 저장되었습니다.")

    # ✅ 전체 매장 수 JSON (count 폴더에 저장)
    count_data = {
        "날짜": current_date,
        "전체": total_count,
        **region_counts
    }
    count_file_path = os.path.join(count_folder, f"starbucks-count_{current_date}.json")
    with open(count_file_path, "w", encoding="utf-8") as json_file:
        json.dump(count_data, json_file, ensure_ascii=False, indent=4)
    print(f"데이터가 JSON 파일로 저장되었습니다: {count_file_path}")

    # ✅ 전체 매장 통합 데이터 JSON (total 폴더에 저장)
    total_data = {
        "kind": "Korea Starbucks",
        "date": current_date,
        "location": "전국(total)",
        "count": len(all_stores_data),
        "item": all_stores_data
    }
    total_file_path = os.path.join(total_folder, f"starbucks-total_{current_date}.json")
    with open(total_file_path, "w", encoding="utf-8") as json_file:
        json.dump(total_data, json_file, ensure_ascii=False, indent=4)
    print(f"전체 통합 데이터가 JSON 파일로 저장되었습니다: {total_file_path}")

except TimeoutException as e:
    print("에러 발생:", str(e))

finally:
    browser.quit()
