from dotenv import load_dotenv
load_dotenv()

from crewai import Crew, Process
from agents import ticker_screener, fundamental_fetcher
from tasks import screen_tickers_task, fetch_fundamentals_task
from langchain_ollama import OllamaLLM

ollama_llm = OllamaLLM(model="exaone-deep")
ollama_llm.supports_stop_words = lambda: False

ticker_screener.llm = ollama_llm
fundamental_fetcher.llm = ollama_llm

stock_analysis_crew = Crew(
    agents = [ticker_screener, fundamental_fetcher],
    tasks=[screen_tickers_task, fetch_fundamentals_task],
    process=Process.sequential,
    verbose=True
)

print("🚀 크루 실행을 시작합니다...")
result = stock_analysis_crew.kickoff()

print("\n\n✅ 크루 작업 완료!")
print("--------------------------------------------------")
print("최종 결과물:")

if isinstance(result, dict):
    print("결과물의 타입: Dictionary")
    print(f"총 {len(result)}개의 종목 정보를 수집했습니다.")
    print("\n샘플 데이터 (처음 5개):")

    count = 0
    for ticker, data in result.items():
        if count < 5:
            print(f"{ticker}: {data}")
            count += 1
        else:
            break
else:
    # 예상치 못한 결과 타입일 경우 그대로 출력
    print(result)