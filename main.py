import requests
from fastapi import FastAPI, Query
import os

app = FastAPI()

# 세션 유지 (연결 재사용)
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

@app.get("/")
def read_root():
    """로그의 404 에러를 방지하기 위한 기본 경로"""
    return {"message": "Stock API is running. Use /stock?name=종목명"}

@app.get("/health")
def health_check():
    """Cron-job.org용 경로"""
    return {"status": "alive"}

@app.get("/stock")
def get_stock_info(name: str = Query(None)):
    if not name:
        return {"name": "N/A", "code": "N/A", "price": "0"}

    try:
        # 1. 종목명으로 코드 찾기 (API 방식 - 메모리 매우 적게 사용)
        search_url = f"https://ac.finance.naver.com/ac?q={name}&q_enc=euc-kr&st=111"
        res = session.get(search_url, timeout=5)
        data = res.json()
        
        items = data.get('items', [])
        if not items or not items[0]:
            return {"name": name, "code": "N/A", "price": "0"}
        
        stock_info = items[0][0]
        code = stock_info[0][0]
        real_name = stock_info[1][0]

        # 2. 실시간 시세 가져오기 (API 방식)
        price_url = f"https://polling.finance.naver.com/api/realtime?query=SERVICE_ITEM:{code}"
        price_res = session.get(price_url, timeout=5)
        price_data = price_res.json()
        
        # 현재가(nv) 추출
        price = price_data['result']['areas'][0]['datas'][0].get('nv', 0)

        return {
            "name": real_name,
            "code": code,
            "price": str(price)
        }

    except Exception as e:
        # 에러 발생 시 로그 출력 및 기본값 반환 (셧다운 방지)
        print(f"API Error: {e}")
        return {"name": name, "code": "Error", "price": "0"}

if __name__ == "__main__":
    import uvicorn
    # Render 포트 환경변수 적용
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
