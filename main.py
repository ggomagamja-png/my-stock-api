import requests
from fastapi import FastAPI, HTTPException
import os

app = FastAPI()

# 세션 관리 및 헤더 설정
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
        # Step 1: 종목명으로 종목 코드 찾기 (네이버 자동완성 API 활용 - 매우 가볍고 빠름)
        search_url = f"https://ac.finance.naver.com/ac?q={name}&q_enc=euc-kr&st=111"
        res = session.get(search_url, timeout=5)
        data = res.json()
        
        # 검색 결과 추출
        items = data.get('items', [])
        if not items or not items[0]:
            return {"name": name, "code": "N/A", "price": "검색결과없음"}
        
        # 첫 번째 검색 결과에서 코드와 실제 이름 추출
        # items[0][0][0]은 코드, [0][1][0]은 종목명
        stock_info = items[0][0]
        code = stock_info[0][0]
        real_name = stock_info[1][0]

        # Step 2: 현재가 가져오기 (네이버 증권 실시간 시세 API 활용 - HTML 파싱 없음)
        # 이 방식은 HTML 전체를 긁지 않아 서버 셧다운 위험이 거의 없습니다.
        price_url = f"https://polling.finance.naver.com/api/realtime?query=SERVICE_ITEM:{code}"
        price_res = session.get(price_url, timeout=5)
        price_data = price_res.json()
        
        # 실시간 가격 데이터 추출
        item_data = price_data.get('result', {}).get('areas', [{}])[0].get('datas', [{}])[0]
        price = item_data.get('nv', "0") # 'nv'가 현재가(Now Value)

        return {
            "name": real_name,
            "code": code,
            "price": str(price)
        }

    except Exception as e:
        print(f"Error: {e}")
        return {"name": name, "code": "Error", "price": "0"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
