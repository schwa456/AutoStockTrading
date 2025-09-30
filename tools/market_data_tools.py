from crewai_tools import tool
from pykrx import stock
from datetime import datetime
import pandas as pd

@tool("Market Ticker List Tool")
def get_ticker_list(market: str = "KOSPI") -> list:
    """
    지정한 시장(KOSPI, KOSDAQ)의 모든 종목 티커 목록을 조회하는 도구입니다.
    인자(argument)로 'KOSPI' 또는 'KOSDAQ'을 전달해야 합니다.
    """
    today = datetime.now().strftime("%Y%m%d")

    try:
        tickers = stock.get_market_ticker_list(today, market=market)
        return tickers
    except Exception as e:
        return [f"{market} 시장의 티커 목록을 가져오는데 실패했습니다: {e}"]

@tool("Stock Fundamental Info Tool")
def get_stock_fundamentals(ticker: str) -> dict:
    """
    특정 종목(티커)의 기본 재무 정보를 조회하는 도구입니다.
    PER, PBR, EPS, BPS, DIV, DPS 정보를 딕셔너리 형태로 반환합니다.
    """
    today = datetime.now().strftime("%Y%m%d")

    try:
        df = stock.get_market_fundamental(today, today, ticker)

        if df.empty:
            return {"error": f"{ticker}에 대한 재무 정보를 찾을 수 없습니다."}

        fundamentals = df.iloc[0].to_dict()
        return fundamentals

    except Exception as e:
        return {"error": f"{ticker}의 재무 정보 조회 중 오류 발생: {e}"}

@tool("Stock OHLCV Data Tool")
def get_stock_ohlcv(ticker: str, from_date: str, to_date: str) -> pd.DataFrame:
    """
    특정 종목(티커)의 지정된 기간 동안의 OHLCV(시가, 고가, 저가, 종가, 거래량) 데이터를 조회하는 도구입니다.
    날짜 형식은 'YYYYMMDD'여야 합니다.
    """
    try:
        df = stock.get_market_ohlcv(from_date, to_date, ticker)
        return df

    except Exception as e:
        return f"{ticker}의 OHLCV 데이터 조회 중 오류 발생: {e}"