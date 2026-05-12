import requests
from fastapi import FastAPI
import os

app = FastAPI()

# 세션 유지 (성능 최적화)
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

@app.get("/health")
def health_check():
    return {"status": "alive"}

@app.get("/stock")
def get_stock_info(name: str):
    if not name:
        return {"name": name, "code": "N/A", "price": "0"}

    try:
        # 1. 종목 코드 찾기 (네이버 자동완성 API - HTML 파싱 없음)
        # 이 주소는 오직 텍스트 데이터만 반환하므로 매우 가볍습니다.
        search_url = f"https://ac.finance.naver.com/ac?q={name}&q_enc=euc-kr&st=111"
        res = session.get(search_url, timeout=3)
        data = res.json()
        
        items = data.get('items', [])
        if not items or not items[0]:
            return {"name": name, "code": "N/A", "price": "0"}
        
        # 데이터 구조에서 코드와 이름 추출
        stock_info = items[0][0]
        code = stock_info[0][0]
        real_name = stock_info[1][0]

        # 2. 현재가 가져오기 (네이버 실시간 시세 API - HTML 파싱 없음)
        price_url = f"https://polling.finance.naver.com/api/realtime?query=SERVICE_ITEM:{code}"
        price_res = session.get(price_url, timeout=3)
        price_data = price_res.json()
        
        # 'nv' 필드가 현재가(Now Value)입니다.
        price = price_data['result']['areas'][0]['datas'][0].get('nv', 0)

        return {
            "name": real_name,
            "code": code,
            "price": str(price)
        }

    except Exception as e:
        return {"name": name, "code": "Error", "price": "0"}

if __name__ == "__main__":
    import uvicorn
    # Render의 환경변수 포트를 사용하며 워커를 1개로 제한하여 메모리 보호
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port, workers=1)
