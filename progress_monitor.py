import time
import os
import signal
import subprocess
import random

FAILED_CSV = "freida_programs_output_failed.csv"
SUCCESS_CSV = "freida_programs_output_success.csv"
TOTAL_CSV = "freida_programs_output_with_academic_year.csv"
CHECK_INTERVAL = 10  # seconds between checks
AVG_TIME_PER_RECORD = 20  # seconds per record (adjust as needed)
STALL_LIMIT = 20  # number of intervals to consider as a stall (was 10)
LOGFILE = "progress_monitor.log"

# Helper to find and kill the main scraping process
SCRAPER_CMD = "python3 acgme_scraper.py"
RUN_ALL_CMD = "./run_all.sh"


def log(msg):
    print(msg)
    with open(LOGFILE, "a") as f:
        f.write(msg + "\n")


def kill_scraper():
    try:
        out = subprocess.check_output(["pgrep", "-f", SCRAPER_CMD])
        pids = [int(pid) for pid in out.decode().split()]
        for pid in pids:
            os.kill(pid, signal.SIGTERM)
        log(f"[WARNING] Killed stalled process(es): {pids}")
        return True
    except Exception as e:
        log(f"[INFO] No running scraper process found to kill. ({e})")
        return False


def count_records(csv_path):
    if not os.path.exists(csv_path):
        return 0
    with open(csv_path, "r") as f:
        return sum(1 for _ in f) - 1  # subtract header


def main():
    log("Monitoring progress. Press Ctrl+C to stop.")
    total = count_records(TOTAL_CSV)
    last_failed = last_success = None
    stall_count = 0
    while True:
        failed = count_records(FAILED_CSV)
        success = count_records(SUCCESS_CSV)
        remaining = failed
        done = success
        if remaining < 0:
            remaining = 0
        if done < 0:
            done = 0

        if remaining == 0:
            log(f"✅ All records processed! ({done}/{total})")
            break

        est_seconds = remaining * AVG_TIME_PER_RECORD
        est_min = est_seconds // 60
        est_sec = est_seconds % 60
        log(f"[{time.strftime('%H:%M:%S')}] Remaining: {remaining} | Success: {done}/{total} | ETA: {int(est_min)}m {int(est_sec)}s")

        # Stall detection
        if (last_failed, last_success) == (failed, success):
            stall_count += 1
            if stall_count >= STALL_LIMIT:
                log(
                    f"[WARNING] No progress detected for {
                        STALL_LIMIT *
                        CHECK_INTERVAL} seconds. Possible block or stall.")
                killed = kill_scraper()
                stall_count = 0  # reset after killing
                if killed:
                    wait_minutes = random.randint(15, 20)
                    log(
                        f"[INFO] Waiting {wait_minutes} minutes before restarting run_all.sh...")
                    time.sleep(wait_minutes * 60)
                    log("[INFO] Restarting run_all.sh...")
                    subprocess.Popen([RUN_ALL_CMD])
        else:
            stall_count = 0
        last_failed, last_success = failed, success

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
