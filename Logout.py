import streamlit as st
from streamlit_option_menu import option_menu
from streamlit.components.v1 import html
from streamlit_extras.app_logo import add_logo
from pathlib import Path
import requests
import xml.etree.ElementTree as et



def app():
    """
    This function sets up the StAZH TranskribusAPI web application.
    It handles the login process and displays the login form.
    """
    st.set_page_config(
        page_title="StAZH Transkribus API",
        initial_sidebar_state="expanded",
    )

    is_authenticated = st.session_state.get("authenticated", False)

    if not is_authenticated:
        sidebar_visibility_style = """
            <style>
                [data-testid="collapsedControl"] {
                    display: block !important;
                }
            </style>
        """
        st.markdown(sidebar_visibility_style, unsafe_allow_html=True)

    #add_logo("data/loewe.png", height=150)

    st.subheader("StAZH TranskribusAPI")

    st.markdown("Bitte Logindaten eingeben:")

    with st.form(key="login_form"):
        email = st.text_input('Transkribus Email')
        password = st.text_input('Transkribus Passwort', type="password")
        submit_button = st.form_submit_button(label='Login')

    if submit_button:
        if email and password:
            r = requests.post("https://transkribus.eu/TrpServer/rest/auth/login",
                                    data ={"user":email, "pw":password})
            if r.status_code == requests.codes.ok:
                session = r.text
                session = et.fromstring(session)
                createStreamlitSession(session, email, password)

                #check if login was successfull
                if st.session_state.sessionId == None:
                    st.warning("Fehler! Login war nicht erfolgreich! \n Bitte erneut versuchen.", icon="⚠️")
                else:
                    st.warning("Login erfolgreich...", icon="✅")
                    st.switch_page("pages/0_About.py")
            else:
                st.warning('Login war nicht erfolgreich', icon="⚠️")

        else:
            st.warning('Bitte Logindaten eingeben.', icon="⚠️")

def authentification(request):
    session = {
        "userId": et.fromstring(request.text).find("userId").text,
        "sessionId": et.fromstring(request.text).find("sessionId").text,
    }
    return session

def createStreamlitSession(auth_session, email, password):
    """
    Creates a Streamlit session with the provided authentication session, email, and password.

    Parameters:
    - auth_session: The authentication session.
    - email: The email associated with the session.
    - password: The password associated with the session.
    """
    if 'sessionId' not in st.session_state:
        st.session_state.sessionId = auth_session.find("sessionId").text

    if 'username' not in st.session_state:
        st.session_state.username = auth_session.find("userId").text

    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = True

    if 'proxy' not in st.session_state:
        st.session_state.proxy = {"https" : 'http://:@:',
                         "http" : 'http://:@:'}

    st.session_state.email = email
    st.session_state.password = password

if __name__ == "__main__":
    app()
