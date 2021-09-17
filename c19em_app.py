"""Streamlit app for FOIA Explorer COVID-19 Emails"""
import streamlit as st
import pandas as pd
import altair as alt
import psycopg2
import datetime
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder


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
# foias = run_query("SELECT file_id, title from covid19.files order by title")


st.selectbox('FOIA', ["Fauci Emails"])
"""
The COVID-19 releated emails of Dr. Anthony Fauci, director of the National
Institute of Allergy and Infectious Diseases.
- Source: MuckRock/DocumentCloud | Contributor: Jason Leopold
- https://www.documentcloud.org/documents/20793561-leopold-nih-foia-anthony-fauci-emails
"""

"""## Daily Email Volume, January - May 2020"""

emcnts = """
select to_char(date_trunc('day',sent), 'MM/DD') date, count(*) emails
    from covid19.emails
    where sent >= '2020-01-01'
    group by date
    order by date;
"""

cntsdf = pd.read_sql_query(emcnts, conn)
c = alt.Chart(cntsdf).mark_bar().encode(
    x='date',
    y='emails'
)
st.altair_chart(c, use_container_width=True)

""" ## Search Emails """
query = False
form = st.form('query_params')
# persons = form.multiselect('Person(s):', ['Fauci', 'Collins'])
# orgs = form.multiselect('Organization(s):', ['NIH', 'White House'])
# locations = form.multiselect('Location(s):', ['Brooklyn'])
begin_date = form.date_input('Start Date', datetime.date(2020, 1, 23))
end_date = form.date_input('End Date', datetime.date(2020, 5, 6))
query = form.form_submit_button(label='Execute Search')

if query:
    """ ## Search Results """
    # entities = persons + orgs + locations
    # st.write(entities)
    selfrom = """
    select sent, subject, topic, from_email "from", to_emails "to",
           cc_emails cc, body, e.email_id, file_pg_start pg_number
        from covid19.emails e left join covid19.top_topic_emails t
            on (e.email_id = t.email_id)"""
    where = f"where sent between '{begin_date}' and '{end_date}' "
    orderby = 'order by sent'
    st.write(where)
    emqry = selfrom + where + orderby
    emdf = pd.read_sql_query(emqry, conn)
    emdf['sent'] = pd.to_datetime(emdf['sent'], utc=True)
    #
    gb = GridOptionsBuilder.from_dataframe(emdf)
    gb.configure_pagination()
    gb.configure_default_column(groupable=True, value=True,
                                enableRowGroup=True, aggFunc="sum",
                                editable=True)
    gridOptions = gb.build()

    AgGrid(emdf, gridOptions=gridOptions, enable_enterprise_modules=True)

"""
## About
The FOIA Explorer and associated tools were created by Columbia
Univesity's [History Lab](http://history-lab.org) under a grant from the Mellon
Foundation's [Email Archives: Building Capacity and Community]
(https://emailarchivesgrant.library.illinois.edu/blog/) program.
"""
