import os
import requests
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
from dotenv import load_dotenv

load_dotenv()

class NaverNewsSearchToolInput(BaseModel):
    query: str = Field(..., description="검색할 키워드 또는 문장")

class NaverNewsSearchTool(BaseTool):
    name: str = "Naver News Search Tool"
    description: str = "네이버 뉴스 API를 사용하여 특정 키워드에 대한 최신 뉴스 기사를 검색합니다."
    args_schema: Type[BaseModel] = NaverNewsSearchToolInput

    def _run(self, query: str) -> str:
        client_id = os.getenv("NAVER_CLIENT_ID")
        client_secret = os.getenv("NAVER_CLIENT_SECRET")

        if not client_id or not client_secret:
            return "오류: .env 파일에 NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET이 설정되지 않았습니다."

        url = "https://openapi.naver.com/v1/search/news.json"
        headers = {
            "X-Naver-Client-Id": client_id,
            "X-Naver-Client-Secret": client_secret,
        }

        params = {
            "query": query,
            "display": 5,
            "sort": "sim",
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            search_results = response.json()

            if not search_results.get('items'):
                return "검색된 뉴스 기사가 없습니다."

            # 결과를 LLM이 이해하기 쉬운 문자열로 가공
            result_str = ""
            for item in search_results['items']:
                title = item['title'].replace('<b>', '').replace('</b>', '')
                description = item['description'].replace('<b>', '').replace('</b>', '')
                result_str += f"- 제목: {title}\n"
                result_str += f"  - 요약: {description}\n"
                result_str += f"  - 링크: {item['link']}\n\n"

            return result_str

        except Exception as e:
            return f"네이버 뉴스 API 요청 중 오류가 발생했습니다: {e}"