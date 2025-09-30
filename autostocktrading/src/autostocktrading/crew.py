from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from .tools.market_data_tools import *

@CrewBase
class Autostocktrading():
    """Autostocktrading crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    @agent
    def sector_researcher(self) -> Agent:
        return Agent(
            role='Sector Reasercher',
            goal='성장 가능성이 높은 투자 섹터와 해당 섹터 내 유망 기업을 찾아낸다.',
            backstory=(
                "당신은 거시 경제와 산업 트렌드 분석의 대가입니다. "
                "최신 기술, 정책 변화, 사회적 트렌드를 분석하여 미래 유망 산업을 예측하고, "
                "그 안에서 돋보이는 기업을 발굴하는 능력이 탁월합니다."
            ),
            # TODO: 뉴스, 산업 리포트 등을 분석할 수 있는 도구 추가 필요 (예: 웹 스크레이핑 툴)
            tools=[],
            allow_delegation=False,
            verbose=True
        )

    @agent
    def ticker_screener(self) -> Agent:
        return Agent(
            role='Ticker Screener',
            goal='주어진 투자 시장(KOSPI 또는 KOSDAQ)에서 거래 가능한 모든 주식의 티커를 찾아 목록을 만든다.',
            backstory=(
                "당신은 대한민국 주식 시장의 베테랑입니다."
                "KOSPI와 KOSDAQ의 모든 종목을 꿰뚫고 있으며,"
                "어떤 종목이 거래 가능한지 신속하게 판단하여 목록을 제공하는 역할을 맡고 있습니다."
            ),
            tools=[TickerListTool],
            allow_delegation=False,
            verbose=True
        )

    # 3: Fundamental Fetcher
    @agent
    def fundamental_fetcher(self) -> Agent:
        return Agent(
            role='Fundamental Fetcher',
            goal='주어진 주식 티커 목록에 대해 각 종목의 핵심 재무 지표(PER, PBR, EPS 등)를 수집한다.',
            backstory=(
                "당신은 꼼꼼하고 정확한 재무 분석가입니다."
                "기업의 재무제표를 신뢰하며, 숫자를 통해 기업의 본질을 파악하는 것을 중요하게 생각합니다."
                "주어진 종목들의 재무 데이터를 빠짐없이 수집하여 다음 분석 단계로 넘기는 임무를 수행합니다."
            ),
            tools=[StockFundamentalTool],
            allow_delegation=False,
            verbose=True
        )

    # 4: Valuation Analyst
    @agent
    def valuation_analyst(self) -> Agent:
        return Agent(
            role='Valuation Analyst',
            goal='수집된 재무 데이터를 기반으로 기업에 대한 멀티 팩터 점수를 매겨 투자 매력도를 평가한다.',
            backstory=(
                "당신은 퀀트 분석의 귀재입니다. 다양한 가치 평가 모델(DCF, RIM 등)과 팩터(모멘텀, 퀄리티, 가치)를 활용하여 "
                "기업의 내재 가치를 정확하게 계산하고, 이를 바탕으로 객관적인 투자 점수를 부여합니다."
            ),
            # TODO: 재무 데이터를 기반으로 가치 평가를 수행하는 도구 추가 필요
            tools=[],
            allow_delegation=False,
            verbose=True
        )

    # 5: Insider Ownership Analyst
    @agent
    def insider_ownership_analyst(self) -> Agent:
        return Agent(
            role='Insider Ownership Analyst',
            goal='기관 투자자 및 주요 주주의 자금 흐름과 지분 변동을 추적하여 시장의 숨은 의도를 파악한다.',
            backstory=(
                "당신은 시장의 '큰 손'들의 움직임을 쫓는 정보 분석가입니다. "
                "공시 정보와 뉴스, 데이터 분석을 통해 기관과 외국인의 매매 동향, 내부자 거래 내역을 추적하고 "
                "이를 통해 해당 종목에 대한 시장의 신뢰도를 판단합니다."
            ),
            # TODO: 기관/외국인 수급 데이터, 지분 공시 등을 가져오는 도구 추가 필요
            tools=[],
            allow_delegation=False,
            verbose=True
        )

    # 6: Risk Analyst
    @agent
    def risk_analyst(self) -> Agent:
        return Agent(
            role='Risk Analyst',
            goal='포트폴리오에 포함될 종목들 간의 상관관계 매트릭스를 생성하여 분산 투자 효과를 분석하고 리스크를 최소화한다.',
            backstory=(
                "당신은 신중한 리스크 관리 전문가입니다. '계란을 한 바구니에 담지 말라'는 격언을 신봉하며, "
                "수익률뿐만 아니라 변동성과 종목 간 상관관계를 면밀히 분석하여 "
                "시장 변동에도 흔들리지 않는 안정적인 포트폴리오를 구축하는 임무를 맡고 있습니다."
            ),
            # TODO: 종목들의 과거 주가 데이터를 기반으로 상관관계 행렬을 계산하는 도구 추가 필요
            tools=[StockOHLCVTool],
            allow_delegation=False,
            verbose=True
        )

    # 7: Allocator
    @agent
    def allocator(self) -> Agent:
        return Agent(
            role='Allocator',
            goal='분석된 데이터(가치 평가, 리스크 등)를 종합하여 각 종목에 대한 최적의 투자 비중을 결정한다.',
            backstory=(
                "당신은 포트폴리오 최적화의 마스터입니다. 마코위츠의 현대 포트폴리오 이론(MPT)을 비롯한 다양한 "
                "자산 배분 모델을 활용하여, 기대 수익률을 극대화하면서도 리스크를 통제하는 최적의 포지션 크기를 결정합니다."
            ),
            # TODO: 최적 포트폴리오 비중을 계산하는 도구 (예: 최적화 라이브러리 연동) 추가 필요
            tools=[],
            allow_delegation=False,
            verbose=True
        )

    # 8: Trader Planner (신규 추가)
    @agent
    def trader_planner(self) -> Agent:
        return Agent(
            role='Trader Planner',
            goal='결정된 포트폴리오 비중에 따라 시장 상황을 고려하여 정확한 매수/매도 주문 계획을 수립한다.',
            backstory=(
                "당신은 실행력 있는 트레이딩 전략가입니다. 시장의 미세한 움직임을 포착하고, "
                "거래 비용(슬리피지, 수수료)을 최소화할 수 있는 최적의 주문 시점과 방식을 결정합니다. "
                "분석가들의 결정을 실제 주문으로 연결하는 마지막 관문을 책임집니다."
            ),
            # TODO: 실제 주문(또는 모의 주문)을 생성하는 기능 추가 필요
            tools=[],
            allow_delegation=False,
            verbose=True
        )

    @task
    def sector_research(self) -> Task:
        return Task(
            config=self.task_config['sector_research_task'],
            agent=self.sector_researcher()
        )

    @task
    def ticker_screening(self) -> Task:
        return Task(
            config=self.task_config['ticker_screening_task'],
            agent=self.ticker_screener()
        )

    @task
    def fundamental_fetching(self) -> Task:
        return Task(
            config=self.task_config['fundamental_fetching_task'],
            agent=self.fundamental_fetcher()
        )

    #TODO: 나머지 Task도 연결

    @crew
    def crew(self) -> Crew:
        """Creates the Autostocktrading crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
