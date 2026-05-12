import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Query
import os
import re
from urllib.parse import unquote  # 추가된 라이브러리

app = FastAPI()

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
}

@app.get("/")
def home():
    return {"status": "ok"}

@app.get("/stock")
def get_stock_data(name: str = Query(None)):
    if not name:
        return {"price": "0", "direction": "-", "change": "0", "rate": "0"}

    # 핵심 수정: VBA에서 넘어온 인코딩된 한글(%EB%9D%BC 등)을 일반 한글로 변환
    decoded_name = unquote(name)

    try:
        # 인코딩된 이름으로 검색 URL 생성
        url = f"https://search.naver.com/search.naver?query={decoded_name}+주가"
        res = requests.get(url, headers=HEADERS, timeout=5)
        html = res.text
        soup = BeautifulSoup(html, 'html.parser')

        # 1. 가격 정보 추출
        price = "0"
        price_candidates = soup.select(".price_info strong, .s0p_nm, .n_price strong, .api_biz_stock_price")
        
        if price_candidates:
            price = re.sub(r'[^0-9]', '', price_candidates[0].text)
        else:
            match = re.search(r'현재가.*?([0-9,]{3,10})', html)
            if match:
                price = match.group(1).replace(",", "")

        # 2. 등락 정보 추출
        direction = "보합"
        change = "0"
        rate = "0"
        
        info_tags = soup.select(".price_at, .n_price, .api_biz_stock_diff")
        if info_tags:
            info_text = info_tags[0].text.strip()
            if "상승" in info_text or "▲" in info_text:
                direction = "▲"
            elif "하락" in info_text or "▼" in info_text:
                direction = "▼"
            
            nums = re.findall(r'[0-9.]+', info_text.replace(",", ""))
            if len(nums) >= 2:
                change = nums[0]
                rate = nums[1]

        if price == "0":
            return {"name": decoded_name, "price": "데이터없음", "direction": "-", "change": "0", "rate": "0"}
            
        return {
            "name": decoded_name,
            "price": price,
            "direction": direction,
            "change": change,
            "rate": rate
        }

    except Exception as e:
        return {"error": str(e), "price": "에러"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
