import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
import re
import os

app = FastAPI()

# 세션 객체 전역 생성 (연결 재사용으로 서버 부하 감소)
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
        raise HTTPException(status_code=400, detail="Name is required")

    try:
        # 1. 네이버 증권 종목 검색 (EUC-KR 인코딩 주의)
        search_url = f"https://finance.naver.com/search/searchList.naver?query={name}"
        res = session.get(search_url, timeout=10)
        res.encoding = 'euc-kr'
        soup = BeautifulSoup(res.text, 'lxml')

        # 2. 첫 번째 검색 결과 행 찾기
        stock_link = soup.select_one("td.tit > a")
        
        if not stock_link:
            # 검색 결과가 하나뿐이라 상세페이지로 바로 리다이렉트 되는 경우 대비
            # 혹은 결과가 정말 없는 경우
            return {"name": name, "code": "N/A", "price": "0"}

        href = stock_link.get('href', '')
        code_match = re.search(r'code=(\d{6})', href)
        code = code_match.group(1) if code_match else "N/A"
        real_name = stock_link.text.strip()

        # 3. 현재가 추출 (상세 페이지 재접속)
        item_url = f"https://finance.naver.com/item/main.naver?code={code}"
        item_res = session.get(item_url, timeout=10)
        item_res.encoding = 'euc-kr'
        item_soup = BeautifulSoup(item_res.text, 'lxml')

        # 네이버 증권 현재가 영역 (구조 변경 대비 여러 선택자 시도)
        price_tag = item_soup.select_one(".no_today .blind")
        price = price_tag.text.strip() if price_tag else "0"

        return {
            "name": real_name,
            "code": code,
            "price": price
        }

    except Exception as e:
        # 서버가 죽지 않도록 에러를 잡아내고 메시지 반환
        print(f"Error: {e}")
        return {"name": name, "code": "Error", "price": "0"}

if __name__ == "__main__":
    import uvicorn
    # Render 환경 변수 PORT 사용
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
