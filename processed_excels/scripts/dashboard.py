import streamlit as st
import pandas as pd

FILE = 'processed_excels/MASTER_UNIVERSITY_INVENTORY.xlsx'


df = pd.read_excel(FILE)

st.set_page_config(page_title='CSJMU Inventory Dashboard', layout='wide')

st.title('CSJMU Inventory Verification Dashboard')

col1, col2, col3, col4 = st.columns(4)

col1.metric('Total Assets', len(df))
col2.metric('Missing Assets', len(df[df['Verification Status'] == 'MISSING']))
col3.metric('Damaged Assets', len(df[df['Condition'] == 'DAMAGED']))
col4.metric('Pending Verification', len(df[df['Verification Status'] == 'PENDING']))

st.subheader('Department-wise Verification')

summary = df.groupby('Department Verification Committee').size().reset_index(name='Total Assets')

st.dataframe(summary)

st.subheader('Missing Assets')

missing = df[df['Verification Status'] == 'MISSING']

st.dataframe(missing)