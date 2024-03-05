import streamlit as st
from utils.utility_functions import set_header, check_session_state

check_session_state(st)
set_header('About', st)

st.markdown("Das Staatsarchiv des Kantons Zürich nutzt Transkribus, um zentrale Bestände im Volltext aufzubereiten und der Öffentlichkeit zur Verfügung zu stellen. Diese API basiert auf dem TranskribusPyClient und bietet gewisse Zusatzfunktionen.")

st.markdown('''*:red[Diese App ist in Arbeit.]*''')

