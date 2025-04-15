import streamlit as st
from time import sleep
from navigation import make_sidebar

st.set_page_config(layout="wide")
make_sidebar()

st.title("Welcome to Big Ape Analytics")

st.write("Please log in to continue ")

username = st.text_input("Username")
password = st.text_input("Password", type="password")

if st.button("Log in", type="primary"):
    if username == st.secrets["username"] and password == st.secrets["password"]:
        st.session_state.logged_in = True
        st.success("Logged in successfully!")
        sleep(0.5)
        st.switch_page("pages/Sales_Overview.py")
    else:
        st.error("Incorrect username or password")
