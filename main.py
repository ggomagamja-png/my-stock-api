from fastapi import FastAPI
import requests
import logging


app = FastAPI()

all_items_cache = []

def fetch_krx_list_via_naver():
    """한글 및 영문 키워드를 조합하여 전 종목 리스트 수집"""
    global all_items_cache
    temp_list = []
    
    # 1. 한글 음절/초성 + 2. 알파벳 A-Z 키워드 결합
    keywords = [
        "가", "나", "다", "라", "마", "바", "사", "아", "자", "차", "카", "타", "파", "하",
        "ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ",
        "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", 
        "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"
    ]
    
    seen_codes = set()
    
    for kw in keywords:
        try:
            # 네이버 금융 자동완성 API
            url = f"https://ac.finance.naver.com/ac?q={kw}&q_enc=utf-8&st=1&frm=stock&r_format=json"
            res = requests.get(url, timeout=5)
            data = res.json()
            # items 구조: [ [ ["삼성전자", "005930", ...], ["SK하이닉스", "000660", ...] ] ]
            items_group = data.get('items', [])
            if not items_group: continue
            
            items = items_group[0]
            
            for item in items:
                name = item[0]
                code = item[1]
                market_type = item[4] # '1'은 국내, '2'는 해외 등
                
                # 중복 제거 및 국내 종목(6자리 숫자) 필터링
                if code not in seen_codes and market_type == '1':
                    if len(code) == 6 and code.isdigit():
                        temp_list.append({
                            "code": code,
                            "name": name,
                            "type": "KRX"
                        })
                        seen_codes.add(code)
        except Exception as e:
            continue

    # 종목명 기준으로 정렬 (가나다-ABC 순)
    all_items_cache = sorted(temp_list, key=lambda x: x['name'])
    logging.info(f"수집 완료: 총 {len(all_items_cache)}개 종목 (영문 종목 포함)")

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
