from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from pykrx import stock
from datetime import datetime
import pandas as pd

class TickerListToolInput(BaseModel):
    """Input Schema for TickerListTool"""
    market: str = Field(..., description="Name of designated market('KOSPI', 'KOSDAQ')")

class TickerListTool(BaseTool):
    name: str = "TickerListTool"
    description: str = (
        "지정한 시장(KOSPI, KOSDAQ)의 모든 종목 티커 목록을 조회하는 도구입니다."
    )

    args_schema: Type[BaseModel] = TickerListToolInput

    def _run(self, market: str) -> list:
        today = datetime.now().strftime("%Y%m%d")

        try:
            tickers = stock.get_market_ticker_list(today, market=market)
            return tickers

        except Exception as e:
            return [f"{market} 시장의 티커 목록을 가져오는데 실패했습니다: {e}"]

class StockFundamentalToolInput(BaseModel):
    """Input Schema for TickerListTool"""
    ticker: str = Field(..., description="Ticker name for retrieving fundamental data.")

class StockFundamentalTool(BaseTool):
    name: str = "StockFundamentalTool"
    description: str = "특정 종목(티커)의 기본 재무 정보를 조회하는 도구입니다. PER, PBR, EPS, BPS, DIV, DPS 정보를 딕셔너리 형태로 반환합니다."

    args_schema: Type[BaseModel] = StockFundamentalToolInput

    def _run(self, ticker: str)-> dict:
        today = datetime.now().strftime("%Y%m%d")

        try:
            df = stock.get_market_fundamental(today, today, ticker)

            if df.empty:
                return {"error": f"{ticker}에 대한 재무 정보를 찾을 수 없습니다."}

            fundamentals = df.iloc[0].to_dict()
            return fundamentals

        except Exception as e:
            return {"error": f"{ticker}의 재무 정보 조회 중 오류 발생: {e}"}

class StockOHLCVToolInput(BaseModel):
    """Input Schema for StockOHLCVTool"""
    ticker: str = Field(..., description="Ticker name for retrieving OHLCV data.")
    from_date: str = Field(..., description="Start date for retrieving OHLCV data.")
    to_date: str = Field(..., description="End date for retrieving OHLCV data.")

class StockOHLCVTool(BaseModel):
    name: str = "StockOHLCVTool"
    description: str = "특정 종목(티커)의 지정된 기간 동안의 OHLCV(시가, 고가, 저가, 종가, 거래량) 데이터를 조회하는 도구입니다. 날짜 형식은 'YYYYMMDD'여야 합니다."

    args_schema: Type[BaseModel] = StockOHLCVToolInput

    def _run(self, ticker: str, from_date: str, to_date: str) -> pd.DataFrame:
        try:
            df = stock.get_market_ohlcv(from_date, to_date, ticker)
            return df

        except Exception as e:
            return f"{ticker}의 OHLCV 데이터 조회 중 오류 발생: {e}"


# 5. Insider Ownership Analyst를 위한 도구
class InstitutionalFlowInput(BaseModel):
    """기관/외국인 순매수 정보 조회를 위한 입력 스키마"""
    ticker: str = Field(..., description="종목 티커")
    from_date: str = Field(..., description="조회 시작일 (YYYYMMDD)")
    to_date: str = Field(..., description="조회 종료일 (YYYYMMDD)")


class InstitutionalFlowTool(BaseTool):
    name: str = "Institutional Trading Flow"
    description: str = "특정 기간 동안의 기관 및 외국인 누적 순매수 거래대금 정보를 조회합니다."
    args_schema: Type[BaseModel] = InstitutionalFlowInput

    def _run(self, ticker: str, from_date: str, to_date: str) -> pd.DataFrame:
        df = stock.get_market_trading_value_by_date(from_date, to_date, ticker)
        # 기관, 외국인 순매수 합계 계산 등 추가적인 가공 가능
        return df


# 6. Risk Analyst를 위한 도구
class CorrelationMatrixInput(BaseModel):
    """상관관계 매트릭스 생성을 위한 입력 스키마"""
    tickers: list[str] = Field(..., description="종목 티커 리스트")
    from_date: str = Field(..., description="조회 시작일 (YYYYMMDD)")
    to_date: str = Field(..., description="조회 종료일 (YYYYMMDD)")


class CorrelationMatrixTool(BaseTool):
    name: str = "Stock Correlation Matrix"
    description: str = "주어진 종목들의 특정 기간 동안의 일일 수익률을 기반으로 상관관계 행렬을 생성합니다."
    args_schema: Type[BaseModel] = CorrelationMatrixInput

    def _run(self, tickers: list[str], from_date: str, to_date: str) -> pd.DataFrame:
        close_prices = {}
        for ticker in tickers:
            df = stock.get_market_ohlcv_by_date(from_date, to_date, ticker)
            close_prices[ticker] = df['종가']

        price_df = pd.DataFrame(close_prices)
        daily_returns = price_df.pct_change().dropna()
        correlation_matrix = daily_returns.corr()
        return correlation_matrix

class MockValuationTool(BaseTool):
    name: str = "Mock Valuation Tool"
    description: str = "재무 데이터를 바탕으로 멀티 팩터 점수를 매기는 것을 시뮬레이션합니다."

    def _run(self, **kwargs) -> str:
        # 실제로는 복잡한 계산이 필요하지만, 테스트를 위해 간단한 텍스트를 반환합니다.
        return "선별된 5개 종목에 대한 멀티 팩터 점수: A(95), B(92), C(88), D(85), E(81)"

class MockInsiderAnalysisTool(BaseTool):
    name: str = "Mock Insider Ownership Analysis Tool"
    description: str = "기관 자금 흐름을 추적하는 것을 시뮬레이션합니다."

    def _run(self, **kwargs) -> str:
        return "최근 1개월간 기관은 종목 A, C에 대해 순매수, 종목 B, D, E에 대해서는 중립 포지션을 유지함."

class MockRiskAnalysisTool(BaseTool):
    name: str = "Mock Risk Analysis Tool"
    description: str = "상관관계 매트릭스를 생성하는 것을 시뮬레이션합니다."

    def _run(self, **kwargs) -> str:
        return "종목 A와 C는 높은 양의 상관관계, 나머지 종목과는 낮은 상관관계를 보임. 포트폴리오 분산 효과 양호."

class MockAllocationTool(BaseTool):
    name: str = "Mock Allocator Tool"
    description: str = "포지션 크기를 결정하는 것을 시뮬레이션합니다."

    def _run(self, **kwargs) -> str:
        return "최적 포트폴리오 비중 결정: 종목 A(30%), C(30%), B(20%), E(20%). 종목 D는 제외."

class MockTradingPlannerTool(BaseTool):
    name: str = "Mock Trader Planner Tool"
    description: str = "매수 주문 계획을 결정하는 것을 시뮬레이션합니다."

    def _run(self, **kwargs) -> str:
        return "최종 매수 계획: 종목 A, C는 장 시작 동시호가에 시장가 매수. 종목 B, E는 현재가 대비 -1% 지정가 매수."