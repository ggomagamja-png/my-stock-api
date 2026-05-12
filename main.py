import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Query
import os

app = FastAPI()

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

@app.get("/")
def home():
    return {"message": "Stock API is running"}

@app.get("/stock")
def get_price(name: str = Query(None)):
    if not name:
        return {"price": "0"}

    try:
        # '종목명 주가'로 검색
        url = f"https://search.naver.com/search.naver?query={name}+주가"
        res = requests.get(url, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')

        # 가격을 찾기 위한 여러가지 후보 태그 (네이버가 수시로 바꿈)
        # 1. 일반적인 주가 박스, 2. 모바일/통합검색 상단, 3. 기타 변형 구조
        price_selectors = [
            ".price_info strong", 
            ".s0p_nm", 
            ".n_price strong",
            "div.stock_tlt strong",
            ".info_area .price"
        ]
        
        price_text = ""
        for selector in price_selectors:
            tag = soup.select_one(selector)
            if tag and tag.text.strip():
                price_text = tag.text.strip()
                break
        
        if price_text:
            # 숫자와 쉼표만 남기고 나머지(원, ▲, ▼ 등) 제거
            # 숫자(0-9)와 콤마(,)만 골라내는 로직
            import re
            price_clean = re.sub(r'[^0-9,]', '', price_text)
            price = price_clean.replace(",", "")
            return {"name": name, "price": price}
        else:
            return {"name": name, "price": "데이터없음"}

    except Exception as e:
        return {"name": name, "price": f"에러:{str(e)}"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
