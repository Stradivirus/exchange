# daily_update/main.py
"""
일일 데이터 업데이트 통합 실행 스크립트

사용법:
  python main.py                      # 전체 실행
  python main.py --only exchange      # 환율만 실행
  python main.py --except mental      # 심리지수 제외하고 실행
  python main.py --categories exchange,stock  # 여러 개 선택
"""

import sys
import argparse
import subprocess
from datetime import datetime


# 실행 가능한 카테고리
CATEGORIES = {
    'exchange': 'exchange_cron.py',
    'stock': 'stock_cron.py',
    'commodities': 'commodities_cron.py',
    'interest': 'interest_cron.py',
    'mental': 'mental_cron.py',
    'economic': 'economic_cron.py'
}


def run_script(script_name, category_name):
    """개별 스크립트 실행"""
    print(f"\n{'='*60}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {category_name.upper()} 실행 중...")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            capture_output=True,
            text=True,
            timeout=600  # 10분 타임아웃
        )
        
        # 출력 표시
        if result.stdout:
            print(result.stdout)
        
        if result.returncode == 0:
            print(f"✅ {category_name.upper()} 완료")
            return True
        else:
            print(f"❌ {category_name.upper()} 실패")
            if result.stderr:
                print(f"에러: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏱️ {category_name.upper()} 타임아웃 (10분 초과)")
        return False
    except Exception as e:
        print(f"❌ {category_name.upper()} 오류: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='일일 데이터 업데이트')
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--only',
        type=str,
        help=f"특정 카테고리만 실행 ({', '.join(CATEGORIES.keys())})"
    )
    group.add_argument(
        '--except',
        type=str,
        dest='exclude',
        help=f"특정 카테고리 제외 ({', '.join(CATEGORIES.keys())})"
    )
    group.add_argument(
        '--categories',
        type=str,
        help="쉼표로 구분된 카테고리 목록 (예: exchange,stock)"
    )
    
    args = parser.parse_args()
    
    # 실행할 카테고리 결정
    if args.only:
        if args.only not in CATEGORIES:
            print(f"❌ 알 수 없는 카테고리: {args.only}")
            print(f"사용 가능: {', '.join(CATEGORIES.keys())}")
            return
        categories_to_run = [args.only]
    elif args.exclude:
        if args.exclude not in CATEGORIES:
            print(f"❌ 알 수 없는 카테고리: {args.exclude}")
            print(f"사용 가능: {', '.join(CATEGORIES.keys())}")
            return
        categories_to_run = [c for c in CATEGORIES.keys() if c != args.exclude]
    elif args.categories:
        requested = [c.strip() for c in args.categories.split(',')]
        invalid = [c for c in requested if c not in CATEGORIES]
        if invalid:
            print(f"❌ 알 수 없는 카테고리: {', '.join(invalid)}")
            print(f"사용 가능: {', '.join(CATEGORIES.keys())}")
            return
        categories_to_run = requested
    else:
        categories_to_run = list(CATEGORIES.keys())
    
    # 시작 시간
    start_time = datetime.now()
    print(f"\n{'='*60}")
    print(f"일일 데이터 업데이트 시작")
    print(f"시작 시간: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"실행 카테고리: {', '.join(categories_to_run)}")
    print(f"{'='*60}")
    
    # 실행
    results = {}
    for category in categories_to_run:
        script = CATEGORIES[category]
        success = run_script(script, category)
        results[category] = success
    
    # 완료 시간
    end_time = datetime.now()
    duration = end_time - start_time
    
    # 결과 요약
    print(f"\n{'='*60}")
    print("실행 결과 요약")
    print(f"{'='*60}")
    
    success_count = sum(1 for r in results.values() if r)
    total_count = len(results)
    
    for category, success in results.items():
        status = "✅ 성공" if success else "❌ 실패"
        print(f"{category.ljust(15)}: {status}")
    
    print(f"\n총 {success_count}/{total_count}개 성공")
    print(f"소요 시간: {duration.seconds}초")
    print(f"완료 시간: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    # 실패가 있으면 exit code 1
    if success_count < total_count:
        sys.exit(1)


if __name__ == "__main__":
    main()