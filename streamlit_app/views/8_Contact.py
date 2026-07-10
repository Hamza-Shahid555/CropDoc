import streamlit as st

from streamlit_app.core import db, ui
from streamlit_app.core.auth import current_user

ui.page_header("Contact", "Questions, feedback, or a bug to report?", "✉️")

user = current_user()

ui.card_open()
with st.form("contact_form", clear_on_submit=True):
    name = st.text_input("Name", value=user["username"] if user else "")
    email = st.text_input("Email")
    message = st.text_area("Message", height=140)
    submitted = st.form_submit_button("Send message", width="stretch")

if submitted:
    if not name.strip() or not email.strip() or not message.strip():
        st.error("Please fill in all fields.")
    else:
        db.add_contact_message(name.strip(), email.strip(), message.strip())
        st.success("Thanks — your message has been recorded.")
ui.card_close()
