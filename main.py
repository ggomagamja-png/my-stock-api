from fastapi import FastAPI, HTTPException
import requests
from bs4 import BeautifulSoup
import re

app = FastAPI()

@app.get("/stock")
def get_stock_info(name: str):
    url = f"https://search.naver.com/search.naver?query={name}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')

        # 가격 추출 (기존에 잘 나왔던 로직)
        price_tag = soup.select_one(".spt_con strong")
        price = price_tag.text if price_tag else "N/A"

        # 종목 코드 추출 (URL 파라미터에서 추출하는 더 확실한 방법)
        code = "N/A"
        # 종목 상세 페이지로 가는 링크들 중 symbol=숫자6자리 패턴을 찾음
        link = soup.find('a', href=re.compile(r'symbol=\d{6}'))
        if link:
            match = re.search(r'symbol=(\d{6})', link['href'])
            if match:
                code = match.group(1)

        return {"name": name, "code": code, "price": price}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
