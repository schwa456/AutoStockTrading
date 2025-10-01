#!/usr/bin/env python
import sys
import time
import warnings

from apscheduler.schedulers.blocking import BlockingScheduler

from autostocktrading.crew import Autostocktrading

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

def run_trading_cycle():
    """
    1회 투자 분석 및 실행 사이클을 수행합니다.
    """
    print("=" * 80)
    print(f"[{time.strftime('%Y-%m%d %H:%M:%S')}] 새로운 투자 사이클을 시작합니다...")

    inputs = {
        'market': 'KOSPI'
    }

    try:
        Autostocktrading().crew().kickoff(inputs=inputs)
        print("투자 사이클을 성공적으로 완료했습니다.")
    except Exception as e:
        print(f"투자 사이클 실행 중 오류가 발생했습니다: {e}")
    print("=" * 80)

if __name__ == '__main__':
    # 1회만 실행
    run_trading_cycle()

    # 스케줄러로 매일 실행
    scheduler = BlockingScheduler()
    # 매일 오전 9시 5분에 run_trading_cycle 함수를 실행하도록 스케줄링
    scheduler.add_job(run_trading_cycle(), 'cron', hour=9, minute=5)

    print("자동 투자 시스템이 시작되었습니다. 매일 오전 9시 5분에 자동으로 실행됩니다.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass