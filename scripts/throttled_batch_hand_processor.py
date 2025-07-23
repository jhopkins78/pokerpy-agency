import os
import csv
import time
import traceback
from datetime import datetime
import sys
import psutil

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../Poker_Transformers-main")))
from model_handler import analyze_hand

INPUT_DIR = "Poker_Transformers-main/data/raw/poker_dataset"
OUTPUT_DIR = "logs/model_outputs"
HEALTH_LOG = "logs/system_health_log.csv"
HARMONY_LOG = "logs/harmony_input_log.csv"
ERROR_LOG = "logs/errors.csv"
BATCH_SIZE = 5
CPU_THRESHOLD = 90.0
MEM_THRESHOLD = 80.0

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs("logs", exist_ok=True)

def detect_format(text):
    # Heuristics for poker hand history format
    if "PokerStars Hand #" in text or "PokerStars" in text:
        return "PokerStars"
    if "Ignition Hand #" in text or "Bovada Hand #" in text or "ACR" in text:
        return "ACR"
    if "Holdem Manager" in text or "Game started at:" in text:
        return "Holdem Manager"
    return "Unknown"

def get_stats():
    mem = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=1)
    return cpu, mem.used / (1024 * 1024)  # MB

def log_csv(path, row, header=None):
    exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not exists and header:
            writer.writerow(header)
        writer.writerow(row)

def main():
    files = [f for f in os.listdir(INPUT_DIR) if f.endswith(".txt")]
    files = sorted(files)[:BATCH_SIZE]
    total = len(files)
    success = 0
    failed = 0
    skipped = 0
    needs_norm = []

    # Prepare logs
    log_csv(HEALTH_LOG, [], header=["timestamp", "filename", "cpu_percent", "mem_used_mb"])
    log_csv(HARMONY_LOG, [], header=["filename", "format_detected", "lines", "chars", "status"])
    log_csv(ERROR_LOG, [], header=["timestamp", "filename", "error"])

    for fname in files:
        input_path = os.path.join(INPUT_DIR, fname)
        output_path = os.path.join(OUTPUT_DIR, f"{os.path.splitext(fname)[0]}_output.txt")
        timestamp = datetime.now().isoformat()

        # System health before
        cpu_before, mem_before = get_stats()
        log_csv(HEALTH_LOG, [timestamp, fname, cpu_before, mem_before])

        # Safety check
        if cpu_before > CPU_THRESHOLD or mem_before > (psutil.virtual_memory().total / (1024 * 1024)) * (MEM_THRESHOLD / 100):
            print(f"🛑 System resources exceeded before processing {fname}. Aborting batch.")
            break

        try:
            with open(input_path, "r", encoding="utf-8") as fin:
                text = fin.read()
            lines = text.count("\n") + 1
            chars = len(text)
            fmt = detect_format(text)
            status = "ready" if fmt != "Unknown" else "needs normalization"
            if status == "needs normalization":
                needs_norm.append(fname)

            # Log harmony prep
            log_csv(HARMONY_LOG, [fname, fmt, lines, chars, status])

            # Inference (split if too large)
            if chars > 8000 or lines > 500:  # Heuristic: split into hands if too large
                # Split on "Game started at:" or blank lines
                hands = []
                current_hand = []
                for line in text.splitlines(keepends=True):
                    if "Game started at:" in line and current_hand:
                        hands.append("".join(current_hand))
                        current_hand = []
                    current_hand.append(line)
                if current_hand:
                    hands.append("".join(current_hand))
                outputs = []
                for idx, hand in enumerate(hands, 1):
                    try:
                        out = analyze_hand(hand)
                        outputs.append(f"--- Hand {idx} ---\n{out}\n")
                        success += 1
                    except Exception as e:
                        failed += 1
                        log_csv(ERROR_LOG, [datetime.now().isoformat(), f"{fname} (hand {idx})", traceback.format_exc()])
                with open(output_path, "w", encoding="utf-8") as fout:
                    fout.writelines(outputs)
            else:
                out = analyze_hand(text)
                with open(output_path, "w", encoding="utf-8") as fout:
                    fout.write(out)
                success += 1

        except Exception as e:
            failed += 1
            log_csv(ERROR_LOG, [datetime.now().isoformat(), fname, traceback.format_exc()])
            print(f"⚠️ Error processing {fname}: {e}")
            continue

        # System health after
        cpu_after, mem_after = get_stats()
        log_csv(HEALTH_LOG, [datetime.now().isoformat(), fname, cpu_after, mem_after])

        # Safety check after
        if cpu_after > CPU_THRESHOLD or mem_after > (psutil.virtual_memory().total / (1024 * 1024)) * (MEM_THRESHOLD / 100):
            print(f"🛑 System resources exceeded after processing {fname}. Aborting batch.")
            break

    print(f"\n=== Batch Summary ===")
    print(f"Total files attempted: {total}")
    print(f"Successful inferences: {success}")
    print(f"Skipped or failed files: {failed}")
    print(f"Files flagged as 'needs normalization': {needs_norm}")
    print(f"System health log: {HEALTH_LOG}")
    print(f"Harmony input log: {HARMONY_LOG}")
    print(f"Error log: {ERROR_LOG}")

    print("Sleeping for 10 seconds before next batch...")
    time.sleep(10)

if __name__ == "__main__":
    main()
