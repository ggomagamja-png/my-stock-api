from fastapi import FastAPI, Query
from pykrx import stock
import logging

app = FastAPI()

# 전역 변수로 데이터 캐싱
all_items_cache = []

def refresh_stock_cache():
    global all_items_cache
    logging.info("KRX 종목 리스트 캐싱 시작...")
    temp_list = []
    
    # 1. 주식 (KOSPI, KOSDAQ)
    for mkt in ["KOSPI", "KOSDAQ"]:
        tickers = stock.get_market_ticker_list(market=mkt)
        for t in tickers:
            # 주식은 이름 가져오기 속도가 중요하므로 일괄 처리 권장되나 
            # 여기서는 안정성을 위해 개별 매핑
            temp_list.append({"code": t, "name": stock.get_market_ticker_name(t), "type": "Stock"})
            
    # 2. ETF
    etf_tickers = stock.get_etf_ticker_list()
    for t in etf_tickers:
        temp_list.append({"code": t, "name": stock.get_etf_ticker_name(t), "type": "ETF"})
        
    # 3. ETN
    etn_tickers = stock.get_etn_ticker_list()
    for t in etn_tickers:
        temp_list.append({"code": t, "name": stock.get_etn_ticker_name(t), "type": "ETN"})
    
    all_items_cache = temp_list
    logging.info(f"캐싱 완료: 총 {len(all_items_cache)}개 종목")

# 앱 시작 시 한 번 실행
@app.on_event("startup")
def startup_event():
    refresh_stock_cache()

@app.get("/krx-list")
async def get_krx_step(start: int = 0, limit: int = 50):
    if not all_items_cache:
        refresh_stock_cache()
    
    end = start + limit
    sliced_data = all_items_cache[start:end]
    
    return {
        "start": start,
        "count": len(sliced_data),
        "total_count": len(all_items_cache),
        "items": sliced_data
    }
