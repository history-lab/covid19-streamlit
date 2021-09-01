"""Streamlit app for FOIA Explorer COVID-19 Emails"""
import streamlit as st
import pandas as pd
import psycopg2
from datetime import datetime, date
from st_aggrid import AgGrid


st.set_page_config(page_title="FOIA Explorer: COVID-19 Emails", layout="wide")
st.title("FOIA Explorer: COVID-19 Emails")


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
select subject, sent, from_email,
       to_emails, cc_emails, email_id, file_pg_start
    from covid19.emails
    order by sent nulls last
"""

# st.sidebar.title('COVID-19 Emails Explorer')
# st.sidebar.multiselect('FOIA', foias)
# st.sidebar.date_input('start date', datetime(2019, 11, 1))
# st.sidebar.date_input('end date', date.today())
st.selectbox('FOIA', ["Fauci Emails"])
"""
The COVID-19 releated emails of Dr. Anthony Fauci, director of the National
Institute of Allergy and Infectious Diseases.
- Source: MuckRock/DocumentCloud | Contributor: Jason Leopold
- https://www.documentcloud.org/documents/20793561-leopold-nih-foia-anthony-fauci-emails

### Individual Emails
"""
emdf = pd.read_sql_query(emqry, conn)
AgGrid(emdf)

"""
### About
The FOIA Explorer and associated tools were created by Columbia
Univesity's [History Lab](http://history-lab.org) under a grant from the Mellon
Foundation's [Email Archives: Building Capacity and Community]
(https://emailarchivesgrant.library.illinois.edu/blog/) program.
"""
