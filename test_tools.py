from tools.market_data_tools import get_ticker_list, get_stock_fundamentals, get_stock_ohlcv
from datetime import datetime, timedelta

def test_market_data_tools():
    print("도구 테스트를 시작합니다.")

    # 1. KOSPI 시장의 티커 목록 조회 테스트
    print("\n--- 1. KOSPI 티커 목록 조회 ---")
    kospi_tickers = get_ticker_list.run("KOSPI")
    print(f"KOSPI 종목 수: {len(kospi_tickers)}")
    print(f"샘플 티커 5개: {kospi_tickers[:5]}")

    # 2. 삼성전자(005930) 재무 정보 조회 테스트
    print("\n--- 2. 삼성전자(005930) 재무 정보 조회 ---")
    samsung_fundamentals = get_stock_fundamentals.run("005930")
    print(samsung_fundamentals)

    # 3. SK하이닉스(000660) 최근 7일간 주가 조회 테스트
    print("\n--- 3. SK하이닉스(000660) 최근 7일간 주가 조회 ---")
    today = datetime.now()
    start_date = today - timedelta(days=7)

    today_str = today.strftime("%Y%m%d")
    start_date_str = start_date.strftime("%Y%m%d")

    skhynix_ohlcv = get_stock_ohlcv.run("000660", start_date_str, today_str)
    print(skhynix_ohlcv)

    print("\n✅ 모든 테스트가 완료되었습니다.")

if __name__ == '__main__':
    test_market_data_tools()