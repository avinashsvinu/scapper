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