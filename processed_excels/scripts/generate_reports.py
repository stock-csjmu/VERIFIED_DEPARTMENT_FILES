import pandas as pd

INPUT_FILE = 'processed_excels/MASTER_UNIVERSITY_INVENTORY.xlsx'


df = pd.read_excel(INPUT_FILE)

missing = df[df['Verification Status'] == 'MISSING']
damaged = df[df['Condition'] == 'DAMAGED']
pending = df[df['Verification Status'] == 'PENDING']

missing.to_excel('reports/MISSING_ASSETS.xlsx', index=False)
damaged.to_excel('reports/DAMAGED_ASSETS.xlsx', index=False)
pending.to_excel('reports/PENDING_VERIFICATION.xlsx', index=False)

print('Reports Generated Successfully')