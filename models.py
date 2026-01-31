import uuid
from sqlalchemy import Column, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


def uuid_column():
    return Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class User(Base):
    __tablename__ = "users"

    id = uuid_column()
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="admin")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    members = relationship("FamilyMember", back_populates="creator")
    uploaded_documents = relationship("Document", back_populates="uploader")


class FamilyMember(Base):
    __tablename__ = "family_members"

    id = uuid_column()
    full_name = Column(String, nullable=False)
    dob = Column(Date, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    creator = relationship("User", back_populates="members")
    documents = relationship("Document", back_populates="member", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = uuid_column()
    member_id = Column(UUID(as_uuid=True), ForeignKey("family_members.id"), nullable=False)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    doc_date = Column(Date, nullable=False)
    condition = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    storage_key = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    member = relationship("FamilyMember", back_populates="documents")
    uploader = relationship("User", back_populates="uploaded_documents")
