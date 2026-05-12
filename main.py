import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
import re

app = FastAPI()

# 세션 객체 생성: 매번 연결을 새로 맺지 않고 유지하여 속도 향상 및 차단 방지
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
})

@app.get("/health")
def health_check():
    """Cron-job.org를 위한 가벼운 헬스체크 경로"""
    return {"status": "ok", "message": "I am awake!"}

@app.get("/stock")
def get_stock_info(name: str):
    if not name:
        raise HTTPException(status_code=400, detail="종목명을 입력하세요.")

    try:
        # 1. 종목명으로 네이버 증권 검색 페이지 접속
        search_url = f"https://finance.naver.com/search/searchList.naver?query={name}"
        res = session.get(search_url, timeout=5)
        res.raise_for_status()
        
        # 한글 깨짐 방지 (네이버 증권은 EUC-KR 사용)
        res.encoding = 'euc-kr' 
        soup = BeautifulSoup(res.text, 'lxml')

        # 2. 검색 결과에서 종목 코드 추출
        # 검색 결과 리스트에서 첫 번째 종목 링크를 찾음
        stock_link = soup.select_one("td.tit > a")
        
        if not stock_link:
            return {"name": name, "code": "N/A", "price": "검색결과없음"}

        # href에서 종목코드 6자리 추출 (예: /item/main.naver?code=005930)
        href = stock_link.get('href', '')
        code_match = re.search(r'code=(\d{6})', href)
        code = code_match.group(1) if code_match else "N/A"
        
        # 실제 종목명 (검색한 이름과 다를 수 있으므로 페이지의 이름 추출)
        real_name = stock_link.text.strip()

        # 3. 해당 종목의 상세 페이지에서 현재가 추출
        item_url = f"https://finance.naver.com/item/main.naver?code={code}"
        item_res = session.get(item_url, timeout=5)
        item_res.encoding = 'euc-kr'
        item_soup = BeautifulSoup(item_res.text, 'lxml')

        # 현재가 추출 (no_today 영역의 blind 데이터 활용)
        price_area = item_soup.select_one(".no_today .blind")
        price = price_area.text.strip() if price_area else "N/A"

        return {
            "name": real_name,
            "code": code,
            "price": price
        }

    except Exception as e:
        return {"name": name, "code": "Error", "price": str(e)}

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
