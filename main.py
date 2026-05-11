from fastapi import FastAPI, HTTPException
import requests
from bs4 import BeautifulSoup

app = FastAPI()

@app.get("/stock")
def get_stock_info(name: str):
    if not name:
        raise HTTPException(status_code=400, detail="종목 이름을 입력하세요.")

    # 네이버 검색 URL
    url = f"https://search.naver.com/search.naver?query={name}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
    }
    
    try:
        res = requests.get(url, headers=headers)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')

        # 종목 코드 추출
        code_tag = soup.select_one(".stk_nm + .stk_cd")
        code = code_tag.text if code_tag else "N/A"

        # 현재 가격 추출
        price_tag = soup.select_one(".spt_con strong")
        price = price_tag.text if price_tag else "N/A"

        if code == "N/A" and price == "N/A":
            return {"message": f"'{name}'에 대한 정보를 찾을 수 없습니다. 정확한 종목명인지 확인해주세요."}

        return {
            "name": name,
            "code": code,
            "price": price
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Render 환경의 PORT 번호에 대응하기 위해 uvicorn 실행 설정
    uvicorn.run(app, host="0.0.0.0", port=8000)
