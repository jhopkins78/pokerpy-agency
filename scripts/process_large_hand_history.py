import os
import csv
import traceback
from datetime import datetime
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../Poker_Transformers-main")))
from model_handler import analyze_hand

input_file = "Poker_Transformers-main/data/raw/poker_dataset/Export Holdem Manager 2.0 12302016144830.txt"
output_dir = "logs/model_outputs"
log_file = "logs/execution_log.csv"

os.makedirs(output_dir, exist_ok=True)
os.makedirs("logs", exist_ok=True)

fname = os.path.basename(input_file)
base_output_name = os.path.splitext(fname)[0]

def split_hands(filepath):
    hands = []
    current_hand = []
    with open(filepath, "r", encoding="utf-8") as fin:
        for line in fin:
            if line.startswith("Game started at:"):
                if current_hand:
                    hands.append("".join(current_hand))
                    current_hand = []
            current_hand.append(line)
        if current_hand:
            hands.append("".join(current_hand))
    return hands

def main():
    hands = split_hands(input_file)
    total = len(hands)
    success = 0
    failed = 0
    failures = []

    with open(log_file, "a", newline="", encoding="utf-8") as log_csv:
        writer = csv.writer(log_csv)
        for idx, hand_text in enumerate(hands, 1):
            output_file = os.path.join(output_dir, f"{base_output_name}_hand{idx}_output.txt")
            timestamp = datetime.now().isoformat()
            status = "success"
            error_msg = ""
            try:
                result = analyze_hand(hand_text)
                with open(output_file, "w", encoding="utf-8") as fout:
                    fout.write(result)
                success += 1
            except Exception as e:
                result = ""
                status = "error"
                error_msg = traceback.format_exc()
                failed += 1
                failures.append((idx, str(e)))
            writer.writerow([timestamp, "analyze_hand", f"{fname} (hand {idx})", "model inference", status, error_msg])

    print(f"✅ Hands processed: {total}")
    print(f"   Succeeded: {success}")
    print(f"   Failed: {failed}")
    print(f"📄 Log file: {log_file}")
    print(f"   Output dir: {output_dir}")
    if failed:
        print("⚠️ Failures:")
        for idx, err in failures:
            print(f"  - Hand {idx}: {err[:200]}")

if __name__ == "__main__":
    main()
