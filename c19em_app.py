"""Streamlit app for FOIA Explorer COVID-19 Emails"""
import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime, date


# initialize database connection - uses st.cache to only run once
@st.cache(allow_output_mutation=True,
          hash_funcs={"_thread.RLock": lambda _: None})
def init_connection():
    return psycopg2.connect(**st.secrets["postgres"])


# perform query - ses st.cache to only rerun once
@st.cache
def run_query(query):
    with conn.cursor() as cur:
        cur.execute(query)
        return cur.fetchall()


conn = init_connection()
foias = run_query("SELECT file_id, title from covid19.files order by title")
emqry = """
select email_id, file_pg_start, subject, sent, from_email,
       to_emails, cc_emails
    from covid19.emails
"""
emdf = pd.read_sql_query(emqry, conn)

st.sidebar.title('COVID-19 Emails Explorer')
st.sidebar.multiselect('FOIA', foias)
st.sidebar.date_input('start date', datetime(2019, 11, 1))
st.sidebar.date_input('end date', date.today())

emdf = pd.read_sql_query(emqry, conn)
st.table(emdf)
