#!/bin/bash

# Batch process in groups of 5, skipping already completed records
echo "[INFO] Starting batch processing in groups of 5..."
while true; do
  python3 acgme_scraper.py
  failed_count=$(awk 'END{print NR-1}' freida_programs_output_failed.csv)
  echo "[INFO] Remaining failed records: $failed_count"
  if [ "$failed_count" -eq 0 ]; then
    break
  fi
  if [ "$failed_count" -le 5 ]; then
    break
  fi
  sleep 2
  # Optional: add a longer sleep here if you want to throttle requests
  # sleep 10
  # You can also add a check for a max number of iterations if desired
  # ((batch++))
  # if [ "$batch" -gt 200 ]; then break; fi
  # Uncomment above if you want a hard stop
  # Otherwise, this will run until all are done

done

echo "[INFO] Batch processing complete. Handling remaining failures one at a time..."
awk -F, 'NR>1{print $2}' freida_programs_output_failed.csv > failed_ids.txt
while read id; do
  if [ -n "$id" ]; then
    python3 acgme_scraper.py --failed-record $id
    sleep 2
  fi
done < failed_ids.txt

echo "[INFO] All records processed!" 