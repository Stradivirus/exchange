#!/usr/bin/env python3
import subprocess
import sys
import os
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, wait

# 통합 설정 로드
try:
    import config
except ImportError:
    print("❌ 'config.py'가 없습니다.")
    sys.exit(1)

# 자식 프로세스용 환경변수 생성
COMMON_ENV = os.environ.copy()
COMMON_ENV.update({
    "MONGO_URI": config.MONGO_URI,
    "DB_NAME": config.DB_NAME,
    "N_JOBS_LIMIT": config.SYSTEM_CONFIG["N_JOBS_LIMIT"],
    "OMP_NUM_THREADS": config.SYSTEM_CONFIG["OMP_NUM_THREADS"],
    "PYTHONUTF8": "1"
})

GRAPH_ROOT = Path(__file__).parent

def run_script(script_info):
    path, script_name, description = script_info
    full_path = GRAPH_ROOT / path
    
    if path == "hong":
        COMMON_ENV["RESULTS_DIR"] = config.OUTPUT_PATHS["hong"]
    
    print(f"⏳ [시작] {description} ({script_name})...")
    start_time = time.time()
    
    try:
        result = subprocess.run(
            [sys.executable, script_name],
            cwd=full_path,
            env=COMMON_ENV, # 설정 주입
            capture_output=True,
            text=True
        )
        elapsed = time.time() - start_time
        
        output_msg = f"\n----- {description} Output -----\n{result.stdout}"
        if result.stderr:
            output_msg += f"\n[STDERR]\n{result.stderr}"
        output_msg += f"\n--------------------------------"
        print(output_msg)

        if result.returncode == 0:
            print(f"✅ [완료] {description} ({elapsed:.1f}초)")
            return True
        else:
            print(f"❌ [실패] {description} (Exit Code: {result.returncode})")
            return False

    except Exception as e:
        print(f"❌ [에러] {description}: {e}")
        return False

def main():
    print("🚀 금융 데이터 분석 시스템 가동 (Centralized Config)")
    start_global = time.time()

    # 폴더 생성
    for path in config.OUTPUT_PATHS.values():
        os.makedirs(path, exist_ok=True)

    gu_task = ("gu", "main.py", "GU: 딥러닝/시계열 통합 분석")
    
    light_tasks = [
        ("kim", "gold.py", "KIM: 금 시세 분석"),
        ("kim", "news.py", "KIM: 뉴스 데이터 분석"),
        ("hong", "hong_allcurrency.py", "HONG: 환율 전체 분석"),
        ("hong", "hong_expimp.py", "HONG: 수출입 지표 분석"),
        ("hong", "hong_interest.py", "HONG: 금리 지표 분석"),
        ("hong", "hong_predictions.py", "HONG: CatBoost 예측 모델")
    ]

    executor = ThreadPoolExecutor(max_workers=2)
    futures = []

    print("\n🔄 병렬 분석 시작...")
    for task in light_tasks:
        futures.append(executor.submit(run_script, task))

    print("\n🧠 GU 모듈 실행 진입...")
    gu_success = run_script(gu_task)

    print("\n⏳ Light Tasks 대기 중...")
    wait(futures)

    failed = 0
    if not gu_success: failed += 1
    for f in futures:
        if not f.result(): failed += 1

    elapsed = time.time() - start_global
    print(f"\n{'='*60}")
    if failed == 0:
        print(f"🎉 모든 작업 완료! ({elapsed:.1f}초)")
    else:
        print(f"⚠️ {failed}개 작업 실패.")
        sys.exit(1)

if __name__ == "__main__":
    main()