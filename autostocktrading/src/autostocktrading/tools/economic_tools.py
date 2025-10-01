from crewai.tools import BaseTool
import requests
import os
from dotenv import load_dotenv

load_dotenv()

class EconomicIndicatorTool(BaseTool):
    name: str = "South Korea Economic Indicator Tool"
    description: str = "한국은행(BOK) API를 사용하여 대한민국의 주요 거시 경제 지표(기준금리, 소비자 물가 지수)를 조회합니다."

    def _run(self) -> str:
        api_key = os.getenv("BOK_API_KEY")
        if not api_key:
            return "[에러]: .env 파일에 BOK_API_KEY가 설정되어 있지 않습니다"

        indicators = []

        try:
            # 기준금리 조회
            url_base_rate = f"https://ecos.bok.or.kr/api/StatisticSearch/{api_key}/json/kr/1/10/028Y001/MM/202301/202512/0101000"
            response_rate = requests.get(url_base_rate)
            rate_data = response_rate.json()
            latest_rate = rate_data['StatisticSearch']['row'][-1]
            indicators.append(f"  - 최신 기준금리: {latest_rate['DATA_VALUE']}% (기준일: {latest_rate['TIME']}")

            # 소비자 물가 지수(CPI) 조회 (전년 동월 대비 증감율)
            url_cpi = f"https://ecos.bok.or.kr/api/StatisticSearch/{api_key}/json/kr/1/10/901Y009/MM/202301/202512/0"
            response_cpi = requests.get(url_cpi)
            cpi_data = response_cpi.json()
            latest_cpi = cpi_data['StatisticSearch']['row'][-1]
            indicators.append(f"  - 최신 소비자물가지수(전년 동월 대비): {latest_cpi['DATA_VALUE']}% (기준일: {latest_cpi['TIME']})")

            return "대한민국 주요 경제 지표 현황:\n" + "\n".join(indicators)

        except Exception as e:
            return f"경제 지표 조회 중 오류가 발생했습니다.: {e}"