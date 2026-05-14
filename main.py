from fastapi import FastAPI
import requests
import logging

# 로그 설정 (Render 로그에서 상세히 보기 위함)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

all_items_cache = []

def fetch_krx_list_via_naver():
    """네이버 금융 API를 사용하여 국내 전 종목 리스트 수집"""
    global all_items_cache
    temp_list = []
    
    # 우선 테스트를 위해 키워드를 핵심적인 것 위주로 압축하여 속도를 높입니다.
    keywords = [
        "ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ",
        "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", 
        "N", "O", "P", "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z"
    ]
    
    seen_codes = set()
    logger.info("데이터 수집 시작...")

    try:
        for kw in keywords:
            # st=1 (국내주식), r_format=json 설정 확인
            url = f"https://ac.finance.naver.com/ac?q={kw}&q_enc=utf-8&st=1&frm=stock&r_format=json"
            res = requests.get(url, timeout=5)
            
            if res.status_code != 200:
                logger.error(f"API 호출 실패: {kw} (Status: {res.status_code})")
                continue
                
            data = res.json()
            items_group = data.get('items', [])
            
            if items_group and len(items_group) > 0:
                items = items_group[0]
                for item in items:
                    # 네이버 응답 구조: [이름, 코드, ..., ..., 시장구분]
                    name = item[0]
                    code = item[1]
                    market_type = str(item[4]) 
                    
                    if market_type == '1' and code not in seen_codes:
                        if len(code) == 6 and code.isdigit():
                            temp_list.append({"code": code, "name": name, "type": "KRX"})
                            seen_codes.add(code)
                            
        # 이름순 정렬
        all_items_cache = sorted(temp_list, key=lambda x: x['name'])
        logger.info(f"수집 완료! 총 종목 수: {len(all_items_cache)}")
        
    except Exception as e:
        logger.error(f"수집 중 치명적 오류: {str(e)}")

@app.on_event("startup")
def startup_event():
    fetch_krx_list_via_naver()

@app.get("/krx-list")
async def get_krx_step(start: int = 0, limit: int = 50):
    global all_items_cache
    
    # 만약 리스트가 비어있다면 (서버 시작 시 실패했을 경우) 다시 시도
    if not all_items_cache:
        logger.info("캐시가 비어있어 재수집을 시도합니다.")
        fetch_krx_list_via_naver()
    
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
