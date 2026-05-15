import os
import pandas as pd
import qrcode

INPUT_FILE = 'processed_excels/MASTER_UNIVERSITY_INVENTORY.xlsx'
OUTPUT_FOLDER = 'qr_codes'

os.makedirs(OUTPUT_FOLDER, exist_ok=True)


df = pd.read_excel(INPUT_FILE)

for index, row in df.iterrows():

    asset_id = str(row['Asset ID'])
    qr_link = str(row['QR Tracking Link'])

    qr = qrcode.make(qr_link)

    qr.save(f'{OUTPUT_FOLDER}/{asset_id}.png')

    print(f'QR Generated: {asset_id}')