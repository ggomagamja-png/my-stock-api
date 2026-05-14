from fastapi import FastAPI
import requests
import logging

app = FastAPI()

# 종목 리스트를 저장할 캐시
all_items_cache = []

def fetch_krx_list_via_naver():
    """네이버 금융 API를 사용하여 국내 전 종목 리스트 수집"""
    global all_items_cache
    temp_list = []
    
    # 네이버 주식 검색 API의 초성 필터를 활용하여 전체 데이터를 긁어옵니다.
    # 가~힣까지 모든 범위를 커버하는 키워드 리스트
    keywords = ["가", "나", "다", "라", "마", "바", "사", "아", "자", "차", "카", "타", "파", "하",
                "ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"]
    
    seen_codes = set()
    
    for kw in keywords:
        try:
            url = f"https://ac.finance.naver.com/ac?q={kw}&q_enc=utf-8&st=1&frm=stock&r_format=json"
            res = requests.get(url, timeout=5)
            data = res.json()
            items = data.get('items', [[]])[0]
            
            for item in items:
                code = item[1]
                name = item[0]
                is_kr = item[4] == '1' # 1이면 국내 주식
                
                if is_kr and code not in seen_codes:
                    # 종목코드 6자리 숫자인 것만 필터링 (주식, ETF, ETN 포함)
                    if len(code) == 6 and code.isdigit():
                        temp_list.append({
                            "code": code,
                            "name": name,
                            "type": "KRX"
                        })
                        seen_codes.add(code)
        except Exception as e:
            logging.error(f"Search error for {kw}: {e}")
            continue

    all_items_cache = temp_list
    logging.info(f"수집 완료: 총 {len(all_items_cache)}개 종목")

@app.on_event("startup")
def startup_event():
    fetch_krx_list_via_naver()

@app.get("/krx-list")
async def get_krx_step(start: int = 0, limit: int = 50):
    if not all_items_cache:
        fetch_krx_list_via_naver()
    
    sliced_data = all_items_cache[start:start+limit]
    
    return {
        "start": start,
        "count": len(sliced_data),
        "total_count": len(all_items_cache),
        "items": sliced_data
    }
