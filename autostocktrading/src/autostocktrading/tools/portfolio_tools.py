from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
from pykrx import stock
from datetime import datetime, timedelta
import pandas as pd
import math

class RiskAnalysisToolInput(BaseTool):
    tickers: list[str] = Field(..., description="리스크 분석을 수행할 종목 티커 리스트")


class RiskAnalysisTool(BaseTool):
    name: str = "Risk Analysis Tool"
    description: str = "주어진 종목 리스트의 과거 주가 데이터를 기반으로 일일 수익률의 상관관계 매트릭스를 생성하여 포트폴리오의 분산 투자 리스크를 분석합니다. "
    args_schema: Type[BaseModel] = RiskAnalysisToolInput

    def _run(self, tickers: list[str]) -> str:
        # 분석 기간 설정 (최근 3개월)
        today = datetime.now()
        start_date = today - timedelta(days=90)

        today_str = today.strftime("%Y%m%d")
        start_date_str = start_date.strftime("%Y%m%d")

        try:
            # 각 티커의 종가 데이터를 모을 데이터 프레임 초기화
            close_prices_df = pd.DataFrame()

            for ticker in tickers:
                # OHLCV 데이터 조회
                df = stock.get_market_ohlcv(start_date_str, today_str, ticker)

                # 종가 데이터만 추출하여 시리즈에 티커 이름 할당
                close_series = df['종가'].rename(ticker)

                # 데이터 프레임에 병합
                close_prices_df = pd.concat([close_prices_df, close_series], axis=1)

            # 모든 데이터가 비어있는 열 제거 (예: 거래정지 종목)
            close_prices_df.dropna(axis=1, how='all', inplace=True)

            if close_prices_df.empty:
                return "유효한 주가 데이터를 가진 종목이 없습니다."

            # 일일 수익률 계산
            daily_returns = close_prices_df.pct_change().dropna()

            # 상관관계 매트릭스 계산
            correlation_matrix = daily_returns.corr()

            # 결과 해석 추가
            interpretation = (
                "\n\n[해석 가이드]\n"
                "- 1에 가까울수록 함께 움직이는 경향이 강해 분산 효과가 낮습니다.\n"
                "- 0에 가까울수록 서로 관련 없이 움직여 분산 효과가 좋습니다.\n"
                "- 음수(-) 값은 반대로 움직이는 경향을 의미하며, 분산 효과가 매우 높습니다.\n"
                "  (일반적으로 포트폴리오 내 모든 종목 간 상관계수 평균이 낮을수록 좋습니다.)"
            )

            return f"포트폴리오 리스크 분석 (상관관계 매트릭스): \n{correlation_matrix.to_string()}\n{interpretation}"


        except Exception as e:
            print(f"리스크 분석 중 오류가 발생했습니다: {e}")


class AllocationToolInput(BaseTool):
    tickers: list[str] = Field(..., description="비중을 할당할 종목 티커 리스트")

class AllocationTool(BaseTool):
    name: str = "Portfolio Allocation Tool"
    description: str = "주어진 종목 리스트에 대해 '역변동성 가중치' 전략을 사용하여 각 종목의 최적 투자 비중을 결정합니다."
    args_schema: Type[BaseTool] = AllocationToolInput

    def _run(self, tickers: list[str]) -> str:
        # 분석 기간 설정 (최근 3개월)
        today = datetime.now()
        start_date = today - timedelta(days=90)

        today_str = today.strftime("%Y%m%d")
        start_date_str = start_date.strftime("%Y%m%d")

        try:
            # 각 티커의 종가 데이터를 모을 데이터 프레임 초기화
            close_prices_df = pd.DataFrame()

            for ticker in tickers:
                # OHLCV 데이터 조회
                df = stock.get_market_ohlcv(start_date_str, today_str, ticker)

                # 종가 데이터만 추출하여 시리즈에 티커 이름 할당
                close_series = df['종가'].rename(ticker)

                # 데이터 프레임에 병합
                close_prices_df = pd.concat([close_prices_df, close_series], axis=1)

            # 모든 데이터가 비어있는 열 제거 (예: 거래정지 종목)
            close_prices_df.dropna(axis=1, how='all', inplace=True)

            if close_prices_df.empty:
                return "비중을 계산할 유효한 주가 데이터를 가진 종목이 없습니다."

            # 일일 수익률 계산
            daily_returns = close_prices_df.pct_change().dropna()

            # 각 종목의 변동성(일일 수익률의 표준편차) 계산
            volatilities = daily_returns.std()

            # 변동성의 역수 계산
            inverse_volatilities = 1 / volatilities

            # 역변동성의 총합 계산
            total_inverse_volatilities = inverse_volatilities.sum()

            # 각 종목의 가중치(비중) 계산
            weights = inverse_volatilities / total_inverse_volatilities

            # 결과를 퍼센트(%)로 변환하여 딕셔너리로 저장
            allocation_dict = (weights * 100).round(2).to_dict()

            summary_lines = ["역변동성 전략 기반 포트폴리오 비중 할당 결과:"]
            for ticker, weight in allocation_dict.items():
                summary_lines.append(f"  - 종목 {ticker}: {weight:.2f}")

            return "\n".join(summary_lines)


        except Exception as e:
            return f"비중 할당 중 오류가 발생했습니다.: {e}"