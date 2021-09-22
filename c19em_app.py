"""Streamlit app for FOIA Explorer COVID-19 Emails"""
import streamlit as st
import pandas as pd
import altair as alt
import psycopg2
import datetime
import base64
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode


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


@st.cache
def get_entity_list(qual):
    entsfw = 'SELECT entity from covid19.entities where enttype '
    entorder = 'order by entity'
    lov = []
    rows = run_query(entsfw + qual + entorder)
    for r in rows:
        lov.append(r[0])
    return(lov)


conn = init_connection()

# build dropdown lists for entity search
person_list = get_entity_list("= 'PERSON' ")
org_list = get_entity_list("= 'ORG' ")
loc_list = get_entity_list("in ('GPE', 'LOC', 'NORP', 'FAC') ")


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
begin_date = form.date_input('Start Date', datetime.date(2020, 1, 23))
end_date = form.date_input('End Date', datetime.date(2020, 5, 6))
persons = form.multiselect('Person(s):', person_list)
orgs = form.multiselect('Organization(s):', org_list)
locations = form.multiselect('Location(s):', loc_list)
query = form.form_submit_button(label='Execute Search')

# if query:
""" ## Search Results """
entities = persons + orgs + locations
selfrom = """
select sent, subject, topic, from_email "from", to_emails "to", cc_emails cc,
       body, e.email_id, file_pg_start pg_number
    from covid19.emails e left join covid19.top_topic_emails t
        on (e.email_id = t.email_id)"""
where = f"where sent between '{begin_date}' and '{end_date}' "
where_ent = ''
orderby = 'order by sent'
qry_explain = where
if entities:
    # build entity in list
    entincl = '('
    for e in entities:
        entincl += f"'{e}', "
    entincl = entincl[:-2] + ')'
    # form subquery
    where_ent = """
    and e.email_id in
        (select eem.email_id
            from covid19.entities ent join covid19.entity_emails eem
                on (ent.entity_id = eem.entity_id)
            where ent.entity in """ + f'{entincl}) '
    qry_explain += f"and email references at least one of {entincl}"
st.write(qry_explain)
# execute query
emqry = selfrom + where + where_ent + orderby
emdf = pd.read_sql_query(emqry, conn)
emdf['sent'] = pd.to_datetime(emdf['sent'], utc=True)
# download results as CSV
csv = emdf.to_csv().encode('utf-8')
st.download_button(label="CSV download", data=csv,
                   file_name='foia-covid19.csv', mime='text/csv')
# generate AgGrid
gb = GridOptionsBuilder.from_dataframe(emdf)
gb.configure_pagination()
gb.configure_selection('single')
gb.configure_default_column(groupable=True, value=True,
                            enableRowGroup=True, aggFunc="sum",
                            editable=True)
gridOptions = gb.build()

grid_response = AgGrid(emdf, gridOptions=gridOptions,
                       reload_data=True,
                       enable_enterprise_modules=True,
                       allow_unsafe_jscode=True,
                       update_mode=GridUpdateMode.SELECTION_CHANGED)
selected = grid_response['selected_rows']
st.write(selected)
"""## Document Preview"""
with open('./pdfs/fauci-cnn.pdf', "rb") as f:
    base64_pdf = base64.b64encode(f.read()).decode('utf-8')
pdf_display = f'<embed src="data:application/pdf;base64,{base64_pdf}" \
width="100%" height="1100" type="application/pdf">'
st.markdown(pdf_display, unsafe_allow_html=True)
"""
## About
The FOIA Explorer and associated tools were created by Columbia
Univesity's [History Lab](http://history-lab.org) under a grant from the Mellon
Foundation's [Email Archives: Building Capacity and Community]
(https://emailarchivesgrant.library.illinois.edu/blog/) program.
"""
