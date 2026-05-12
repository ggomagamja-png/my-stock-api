import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, Query
import os
import re

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

    try:
        url = f"https://search.naver.com/search.naver?query={name}+주가"
        res = requests.get(url, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')

        # 1. 가격 추출 (이미 잘 나오는 부분)
        price = "0"
        price_tag = soup.select_one(".price_info strong, .s0p_nm, .n_price strong")
        if price_tag:
            price = re.sub(r'[^0-9]', '', price_tag.text)

        # 2. 변동 정보 추출 (이 부분이 핵심 수정 사항입니다)
        direction = "보합"
        change = "0"
        rate = "0"

        # 변동액과 변동률이 포함된 태그 후보군
        # 네이버는 상승일 때 'up', 하락일 때 'down'이라는 클래스를 태그에 붙이는 경우가 많습니다.
        info_area = soup.select_one(".price_at, .info_area, .price_info")
        
        if info_area:
            info_text = info_area.text.strip()
            
            # 방향 판단 (글자 혹은 클래스명으로 판단)
            # 클래스명에 'up'이나 'plus'가 있는지, 혹은 텍스트에 상승 기호가 있는지 확인
            area_html = str(info_area).lower()
            if "상승" in info_text or "▲" in info_text or "plus" in area_html:
                direction = "▲"
            elif "하락" in info_text or "▼" in info_text or "minus" in area_html:
                direction = "▼"

            # 숫자만 추출 (변동액과 변동률)
            # 정규식으로 숫자, 점(.), 콤마(,)가 포함된 덩어리들을 모두 찾습니다.
            nums = re.findall(r'[0-9.,]+', info_text)
            
            # 추출된 숫자 리스트에서 현재가(price)를 제외한 나머지가 변동액과 변동률입니다.
            valid_nums = [n.replace(",", "") for n in nums if n.replace(",", "") != price]
            
            if len(valid_nums) >= 2:
                change = valid_nums[0] # 첫 번째 숫자가 변동액
                rate = valid_nums[1]   # 두 번째 숫자가 변동률
            elif len(valid_nums) == 1:
                # 숫자가 하나만 발견되면 변동액으로 간주
                change = valid_nums[0]

        return {
            "name": name,
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
