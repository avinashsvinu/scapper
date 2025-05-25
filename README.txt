## Output Files

- `freida_programs_output_with_academic_year.csv`: Main output, all records with updated academic year field.
- `freida_programs_output_success.csv`: All records with a valid academic year (successes).
- `freida_programs_output_failed.csv`: All records still missing an academic year (failures).

## acgme_scraper.py Usage

### Command Line Flags

- `--failed-only` : Only process records with missing academic year in output CSV (`freida_programs_output_failed.csv`).
- `--failed-record <ids>` : Comma-separated list of program_ids to retry from failed output CSV (e.g., `--failed-record 1405621446,1400500932`). Overrides `--failed-only` if set.

### Examples

- Process all failed records:
  ```bash
  python3 acgme_scraper.py --failed-only
  ```
- Process specific failed records:
  ```bash
  python3 acgme_scraper.py --failed-record 1405621446,1400500932
  ```

## Architecture & Flow Chart

```mermaid
flowchart TD
    A[Start: main.py/acgme_scraper.py] --> B[Read program IDs from CSV]
    B --> C[Launch Playwright browser]
    C --> D[For each program ID (all, failed, or specific)]
    D --> E[Visit program detail page]
    E --> F[Try to click 'View Accreditation History' (human-like)]
    F --> G[If click fails, try all fallbacks]
    G --> H[If page loads, extract academic year from table]
    H --> I{Valid year found?}
    I -- Yes --> J[Write to main CSV]
    I -- No --> K[Take screenshot, run OCR]
    K --> L{OCR finds year?}
    L -- Yes --> J
    L -- No --> M[Log as failed]
    J --> N{More IDs?}
    N -- Yes --> D
    N -- No --> O[Write final CSVs: success & failed]
    O --> P[End]
``` 

## Nuances & Best Practices

- **Batch Size:** By default, the script processes 5 random records per run (can be changed in the code). This helps avoid overloading the site and makes debugging easier.
- **Skipping Already Collected Records:** The script always skips records that already have an academic year, ensuring no duplicate work or overwriting of good data.
- **Navigation Robustness:** If a click to 'View Accreditation History' fails but the browser has already navigated to the correct page, the script detects this and continues extraction. This handles edge cases where Playwright's click or wait times out but navigation succeeded.
- **Output File Management:**
  - `freida_programs_output_success.csv`: All records with a valid academic year (successes).
  - `freida_programs_output_failed.csv`: All records still missing an academic year (failures).
  - `freida_programs_output_with_academic_year.csv`: Main output, all records with updated academic year field.
  - After each run, these files are kept in sync: successful records are moved from failed to success, and vice versa if needed.
- **Processing Failed Records:**
  - Use `--failed-only` to process all failed records in batch.
  - Use `--failed-record <id>` to process a specific failed record.
  - To process all failed records one at a time, loop over the IDs and call the script with `--failed-record` for each.
- **Debugging:**
  - Debug screenshots and HTML are saved for failed or edge cases.
  - OCR fallback is used if DOM extraction fails.
- **Usage Tips:**
  - For large datasets, run the script multiple times to gradually fill in missing data.
  - You can safely interrupt and resume scraping; already-scraped records will be skipped.
  - All logs should be stored in the `logs/` directory (excluded from git). 

## Automation: Process All Records in Batches

To process all 600+ records efficiently, use the provided automation script:

### `run_all.sh`

- **What it does:**
  - Runs the scraper in batches of 5, skipping already completed records.
  - When only a few failures remain, it processes each failed record one at a time.
  - Continues until all records are completed and all failures are resolved.

### Usage

```bash
./run_all.sh
```

- You can safely interrupt and resume the script; it will always skip already-completed records.
- The script prints progress and will not stop until all records are processed.
- All output and debug files are managed as described above. 