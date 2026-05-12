import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Query
import os

app = FastAPI()

# 네이버 차단 방지를 위한 최소한의 헤더
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
        # 네이버 검색창에 '종목명 주가'로 검색
        url = f"https://search.naver.com/search.naver?query={name}+주가"
        res = requests.get(url, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')

        # 검색 결과 상단 '현재가' 영역 추출 (네이버 주가 검색 결과 전용 선택자)
        # s0p_nm 이나 ._price_lst 등 가변적인 것 대신 가장 안정적인 클래스 사용
        price_tag = soup.select_one(".price_info strong") or soup.select_one(".s0p_nm")
        
        if price_tag:
            # 숫자와 쉼표만 남기고 '원' 등 제거
            price = price_tag.text.replace("원", "").replace(",", "").strip()
            return {"name": name, "price": price}
        else:
            return {"name": name, "price": "데이터없음"}

    except Exception as e:
        return {"name": name, "price": "에러"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
