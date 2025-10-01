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
            df = stock.get_market_fundamental(today, today, ticker)

            if df.empty:
                return {"error": f"{ticker}에 대한 재무 정보를 찾을 수 없습니다."}

            fundamentals = df.iloc[0].to_dict()
            return fundamentals

        except Exception as e:
            return {"error": f"{ticker}의 재무 정보 조회 중 오류 발생: {e}"}

class StockOHLCVToolInput(BaseModel):
    """Input Schema for StockOHLCVTool"""
    ticker: str = Field(..., description="종목 티커")
    from_date: str = Field(..., description="OHLCV 데이터 조회 시작일 (YYYYMMDD)")
    to_date: str = Field(..., description="OHLCV 데이터 조회 종료일 (YYYYMMDD)")

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

        return