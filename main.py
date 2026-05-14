from fastapi import FastAPI
import requests
import re
import logging
from typing import List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

all_items_cache = []

def fetch_krx_via_html():
    """네이버 금융 시가총액 페이지 등을 크롤링하여 국내 전 종목 리스트 수집"""
    global all_items_cache
    temp_list = []
    seen_codes = set()
    
    # Render IP 차단을 피하기 위한 표준 브라우저 헤더
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }

    # 코스피(0)와 코스닥(1) 시가총액 페이지 순회 (각 시장별 약 30페이지씩 존재)
    # 효율성을 위해 상위 20페이지씩만 긁어도 대부분의 유효 종목이 포함됩니다.
    for market_code in [0, 1]:
        for page in range(1, 25):  
            try:
                url = f"https://finance.naver.com/sise/sise_market_sum.naver?sosok={market_code}&page={page}"
                res = requests.get(url, headers=headers, timeout=10)
                
                if res.status_code != 200:
                    continue
                
                # 정규표현식으로 종목코드와 종목명 추출
                # <a href="/item/main.naver?code=005930" class="tltle">삼성전자</a>
                matches = re.findall(r'href="/item/main\.naver\?code=(\d{6})".*?class="tltle">(.*?)</a>', res.text)
                
                if not matches:
                    break # 더 이상 데이터가 없는 페이지면 중단
                
                for code, name in matches:
                    if code not in seen_codes:
                        temp_list.append({
                            "code": code,
                            "name": name,
                            "type": "KOSPI" if market_code == 0 else "KOSDAQ"
                        })
                        seen_codes.add(code)
                
            except Exception as e:
                logger.error(f"Error crawling market {market_code} page {page}: {e}")
                continue

    if temp_list:
        # 이름순 정렬
        all_items_cache = sorted(temp_list, key=lambda x: x['name'])
        logger.info(f"수집 완료: 총 {len(all_items_cache)}개 종목 캐싱됨")
    else:
        logger.error("HTML 크롤링 결과가 0건입니다.")

@app.on_event("startup")
def startup_event():
    fetch_krx_via_html()

@app.get("/krx-list")
async def get_krx_step(start: int = 0, limit: int = 50):
    if not all_items_cache:
        fetch_krx_via_html()
    
    total = len(all_items_cache)
    sliced_data = all_items_cache[start:start+limit]
    
    return {
        "start": start,
        "count": len(sliced_data),
        "total_count": total,
        "items": sliced_data
    }

@app.get("/health")
def health_check():
    return {"status": "ok", "cache_count": len(all_items_cache)}
