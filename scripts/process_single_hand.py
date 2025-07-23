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
output_file = os.path.join(output_dir, f"{os.path.splitext(fname)[0]}_output.txt")
timestamp = datetime.now().isoformat()

status = "success"
error_msg = ""

try:
    with open(input_file, "r", encoding="utf-8") as fin:
        hand_text = fin.read()
    result = analyze_hand(hand_text)
    with open(output_file, "w", encoding="utf-8") as fout:
        fout.write(result)
    print("✅ Hand processed successfully.")
except Exception as e:
    result = ""
    status = "error"
    error_msg = traceback.format_exc()
    print("⚠️ Error processing hand:", e)

with open(log_file, "a", newline="", encoding="utf-8") as log_csv:
    writer = csv.writer(log_csv)
    writer.writerow([timestamp, "analyze_hand", fname, "model inference", status, error_msg])

print(f"📄 Log file: {log_file}")
print(f"   Output: {output_file}")
print(f"   Status: {status}")
print(f"   Error: {error_msg[:200] if error_msg else 'None'}")
