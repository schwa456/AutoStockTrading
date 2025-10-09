from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from pykrx import stock
from datetime import datetime, timedelta
import pandas as pd
import math

class StockFundamentalToolInput(BaseModel):
    """Input Schema for TickerListTool"""
    ticker: str = Field(..., description="종목 티커")

class StockFundamentalTool(BaseTool):
    name: str = "StockFundamentalTool"
    description: str = "특정 종목(티커)의 기본 재무 정보를 조회하는 도구입니다. PER, PBR, EPS, BPS, DIV, DPS 정보를 딕셔너리 형태로 반환합니다."

    args_schema: Type[BaseModel] = StockFundamentalToolInput

    def _run(self, ticker: str)-> dict:
        today = datetime.now().strftime("%Y%m%d")

        try:
            df = stock.get_market_fundamental(today, ticker=ticker)

            if df.empty:
                return {"error": f"{ticker}에 대한 재무 정보를 찾을 수 없습니다."}

            fundamentals = df.iloc[-1].to_dict()
            return fundamentals

        except Exception as e:
            return {"error": f"{ticker}의 재무 정보 조회 중 오류 발생: {e}"}


class ValuationToolInput(BaseTool):
    """종목 가치 평가를 위한 스키마"""
    tickers: list[str] = Field(..., description="가치 평가를 수행할 종목 티커 리스트")

class ValuationTool(BaseTool):
    name: str = "Stock Valuation Tool"
    description: str = "주어진 종목 리스트에 대해 PER, PBR, ROE, 배당수익률을 기반으로 멀티 팩터 가치 평가를 수행하고 순위를 매깁니다."
    args_schema: Type[BaseModel] = ValuationToolInput

    def _run(self, tickers: list[str]) -> str:
        # 실제로는 복잡한 계산이 필요하지만, 테스트를 위해 간단한 텍스트를 반환합니다.
        today = datetime.now().strftime("%Y%m%d")

        all_fundamentals = []
        for ticker in tickers:
            try:
                # pykrx를 이용해 개별 종목의 펀더멘탈 데이터 조회
                f = stock.get_market_fundamental(today, ticker=ticker)

                # 계산에 필요한 값들이 0이 아닌 경우에만 데이터 추가
                if f['BPS'].iloc[0] > 0 and f['PER'].iloc[0] > 0 and f['PBR'].iloc[0] > 0:
                    fund_dict = f.to_dict('records')[0]
                    fund_dict['ticker'] = ticker

                    # ROE 계산 (EPS / BPS) * 100
                    fund_dict['ROE'] = (fund_dict['EPS'] / fund_dict['BPS']) * 100 if fund_dict['BPS'] > 0 else 0
                    all_fundamentals.append(fund_dict)

            except Exception as e:
                # 데이터를 가져오지 못한 경우 무시하고 계속 진행
                print(f"티커 {ticker}의 데이터를 가져오는데 실패했습니다.: {e}")
                continue

        if not all_fundamentals:
            return "유효한 펀더멘탈 데이터를 가진 종목이 없습니다."

        # 데이터 프레임으로 변환
        df = pd.DataFrame(all_fundamentals)

        # 순위 계산: PER, PBR은 낮을수록 순위가 높고(오름차순), DIV, ROE는 높을수록 순위가 높음
        # rank(ascending=True)가 낮은 값에 높은 순위(1위)를 부여함
        per_rank = df['PER'].rank(ascending=True)
        pbr_rank = df['PBR'].rank(ascending=True)
        div_rank = df['DIV'].rank(ascending=False)
        roe_rank = df['ROE'].rank(ascending=False)

        # 각 팩터의 순위를 합산하여 종합 순위 계산
        df['total_rank'] = per_rank + pbr_rank + div_rank + roe_rank

        # 종합 순위를 기준으로 오름차순 정렬 (숫자가 낮을수록 좋은 것)
        result_df = df.sort_values(by='total_rank', ascending=True)

        # 최종 결과에서 필요한 컬럼만 선택
        final_df = result_df[['ticker', 'PER', 'PBR', 'DIV', 'ROE', 'total_rank']]

        # 결과를 문자열로 변환하여 반환
        return f"멀티 팩터 가치 평가 결과: \n{final_df.to_string()}"