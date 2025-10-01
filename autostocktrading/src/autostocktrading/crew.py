from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from langchain.tools import DuckDuckGoSearchRun
from typing import List

from langchain_ollama import OllamaLLM

from .tools.economic_tools import *
from .tools.market_data_tools import *
from .tools.financial_tools import *
from .tools.trading_tools import *
from .tools.portfolio_tools import *

@CrewBase
class Autostocktrading():
    """Autostocktrading crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    def __init__(self):
        self.ollama_llm = OllamaLLM(model='ollama/exaone-deep')
        self.search_tool = DuckDuckGoSearchRun()

    # 1: Market Trend Analyst
    @agent
    def market_trend_analyst(self) -> Agent:
        return Agent(
            role='Market Trend Analyst',
            goal='현재 보유 포트폴리오와 시장 상황을 종합 분석하여, 리밸런싱을 포함한 최적의 투자 방향을 결정한다.',
            backstory="경제와 산업 전반을 아우르는 넓은 시야를 가진 분석가. 데이터와 최신 트렌드를 결합하여 미래 시장을 예측하는 능력이 탁월하다.",
            tools=[self.search_tool, KREconomicIndicatorTool(), USEconomicIndicatorTool(), PortfolioReaderTool()],
            verbose=True,
            llm=self.ollama_llm
        )

    # 2: Sector Researcher
    @agent
    def sector_researcher(self) -> Agent:
        return Agent(
            role='Sector Researcher',
            goal='성장 가능성이 높은 투자 섹터와 해당 섹터 내 유망 기업을 찾아낸다.',
            backstory=(
                "거시 경제와 산업 트렌드 분석의 대가. "
                "최신 기술, 정책 변화, 사회적 트렌드를 분석하여 미래 유망 산업을 예측한다. "
                "특히, 한국 시장 분석을 위해 네이버 뉴스(news.naver.com)의 정보를 최우선으로 활용하여 "
                "신뢰도 높은 분석을 수행한다."
            ),
            tools=[self.search_tool],
            allow_delegation=False,
            verbose=True,
            llm=self.ollama_llm
        )

    # 3: Ticker Screener
    @agent
    def ticker_screener(self) -> Agent:
        return Agent(
            role='Ticker Screener',
            goal='주어진 투자 시장과 섹터에서 거래 가능한 모든 주식의 티커를 찾아 목록을 만든다.',
            backstory="대한민국 주식 시장의 베테랑. KOSPI와 KOSDAQ의 모든 종목을 꿰뚫고 있다.",
            tools=[TickerListTool()],
            allow_delegation=False,
            verbose=True,
            llm=self.ollama_llm
        )

    # 4: Fundamental Fetcher
    @agent
    def fundamental_fetcher(self) -> Agent:
        return Agent(
            role='Fundamental Fetcher',
            goal='주어진 주식 티커 목록에 대해 각 종목의 핵심 재무 지표를 수집한다.',
            backstory="꼼꼼하고 정확한 재무 분석가. 숫자를 통해 기업의 본질을 파악한다.",
            tools=[StockFundamentalTool()],
            allow_delegation=False,
            verbose=True,
            llm=self.ollama_llm
        )

    # 5: Valuation Analyst
    @agent
    def valuation_analyst(self) -> Agent:
        return Agent(
            role='Valuation Analyst',
            goal='수집된 재무 데이터를 기반으로 기업에 대한 멀티 팩터 점수를 매겨 투자 매력도를 평가한다.',
            backstory="퀀트 분석의 귀재. 다양한 가치 평가 모델을 활용하여 기업의 내재 가치를 정확하게 계산한다.",
            tools=[ValuationTool()],
            allow_delegation=False,
            verbose=True,
            llm=self.ollama_llm
        )

    # 6: ESG Analyst
    @agent
    def esg_analyst(self) -> Agent:
        return Agent(
            role='ESG Analyst',
            goal='기업의 사회적, 환경적 영향을 분석하여 잠재적인 윤리적 리스크를 식별한다.',
            backstory=(
                "당신은 기업의 재무적 성과 너머를 보는 윤리적 투자 전문가입니다."
                "뉴스기사, NGO 보고서, 소셜 미디어 등을 샅샅이 뒤져가며 기업의 숨겨진 사회적 리스크를 찾아내는 데 특화되어 있습니다."
            ),
            tools=[self.search_tool],
            verbose=True,
            llm=self.ollama_llm
        )

    # 7: Insider Ownership Analyst
    @agent
    def insider_ownership_analyst(self) -> Agent:
        return Agent(
            role='Insider Ownership Analyst',
            goal='기관 투자자 및 주요 주주의 자금 흐름과 지분 변동을 추적하여 시장의 숨은 의도를 파악한다.',
            backstory="시장의 '큰 손'들의 움직임을 쫓는 정보 분석가. 공시 정보와 데이터를 통해 시장의 신뢰도를 판단한다.",
            tools=[InsiderAnalysisTool()],
            allow_delegation=False,
            verbose=True,
            llm=self.ollama_llm
        )

    # 8: Risk Analyst
    @agent
    def risk_analyst(self) -> Agent:
        return Agent(
            role='Risk Analyst',
            goal='포트폴리오에 포함될 종목들 간의 상관관계 매트릭스를 생성하여 리스크를 최소화한다.',
            backstory="신중한 리스크 관리 전문가. 변동성과 종목 간 상관관계를 면밀히 분석하여 안정적인 포트폴리오를 구축한다.",
            tools=[RiskAnalysisTool()],
            allow_delegation=False,
            verbose=True,
            llm=self.ollama_llm
        )

    # 9: Allocator
    @agent
    def allocator(self) -> Agent:
        return Agent(
            role='Allocator',
            goal='분석된 데이터를 종합하여 각 종목에 대한 최적의 투자 비중을 결정한다.',
            backstory="포트폴리오 최적화의 마스터. 기대 수익률을 극대화하면서도 리스크를 통제하는 최적의 포지션 크기를 결정한다.",
            tools=[AllocationTool()],
            allow_delegation=False,
            verbose=True,
            llm=self.ollama_llm
        )

    # 10: Trader Planner
    @agent
    def trader_planner(self) -> Agent:
        return Agent(
            role='Trader Planner',
            goal='결정된 포트폴리오 비중에 따라 시장 상황을 고려하여 정확한 매수/매도 주문 계획을 수립한다.',
            backstory="실행력 있는 트레이딩 전략가. 거래 비용을 최소화할 수 있는 최적의 주문 시점과 방식을 결정한다.",
            tools=[TradingPlannerTool()],
            allow_delegation=False,
            verbose=True,
            llm=self.ollama_llm
        )

    # 11: Trade Executor
    @agent
    def trade_executor(self) -> Agent:
        return Agent(
            role="Trade Executor",
            goal="수립된 매매 계획을 오차 없이 정확하게 실행하고 그 결과를 기록한다.",
            backstory='냉철하고 신속한 판단력을 지닌 트레이더. 감정의 개입 없이 오직 계획에 따라서만 주문을 집행한다.',
            tools=[TradeExecutorTool()],
            verbose=True,
            llm=self.ollama_llm
        )


    # --- Tasks ---
    @task
    def trend_analysis_task(self) -> Task:
        return Task(config=self.tasks_config['trend_analysis_task'], agent=self.market_trend_analyst())

    @task
    def sector_research_task(self) -> Task:
        return Task(config=self.tasks_config['sector_research_task'], agent=self.sector_researcher())

    @task
    def ticker_screening_task(self) -> Task:
        return Task(config=self.tasks_config['ticker_screening_task'], agent=self.ticker_screener())

    @task
    def fundamental_fetching_task(self) -> Task:
        return Task(config=self.tasks_config['fundamental_fetching_task'], agent=self.fundamental_fetcher())

    @task
    def valuation_analysis_task(self) -> Task:
        return Task(config=self.tasks_config['valuation_analysis_task'], agent=self.valuation_analyst())

    @task
    def esg_analysis_task(self) -> Task:
        return Task(config=self.tasks_config['esg_analysis_task'], agent=self.esg_analyst())

    @task
    def insider_ownership_analysis_task(self) -> Task:
        return Task(config=self.tasks_config['insider_ownership_analysis_task'], agent=self.insider_ownership_analyst())

    @task
    def risk_analysis_task(self) -> Task:
        return Task(config=self.tasks_config['risk_analysis_task'], agent=self.risk_analyst())

    @task
    def allocation_task(self) -> Task:
        return Task(config=self.tasks_config['allocation_task'], agent=self.allocator())

    @task
    def trade_planning_task(self) -> Task:
        return Task(config=self.tasks_config['trade_planning_task'], agent=self.trader_planner())

    @task
    def trade_execution_task(self) -> Task:
        return Task(config=self.tasks_config['trade_execution_task'], agent=self.trade_executor())

    @crew
    def crew(self) -> Crew:
        """Creates the Autostocktrading crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )