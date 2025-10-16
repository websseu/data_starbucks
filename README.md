# Starbucks Data Scraper

This project uses Python to collect Starbucks store location data from the official Starbucks website. The script automates the process using Selenium and BeautifulSoup

## 폴더명

```
└── location [지역명, 지역 매장 갯수, 위도, 경도]
    ├── 01 seoul
    ├── 02 gyeonggi
    ├── 03 busan
    ├── 04 daegu
    ├── 05 incheon
    ├── 06 gwangju
    ├── 07 daejeon
    ├── 08 ulsan
    ├── 09 gangwon
    ├── 10 chungbuk
    ├── 11 chungnam
    ├── 12 jeolbuk
    ├── 13 jeolnam
    ├── 14 gyeongbuk
    ├── 15 gyeongnam
    ├── 16 jeju
    └── 17 sejong
```

## 지역명

지역명은 다음과 같이 정리합니다.

```
location_name_mapping = {
    "서울": "seoul",
    "부산": "busan",
    "대구": "daegu",
    "인천": "incheon",
    "광주": "gwangju",
    "대전": "daejeon",
    "울산": "ulsan",
    "경기": "gyeonggi",
    "강원": "gangwon",
    "충북": "chungbuk",
    "충남": "chungnam",
    "전북": "jeolbuk",
    "전남": "jeolnam",
    "경북": "gyeongbuk",
    "경남": "gyeongnam",
    "제주": "jeju",
    "세종": "sejong"
}
```
