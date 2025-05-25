import pandas as pd

csv_path = "freida_programs_output_with_academic_year.csv"

df = pd.read_csv(csv_path)

if 'acgme_first_academic_year' not in df.columns:
    df.insert(0, 'acgme_first_academic_year', '')

# Save back to the same file (overwriting)
df.to_csv(csv_path, index=False)

print("Column added (if missing) and file saved.") 