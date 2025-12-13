import os
import subprocess

# 공통 MongoDB URI 및 DB 이름
MONGO_URI = "mongodb+srv://stradivirus:1q2w3e4r6218@cluster0.e7rvfpz.mongodb.net/exchange_all?retryWrites=true&w=majority&appName=Cluster0"
DB_NAME = "exchange_all"


# 환경 변수로 전달 (각 스크립트에서 os.environ으로 접근 가능)
os.environ["MONGO_URI"] = MONGO_URI
os.environ["DB_NAME"] = DB_NAME
os.environ["RESULTS_DIR"] = os.path.abspath(os.path.join(os.path.dirname(__file__), '../outputs/hong'))

# 실행할 스크립트 리스트 (순차 실행)
script_paths = [
    "hong_allcurrency.py",
    "hong_expimp.py",
    "hong_interest.py",
    "hong_predictions.py"
]

for script in script_paths:
    print(f"\n===== {script} 실행 시작 =====")
    result = subprocess.run(["python3", script], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(f"[stderr] {result.stderr}")
    print(f"===== {script} 실행 완료 =====\n")

print("모든 스크립트 실행이 완료되었습니다. 결과 HTML 파일은 각 results 폴더에 저장됩니다.")
