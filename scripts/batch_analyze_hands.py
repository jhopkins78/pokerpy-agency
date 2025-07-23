import os
import csv
import traceback
from datetime import datetime

# Import analyze_hand from the Poker Transformer handler
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../Poker_Transformers-main")))
from model_handler import analyze_hand

INPUT_DIR = "Poker_Transformers-main/data/raw"
OUTPUT_DIR = "logs/model_outputs"
LOG_FILE = "logs/execution_log.csv"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs("logs", exist_ok=True)

def main():
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".txt")]
    total = len(files)
    success = 0
    failed = 0
    failures = []

    with open(LOG_FILE, "w", newline='', encoding="utf-8") as log_csv:
        writer = csv.writer(log_csv)
        writer.writerow(["timestamp", "agent", "input_file", "task", "status", "error_message"])

        for fname in files:
            input_path = os.path.join(INPUT_DIR, fname)
            output_path = os.path.join(OUTPUT_DIR, f"{os.path.splitext(fname)[0]}_output.txt")
            timestamp = datetime.now().isoformat()
            try:
                with open(input_path, "r", encoding="utf-8") as fin:
                    hand_text = fin.read()
                result = analyze_hand(hand_text)
                with open(output_path, "w", encoding="utf-8") as fout:
                    fout.write(result)
                writer.writerow([timestamp, "analyze_hand", fname, "model inference", "success", ""])
                success += 1
            except Exception as e:
                error_msg = traceback.format_exc()
                writer.writerow([timestamp, "analyze_hand", fname, "model inference", "error", error_msg])
                failed += 1
                failures.append((fname, str(e)))

    # Print summary
    print(f"✅ Hands processed: {total}")
    print(f"   Succeeded: {success}")
    print(f"   Failed: {failed}")
    print(f"📄 Log file: {LOG_FILE}")
    if failed:
        print("⚠️ Failures:")
        for fname, err in failures:
            print(f"  - {fname}: {err}")

if __name__ == "__main__":
    main()
