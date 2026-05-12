import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Query
import os
import re

app = FastAPI()

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

@app.get("/")
def home():
    return {"message": "Stock API is running"}

@app.get("/stock")
def get_stock_data(name: str = Query(None)):
    if not name:
        return {"price": "0", "direction": "-", "change": "0", "rate": "0"}

    try:
        url = f"https://search.naver.com/search.naver?query={name}+주가"
        res = requests.get(url, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')

        # 네이버 주가 정보 박스 영역 찾기
        container = soup.select_one(".price_info") or soup.select_one(".info_area")
        
        if not container:
            return {"price": "데이터없음", "direction": "-", "change": "0", "rate": "0"}

        # 1. 현재 가격 (price)
        price_raw = container.select_one("strong").text
        price = re.sub(r'[^0-9]', '', price_raw)

        # 2. 등락 정보 (기호, 변동액, 변동률이 섞여 있는 영역)
        # 보통 '전일대비' 문구 옆에 위치함
        change_info = container.select_one(".price_at") or container.select_one(".n_price")
        
        # 기본값 설정
        direction = "보합"
        change_val = "0"
        rate_val = "0"

        if change_info:
            full_text = change_info.text.strip() # 예: "상승 3,500 +1.45%"
            
            # 기호(방향) 추출
            if "상승" in full_text or "▲" in full_text: direction = "▲"
            elif "하락" in full_text or "▼" in full_text: direction = "▼"
            
            # 숫자들만 골라내기 (변동액과 변동률)
            numbers = re.findall(r'[0-9.,]+', full_text)
            if len(numbers) >= 2:
                change_val = numbers[0].replace(",", "") # 변동액
                rate_val = numbers[1] # 변동률

        return {
            "name": name,
            "price": price,       # 현재가
            "direction": direction, # 등락기호 (▲/▼/보합)
            "change": change_val,  # 변동금액
            "rate": rate_val       # 변동률 (%)
        }

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
