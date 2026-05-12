import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
import re
import os

app = FastAPI()

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
})

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/stock")
def get_stock_info(name: str):
    if not name:
        return {"name": name, "code": "N/A", "price": "0"}

    try:
        # 1. 검색 페이지 요청
        search_url = f"https://finance.naver.com/search/searchList.naver?query={name}"
        res = session.get(search_url, timeout=10)
        res.encoding = 'euc-kr'
        
        # 만약 바로 상세 페이지로 리다이렉트 되었다면 (URL에 code=가 포함됨)
        if "code=" in res.url:
            code_match = re.search(r'code=(\d{6})', res.url)
            code = code_match.group(1) if code_match else "N/A"
        else:
            # 리스트 페이지인 경우 첫 번째 항목 추출
            soup = BeautifulSoup(res.text, 'html.parser')
            stock_link = soup.select_one("td.tit > a")
            if stock_link:
                href = stock_link.get('href', '')
                code_match = re.search(r'code=(\d{6})', href)
                code = code_match.group(1) if code_match else "N/A"
            else:
                return {"name": name, "code": "N/A", "price": "0"}

        # 2. 상세 페이지에서 가격 추출 (확정된 code 사용)
        item_url = f"https://finance.naver.com/item/main.naver?code={code}"
        item_res = session.get(item_url, timeout=10)
        item_res.encoding = 'euc-kr'
        item_soup = BeautifulSoup(item_res.text, 'html.parser')

        # 가격 영역 추출 (여러 케이스 대응)
        price_tag = item_soup.select_one(".no_today .blind")
        if not price_tag:
            price_tag = item_soup.select_one("#_nowVal") # 대안 선택자
            
        price = price_tag.text.strip() if price_tag else "0"

        return {
            "name": name,
            "code": code,
            "price": price
        }

    except Exception as e:
        print(f"Error occurred: {e}")
        return {"name": name, "code": "Error", "price": "0"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
