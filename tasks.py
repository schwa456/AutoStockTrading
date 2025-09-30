from crewai import Task
from agents import ticker_screener, fundamental_fetcher

# Task 1: Ticker Screening Task (종목 발굴 임무)
screen_tickers_task = Task(
    description='KOSPI 시장에 상장된 모든 주식의 티커 목록을 조회하세요.',
    expected_output='KOSPI 시장의 모든 티커가 포함된 파이썬 리스트(list).',
    agent=ticker_screener
)

# Task 2: Fundamental Fetching Task (재무 정보 수집 임무)
fetch_fundamentals_task = Task(
    description='제공된 티커 리스트의 각 종목에 대한 기본 재무 정보(PER, PBR, EPS, BPS, DIV, DPS)를 조회하세요. 모든 티커에 대한 정보를 수집해야 합니다.',
    expected_output='각 티커를 키(key)로 하고, 해당 티커의 재무 정보를 값(value)으로 하는 파이썬 딕셔너리(dictionary).',
    agent=fundamental_fetcher,
    context=[screen_tickers_task] # 이전 태스크의 결과를 사용
)