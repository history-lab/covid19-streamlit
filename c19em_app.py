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


@st.cache
def get_entity_list(qual):
    entsfw = 'SELECT entity from covid19.entities where entity_id <= 515 and \
    enttype '
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



"""
The COVID-19 releated emails of Dr. Anthony Fauci, director of the National
Institute of Allergy and Infectious Diseases.
- Source: MuckRock/DocumentCloud | Contributor: Jason Leopold
- https://www.documentcloud.org/documents/20793561-leopold-nih-foia-anthony-fauci-emails
"""

"""## Daily Email Volume, January - May 2020"""

emcnts = """
select date(sent) date, count(*) emails
    from covid19.emails
    where file_id = 1000 and sent >= '2020-01-01'
    group by date
    order by date;
"""

cntsdf = pd.read_sql_query(emcnts, conn)
c = alt.Chart(cntsdf).mark_bar().encode(
    x=alt.X('date:T', scale=alt.Scale(domain=('2020-01-23', '2020-05-06'))),
    y=alt.Y('emails:Q', scale=alt.Scale(domain=(0, 60)))
    )
st.altair_chart(c, use_container_width=True)

"""## Search Emails """
with st.form(key='query_params'):
    cols = st.columns(2)
    begin_date = cols[0].date_input('Start Date', datetime.date(2020, 1, 23))
    end_date = cols[1].date_input('End Date', datetime.date(2020, 5, 6))
    persons = st.multiselect('Person(s):', person_list)
    orgs = st.multiselect('Organization(s):', org_list)
    locations = st.multiselect('Location(s):', loc_list)
    ftq_text = st.text_input('Full Text Search:', '',
                             help='Perform full text search. Use double quotes \
                             for phrases, OR for logical or, and - for \
                             logical not.')
    query = st.form_submit_button(label='Execute Search')
    where_ent = where_ft = ''


""" ## Search Results """
entities = persons + orgs + locations
selfrom = """
select sent,
       coalesce(subject, '') subject,
       coalesce(topic, '') topic,
       coalesce(from_email, '') "from",
       coalesce(to_emails, '') "to",
       -- coalesce(cc_emails, '') cc,
       -- coalesce(substr(body, 1, 1024), '') body,
       e.email_id,
       file_pg_start pg_number
    from covid19.emails e left join covid19.top_topic_emails t
        on (e.email_id = t.email_id)"""
where = f"where sent between '{begin_date}' and '{end_date}' "
qry_explain = where
where += "and file_id = 1000 "
where_ent = ''
orderby = 'order by sent'
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
            where ent.entity_id <= 515 and ent.entity in """ + f'{entincl}) '
    qry_explain += f"and email references at least one of {entincl}"
if ftq_text:
    if ftq_text[0] == "'":         # replace single quote with double
        ftq_text = '"' + ftq_text[1:-1:] + '"'
    where_ft = f"and to_tsvector('english', body) @@ websearch_to_tsquery\
('english', '{ftq_text}')"
    qry_explain += f"and text body contains '{ftq_text}'"
st.write(qry_explain)
# execute query
emqry = selfrom + where + where_ent + where_ft + orderby
emdf = pd.read_sql_query(emqry, conn)
# emdf['sent'] = pd.to_datetime(emdf['sent'], utc=True)
# download results as CSV
csv = emdf.to_csv().encode('utf-8')
st.download_button(label="CSV download", data=csv,
                   file_name='foia-covid19.csv', mime='text/csv')
# generate AgGrid
gb = GridOptionsBuilder.from_dataframe(emdf)
gb.configure_default_column(value=True, editable=False)
gb.configure_selection(selection_mode='single', groupSelectsChildren=False)
# gb.configure_pagination(paginationAutoPageSize=True)
# gb.configure_auto_height(autoHeight=False)
# gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=50)

gb.configure_grid_options(domLayout='normal')
gridOptions = gb.build()

grid_response = AgGrid(emdf,
                       gridOptions=gridOptions,
                       return_mode_values='AS_INPUT',
                       update_mode='SELECTION_CHANGED',
                       allow_unsafe_jscode=False,
                       enable_enterprise_modules=False)
selected = grid_response['selected_rows']

# define DocumentCloud references
dc_base = 'https://www.documentcloud.org/documents/'
dc_id = '20793561'
dc_slug = 'leopold-nih-foia-anthony-fauci-emails'
dc_gif_sz = 'large'
dc_doc_url = dc_base + dc_id + '-' + dc_slug
dc_pg_gif = dc_base + dc_id + '/pages/' + dc_slug + '-p{pg}-' + dc_gif_sz + \
            '.gif'

if selected:
    """## Email Preview"""
    pg = int(selected[0]["pg_number"])
    st.write(f'View the full document on DocumentCloud: {dc_doc_url}')
    st.markdown('<iframe src=' + dc_pg_gif.format(pg=pg) +
                ' width="100%" height="1300">', unsafe_allow_html=True)
else:
    st.write('Select row to view email')

"""
## About
The FOIA Explorer and associated tools were created by Columbia
Univesity's [History Lab](http://history-lab.org) under a grant from the Mellon
Foundation's [Email Archives: Building Capacity and Community]
(https://emailarchivesgrant.library.illinois.edu/blog/) program.
"""
