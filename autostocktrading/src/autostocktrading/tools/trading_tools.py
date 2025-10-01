from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from pykrx import stock
from datetime import datetime, timedelta
import pandas as pd
import math
import json

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

class PortfolioReaderTool(BaseTool):
    name: str = "Portfolio Reader Tool"
    description: str = "현재 보유 금액과 주식 포트폴리오 상태를 JSON 파일에서 읽어옵니다."

    def _run(self) -> str:
        try:
            with open('portfolio_json', 'r', encoding='utf-8') as f:
                portfolio = json.load(f)

            return f"현재 포트폴리오 상태: {json.dumps(portfolio, indent=2, ensure_ascii=False)}"

        except FileNotFoundError:
            return "오류: portfolio.json 파일을 찾을 수 없습니다."

        except Exception as e:
            return f"포트폴리오 조회 중 오류 발생: {e}"

class TradeExecutorToolInput(BaseModel):
    ticker: str = Field(..., description="매매할 종목의 티커")
    quantity: int = Field(..., description="매매할 주식의 수량")
    action: str = Field(..., description="수행할 동작 ('BUY' 또는 'SELL')")
    price: float = Field(..., description="매매가 체결된 주당 가격")

class TradeExecutorTool(BaseTool):
    name: str = "Trade Executor Tool"
    description: str = "계획에 따라 실제 주식 매수 또는 매도 주문을 실행하고, 그 결과를 portfolio.json 파일에 기록합니다."
    args_schema: Type[BaseModel] = TradeExecutorToolInput

    def _run(self, ticker: str, quantity: int, action: str, price: float) -> str:
        # 이 도구는 실제 증권사 API와 연동되어야 하지만,
        # 여기서는 모의 거래로 portfolio.json 파일을 업데이트하는 역할만 합니다.
        try:
            with open('portfolio_json', 'r', encoding='utf-8') as f:
                portfolio = json.load(f)

                if action.upper() == 'BUY':
                    cost = quantity * price
                    if portfolio['cash'] < cost:
                        return f"주문 실패: 현금 부족 (필요: {cost:,.0f}원, 보유: {portfolio['cash']:,.0f}원"

                    portfolio['cash'] -= cost

                    # 이미 보유한 종목인지 확인
                    found = False
                    for stock in portfolio['stocks']:
                        if stock['ticker'] == ticker:
                            # 평균 매수 단가 재계산
                            total_cost = (stock['purchase_price'] * stock['quantity']) + cost
                            total_quantity = stock['quantity'] + quantity
                            stock['purchase_price'] = total_cost / total_quantity
                            stock['quantity'] = total_quantity
                            found = True
                            break
                    if not found:
                        portfolio['stocks'].append({
                            'ticker': ticker,
                            'quantity': quantity,
                            'purchase_price': price
                        })

                elif action.upper() == 'SELL':
                    income = quantity * price

                    stock_to_sell = None
                    for stock in portfolio['stocks']:
                        if stock['ticker'] == ticker:
                            stock_to_sell = stock
                            break

                    if not stock_to_sell:
                        return f"주문 실패: 보유하지 않은 종목({ticker})입니다."

                    if stock_to_sell['quantity'] < quantity:
                        return f"주문 실패: 보유 수량 부족 ({ticker} - 보유: {stock_to_sell['quantity']}주, 매도 요청: {quantity}주)"

                    # 보유 수량을 줄이고 현금을 늘립니다.
                    stock_to_sell['quantity'] -= quantity
                    portfolio['cash'] += income

                    # 만약 매도 후 수량이 0이 되면 포트폴리오에서 해당 종목을 제거합니다.
                    if stock_to_sell['quantity'] == 0:
                        portfolio['stocks'] = [s for s in portfolio['stocks'] if s['ticker'] != ticker]

                else:
                    return f"주문 실패: 알 수 없는 동작('{action}')입니다. 'BUY' 또는 'SELL'만 가능합니다."

                # 파일의 맨 앞으로 이동하여 덮어쓰기
                f.seek(0)
                json.dump(portfolio, f, indent=2, ensure_ascii=False)
                f.truncate()
                return f"주문 성공: {ticker} {quantity}주 {action} 완료. 현재 포트폴리오가 업데이트되었습니다."

        except Exception as e:
            return f"거래 실행 중 오류 발생: {e}"