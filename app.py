
## 2) `app.py`

import os
import uuid
from datetime import date

from dotenv import load_dotenv

load_dotenv()

import streamlit as st
from sqlalchemy import select

from auth import hash_password, verify_password
from db import engine, get_db_session
from models import Base, Document, FamilyMember, User
from storage import get_storage_adapter

Base.metadata.create_all(bind=engine)


def get_current_user():
    return st.session_state.get("current_user")


def set_current_user(user: User | None):
    if user is None:
        st.session_state.pop("current_user", None)
        return
    st.session_state["current_user"] = {
        "id": str(user.id),
        "email": user.email,
        "role": user.role,
    }


def is_admin():
    user = get_current_user()
    return user and user["role"] == "admin"


def login_form():
    st.header("Sign in")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Sign in"):
        with get_db_session() as db:
            user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
            if not user or not verify_password(password, user.password_hash):
                st.error("Invalid credentials")
                return
            set_current_user(user)
            st.session_state["page"] = "family_members"
            st.session_state.pop("member_id", None)
            st.success("Signed in")
            st.rerun()

    st.divider()
    st.subheader("New here?")
    with st.expander("Register"):
        new_email = st.text_input("New email")
        new_password = st.text_input("New password", type="password")
        if st.button("Create account"):
            if not new_email or not new_password:
                st.error("Email and password are required")
                return
            with get_db_session() as db:
                existing = db.execute(select(User).where(User.email == new_email)).scalar_one_or_none()
                if existing:
                    st.error("Email already registered")
                    return
                user = User(email=new_email, password_hash=hash_password(new_password), role="admin")
                db.add(user)
                db.commit()
                st.success("Account created. Please sign in.")


def app_header():
    st.title("Family Medical Record App")

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Logout"):
            set_current_user(None)
            st.rerun()


def family_members_tab():
    with get_db_session() as db:
        members = db.execute(select(FamilyMember).order_by(FamilyMember.created_at.desc())).scalars().all()

    st.subheader("Family Members")
    for index, member in enumerate(members, start=1):
        dob_label = f"DOB: {member.dob or 'Not provided'}"
        card_label = f"{index}. {member.full_name}\n{dob_label}"
        if st.button(card_label, key=f"member_{member.id}", use_container_width=True):
            st.session_state["member_id"] = member.id
            st.session_state["navigate_to"] = "member_documents"
            st.rerun()


def add_member_tab():
    if not is_admin():
        st.info("Only admins can add family members.")
        return

    st.subheader("Add Family Member")
    with st.form("add_member"):
        name = st.text_input("Full name")
        dob = st.date_input("Date of birth", value=None)
        submitted = st.form_submit_button("Add member")
        if submitted:
            if not name:
                st.error("Full name is required")
            else:
                with get_db_session() as db:
                    creator = db.execute(select(User).where(User.email == get_current_user()["email"]))
                    creator_user = creator.scalar_one()
                    member = FamilyMember(full_name=name, dob=dob, created_by=creator_user.id)
                    db.add(member)
                    db.commit()
                st.success("Member added")
                st.rerun()


def member_detail():
    with get_db_session() as db:
        members = db.execute(select(FamilyMember).order_by(FamilyMember.created_at.desc())).scalars().all()

    if not members:
        st.info("No family members found. Add a member to get started.")
        return

    member_ids = [member.id for member in members]
    member_labels = {
        member.id: f"{member.full_name} (DOB: {member.dob or 'Not provided'})"
        for member in members
    }

    current_id = st.session_state.get("member_id")
    if isinstance(current_id, str):
        try:
            current_id = uuid.UUID(current_id)
        except ValueError:
            current_id = None

    if current_id not in member_ids:
        current_id = member_ids[0]

    selected_id = st.selectbox(
        "Select family member",
        member_ids,
        index=member_ids.index(current_id),
        format_func=lambda member_id: member_labels[member_id],
    )
    st.session_state["member_id"] = selected_id

    with get_db_session() as db:
        member = db.get(FamilyMember, selected_id)
        if not member:
            st.error("Member not found")
            st.session_state.pop("member_id", None)
            return
        documents = (
            db.execute(select(Document).where(Document.member_id == member.id).order_by(Document.created_at.desc()))
            .scalars()
            .all()
        )

    st.subheader(member.full_name)
    st.caption(f"DOB: {member.dob or 'Not provided'}")

    if is_admin():
        st.markdown("### Upload Documents")
        with st.form("upload_document"):
            doc_date = st.date_input("Document date", value=date.today())
            condition = st.text_input("Condition (treated for)")
            description = st.text_area("Description (optional)")
            file = st.file_uploader("Upload PDF or image", type=["pdf", "png", "jpg", "jpeg"])
            submitted = st.form_submit_button("Upload")

            if submitted:
                if not condition:
                    st.error("Condition is required")
                elif not file:
                    st.error("Please select a file")
                else:
                    adapter = get_storage_adapter()
                    storage_key = adapter.upload(file.getvalue(), file.name, file.type)
                    with get_db_session() as db:
                        uploader = db.execute(select(User).where(User.email == get_current_user()["email"]))
                        uploader_user = uploader.scalar_one()
                        document = Document(
                            member_id=member.id,
                            uploaded_by=uploader_user.id,
                            doc_date=doc_date,
                            condition=condition,
                            description=description,
                            storage_key=storage_key,
                            file_name=file.name,
                            mime_type=file.type,
                        )
                        db.add(document)
                        db.commit()
                    st.success("Document uploaded")
                    st.rerun()

    st.divider()
    st.markdown("### Existing Documents")
    if not documents:
        st.info("No documents uploaded yet.")
        return

    adapter = None
    for document in documents:
        if adapter is None:
            adapter = get_storage_adapter()
        signed_url = adapter.get_signed_url(document.storage_key, 3600)
        st.write(f"**{document.file_name}**")
        st.caption(
            f"{document.doc_date} • {document.condition} • Uploaded {document.created_at.date()}"
        )
        if document.description:
            st.write(document.description)
        if signed_url:
            st.markdown(f"[Download/View]({signed_url})")
        st.divider()


def main():
    st.set_page_config(page_title="Family Medical Record App", layout="wide")

    if not get_current_user():
        login_form()
        return

    app_header()

    if "page" not in st.session_state:
        st.session_state["page"] = "family_members"
    if st.session_state.get("navigate_to"):
        st.session_state["page"] = st.session_state.pop("navigate_to")

    pages = ["family_members", "add_member", "member_documents"]
    labels = {
        "family_members": "Family Members",
        "add_member": "Add Member",
        "member_documents": "Member Documents",
    }

    st.sidebar.title("Navigation")
    selection = st.sidebar.radio(
        "Go to",
        pages,
        format_func=lambda value: labels[value],
        key="page",
    )

    if selection == "family_members":
        family_members_tab()
    elif selection == "add_member":
        add_member_tab()
    else:
        member_detail()


if __name__ == "__main__":
    main()
