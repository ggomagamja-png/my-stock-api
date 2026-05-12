import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Query
import os
import re
from urllib.parse import unquote

app = FastAPI()

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
}

@app.get("/")
def home():
    return {"status": "ok"}

# 1. 경로를 /api/stock 으로 수정
# 2. 인자 이름을 stock_name 으로 수정 (VBA 로그 기준)
@app.get("/api/stock")
def get_stock_data(stock_name: str = Query(None)):
    if not stock_name:
        return {"price": "0", "direction": "-", "change": "0", "rate": "0"}

    # URL 인코딩된 이름을 한글로 변환 (HLB%EC%9D%B4%EB%85%B8... -> HLB이노베이션)
    decoded_name = unquote(stock_name)

    try:
        url = f"https://search.naver.com/search.naver?query={decoded_name}+주가"
        res = requests.get(url, headers=HEADERS, timeout=5)
        html = res.text
        soup = BeautifulSoup(html, 'html.parser')

        # 가격 정보 추출
        price = "0"
        price_candidates = soup.select(".price_info strong, .s0p_nm, .n_price strong, .api_biz_stock_price")
        
        if price_candidates:
            price = re.sub(r'[^0-9]', '', price_candidates[0].text)
        else:
            match = re.search(r'현재가.*?([0-9,]{3,10})', html)
            if match:
                price = match.group(1).replace(",", "")

        # 등락 정보 추출
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
    # 포트 번호는 환경 변수에 따라 유동적으로 설정 (기본값 10000)
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
