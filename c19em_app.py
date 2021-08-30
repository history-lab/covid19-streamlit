"""Streamlit app for FOIA Explorer COVID-19 Emails"""
import streamlit as st
# import pyscopg2
from datetime import datetime, date

st.sidebar.title('COVID-19 Emails Explorer')
st.sidebar.multiselect('FOIA', ['ABCAAAAAAAAAAAAAAAAAAAAAAAAAAA', 'DEF', 'GHI'])
st.sidebar.date_input('start date', datetime(2019, 11, 1))
st.sidebar.date_input('end date', date.today())
