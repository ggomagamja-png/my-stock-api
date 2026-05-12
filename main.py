import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Query
import os
import re

app = FastAPI()

# 헤더를 실제 브라우저와 거의 동일하게 세팅하여 차단을 방지합니다.
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
}

@app.get("/")
def home():
    return {"status": "running"}

@app.get("/stock")
def get_only_price(name: str = Query(None)):
    if not name:
        return {"price": "0"}

    try:
        # '현대차 주가' 형태로 검색
        url = f"https://search.naver.com/search.naver?query={name}+주가"
        res = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(res.text, 'html.parser')

        # 가격이 위치하는 가장 대표적인 3가지 클래스만 순차적으로 확인
        price_tag = soup.select_one(".price_info strong") # 통합검색 상단
        if not price_tag:
            price_tag = soup.select_one(".s0p_nm")        # 신규 레이아웃
        if not price_tag:
            price_tag = soup.select_one(".n_price strong") # 구형/모바일 레이아웃

        if price_tag:
            # 숫자 이외의 모든 문자(원, 콤마, 공백 등) 제거
            raw_text = price_tag.text.strip()
            price = re.sub(r'[^0-9]', '', raw_text)
            
            # 만약 추출 결과가 빈 문자열이면 '데이터없음' 반환
            return {"name": name, "price": price if price else "데이터없음"}
        
        return {"name": name, "price": "데이터없음"}

    except Exception as e:
        return {"name": name, "price": "에러"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
