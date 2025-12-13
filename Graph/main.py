#!/usr/bin/env python3
# ==========================================================================
# Graph Main - GU 모듈 실행기 (Outputs 통합)
# ==========================================================================

import subprocess
import sys
import os
from pathlib import Path

def main():
    """
    hong, gu, kim 폴더의 main.py를 모두 실행하는 통합 메인
    """
    print("🚀 통합 금융 예측 분석 시작...")
    graph_root = Path(__file__).parent

    import threading

    # hong/main.py 병렬 실행 함수
    def run_hong():
        hong_path = graph_root / "hong"
        if not (hong_path / "main.py").exists():
            print("❌ hong/main.py 파일을 찾을 수 없습니다!")
            sys.exit(1)
        print("\n===== [1/3] hong/main.py 실행 =====")
        result_hong = subprocess.run([
            sys.executable, "main.py"
        ], cwd=hong_path)
        if result_hong.returncode == 0:
            print("✅ hong/main.py 분석 완료!")
        else:
            print(f"❌ hong/main.py 분석 실패 (코드: {result_hong.returncode})")
            sys.exit(1)

    # kim/gold.py, kim/news.py 병렬 실행 함수
    def run_kim():
        kim_path = graph_root / "kim"
        kim_files = [("gold.py", "금 예측"), ("news.py", "뉴스 분석")]
        for idx, (fname, desc) in enumerate(kim_files, start=1):
            kim_file = kim_path / fname
            if not kim_file.exists():
                print(f"❌ kim/{fname} 파일을 찾을 수 없습니다!")
                sys.exit(1)
            print(f"\n===== [3.{idx}/3] kim/{fname}({desc}) 실행 =====")
            result_kim = subprocess.run([
                sys.executable, fname
            ], cwd=kim_path)
            if result_kim.returncode == 0:
                print(f"✅ kim/{fname}({desc}) 분석 완료!")
            else:
                print(f"❌ kim/{fname}({desc}) 분석 실패 (코드: {result_kim.returncode})")
                sys.exit(1)

    def run_gu():
        gu_path = graph_root / "gu"
        unified_output = graph_root / "outputs" / "gu"
        unified_output.mkdir(parents=True, exist_ok=True)
        if not (gu_path / "main.py").exists():
            print("❌ gu/main.py 파일을 찾을 수 없습니다!")
            sys.exit(1)
        print("\n===== [2/3] gu/main.py 실행 =====")
        env = os.environ.copy()
        env["OUTPUT_FOLDER"] = str(unified_output)
        result_gu = subprocess.run([
            sys.executable, "main.py"
        ], cwd=gu_path, env=env)
        if result_gu.returncode == 0:
            print("✅ gu/main.py 분석 완료!")
            print(f"📁 gu 결과 저장 위치: {unified_output}")
        else:
            print(f"❌ gu/main.py 분석 실패 (코드: {result_gu.returncode})")
            sys.exit(1)


    # gu, kim 병렬 실행 & 둘 중 하나라도 끝나면 hong 실행
    hong_started = threading.Event()

    def run_and_trigger_hong(target_func):
        try:
            target_func()
        finally:
            if not hong_started.is_set():
                hong_started.set()
                run_hong()

    t_gu = threading.Thread(target=lambda: run_and_trigger_hong(run_gu))
    t_kim = threading.Thread(target=lambda: run_and_trigger_hong(run_kim))
    t_gu.start()
    t_kim.start()
    t_gu.join()
    t_kim.join()

    print("\n🎉 모든 분석 완료! gu + kim + hong 결과가 통합되었습니다.")

if __name__ == "__main__":
    main()