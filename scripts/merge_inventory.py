import os
import pandas as pd

INPUT_FOLDER = 'input_excels'
OUTPUT_FILE = 'processed_excels/MASTER_UNIVERSITY_INVENTORY.xlsx'

all_data = []

for file in os.listdir(INPUT_FOLDER):
    if file.endswith('.xlsx'):
        path = os.path.join(INPUT_FOLDER, file)

        try:
            df = pd.read_excel(path)
            df['Department File'] = file
            all_data.append(df)
            print(f'Read: {file}')

        except Exception as e:
            print(f'Error reading {file}: {e}')

master_df = pd.concat(all_data, ignore_index=True)

master_df.to_excel(OUTPUT_FILE, index=False)

print('Master Inventory File Generated Successfully')