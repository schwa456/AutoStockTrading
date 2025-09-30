from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from .tools.market_data_tools import *
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

@CrewBase
class Autostocktrading():
    """Autostocktrading crew"""

    agents: List[BaseAgent]
    tasks: List[Task]

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    
    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def researcher(self) -> Agent:
        return Agent(
            role='Ticker Screener',
            goal='주어진 투자 시장(KOSPI 또는 KOSDAQ)에서 거래 가능한 모든 주식의 티커를 찾아 목록을 만든다.',
            backstory=(
                "당신은 대한민국 주식 시장의 베테랑입니다."
                "KOSPI와 KOSDAQ의 모든 종목을 꿰뚫고 있으며,"
                "어떤 종목이 거래 가능한지 신속하게 판단하여 목록을 제공하는 역할을 맡고 있습니다."
            ),
            tools=[TickerListTool],
            allow_delegation=False, # 다른 에이전트에게 위임 비활성화
            verbose=True
        )

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

    @agent
    def reporting_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config['reporting_analyst'], # type: ignore[index]
            verbose=True
        )

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task'], # type: ignore[index]
        )

    @task
    def reporting_task(self) -> Task:
        return Task(
            config=self.tasks_config['reporting_task'], # type: ignore[index]
            output_file='report.md'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Autostocktrading crew"""
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
