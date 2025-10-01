from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from pykrx import stock
from datetime import datetime, timedelta
import pandas as pd
import math

class TickerListToolInput(BaseModel):
    """Input Schema for TickerListTool"""
    market: str = Field(..., description="지정된 시장 이름(KOSPI, KOSDAQ)")

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

class InsiderAnalysisToolInput(BaseTool):
    tickers: list[str] = Field(..., description="수급 분석을 수행할 종목 티커 리스트")

class InsiderAnalysisTool(BaseTool):
    name: str = "Insider Trading Analysis Tool"
    description: str = "주어진 종목 리스트에 대해 최근 한 달간의 기관 및 외국인 투자자의 순매수 동향을 분석합니2다."
    args_schema: Type[BaseModel] = InsiderAnalysisToolInput

    def _run(self, tickers: list[str]) -> str:
        # 분석 기간 설정 (최근 한 달)
        today = datetime.now()
        start_date = today - timedelta(days=30)

        today_str = today.strftime("%Y%m%d")
        start_date_str = start_date.strftime("%Y%m%d")

        results = []
        for ticker in tickers:
            try:
                # pykrx를 이용해 투자자별 거래대금 데이터 조회
                df = stock.get_market_trading_value_by_date(start_date_str, today_str, ticker)

                # '기관계'와 '외국인'의 순매수 금액 합계 계산
                # 순매수 = 매수 - 매도. pykrx 데이터는 이미 순매수 금액을 제공합니다.
                inst_net_purchase = df['기관계'].sum()
                foreign_net_purchase = df['외국인'].sum()

                # 분석 결과를 딕셔너리로 저장
                results.append({
                    'ticker': ticker,
                    'inst_net_purchase': inst_net_purchase,
                    'foreign_net_purchase': foreign_net_purchase
                })

            except Exception as e:
                print(f"티커 {ticker}의 수급 데이터를 가져오는데 실패했습니다.: {e}")
                continue

        if not results:
            return "유효한 수급 데이터를 가진 종목이 없습니다."

        # 결과 요약 문자열 생성
        summary_lines = ["기관 및 외국민 수급 분석 결과 (최근 한 달 누적):"]

        for res in results:
            inst_trend = "순매수" if res['inst_net_purchase'] > 0 else "순매도"
            foreign_trend = "순매수" if res['foreign_net_purchase'] > 0 else "순매도"

            # 금액 단위를 읽기 쉽게 '억 원' 단위로 변환
            inst_amount_in_billions = res['inst_net_purchase'] / 1_000_000_00
            foreign_amount_in_billions = res['foreign_net_purchase'] / 1_000_000_00

            line = (
                f"  - 종목 {res['ticker']}: "
                f"기관 {inst_trend} ({inst_amount_in_billions:,.1f}억 원), "
                f"외국인 {foreign_trend} ({foreign_amount_in_billions:,.1f}억 원), "
            )

            summary_lines.append(line)

        return "\n".join(summary_lines)



