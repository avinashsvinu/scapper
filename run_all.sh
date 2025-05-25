#!/bin/bash

# Get the total number of records (excluding header) from the input CSV
TOTAL_RECORDS=$(awk 'END{print NR-1}' freida_programs_output.csv)

# Batch process in groups of 5, skipping already completed records
echo "[INFO] Starting batch processing in groups of 5..."
while true; do
  python3 acgme_scraper.py
  failed_count=$(awk 'END{print NR-1}' freida_programs_output_failed.csv)
  success_count=$(awk 'END{print NR-1}' freida_programs_output_success.csv)
  echo "[INFO] Remaining failed records: $failed_count | Success count: $success_count / $TOTAL_RECORDS"
  if [ "$failed_count" -eq 0 ] && [ "$success_count" -ge "$TOTAL_RECORDS" ]; then
    break
  fi
  sleep 2
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