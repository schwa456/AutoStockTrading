from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from pykrx import stock
from datetime import datetime, timedelta
import pandas as pd
import math

class TradingPlannerToolInput(BaseTool):
    portfolio_allocations: dict = Field(..., description="종목 티커와 할당된 비중(%)을 담은 딕셔너리")
    total_capital: int = Field(..., description="투입할 총 자본(원)")

class TradingPlannerTool(BaseTool):
    name: str = "Trader Execution Planner Tool"
    description: str = "제공된 포트폴리오 비중과 총 자본에 따라, 각 종목의 현재가를 기준으로 매수할 주식 수량을 계산하여 최종 매매 계획을 수립합니다."
    args_schema: Type[BaseTool] = TradingPlannerToolInput

    def _run(self, portfolio_allocations: dict, total_capital: int) -> str:

        trade_plan = []
        today_str = datetime.now().strftime("%Y%m%d")

        for ticker, weight in portfolio_allocations.items():
            try:
                # 할당된 금액 계산
                allocated_capital = total_capital * (weight / 100)

                # 현재 (또는 가장 최근) 주가 조회
                current_price_df = stock.get_market_ohlcv(today_str, today_str, ticker)
                if current_price_df.empty:
                    # 당일 데이터가 없으면 전일 종가 조회
                    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
                    current_price_df = stock.get_market_ohlcv(yesterday, yesterday, ticker)

                current_price = current_price_df['종가'].iloc[-1]

                if current_price == 0:
                    continue

                # 매수할 주식 수량 계산 (소수점 이하 버림)
                shares_to_buy = math.floor(allocated_capital / current_price)

                # 예상 주문 금액
                estimated_cost = shares_to_buy * current_price

                trade_plan.append({
                    "종목 티커": ticker,
                    "주문 방식": "시장가 매수",
                    "계산 기준가": f"{current_price:,.0f}원",
                    "매수 수량": f"{shares_to_buy}주",
                    "예상 주문 금액": f"{estimated_cost:,.0f}원",
                    "포트폴리오 비중": f"{weight:.2f}%"
                })

            except Exception as e:
                print(f"티커 {ticker}의 매매 계획 수립 중 오류 발생: {e}")
                continue

        if not trade_plan:
            return "매매 계획을 수립할 종목이 없습니다."

        # 결과를 데이터 프레임으로 변환하여 보기 좋게 출력
        plan_df = pd.DataFrame(trade_plan)

        return f"최종 매매 실행 계획서: \n{plan_df.to_string()}"