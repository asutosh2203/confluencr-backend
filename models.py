from sqlalchemy import create_engine, Column, String, Integer, DateTime, Float
from sqlalchemy.orm import sessionmaker, declarative_base
import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Database Connection
DATABASE_URL = os.environ.get('DATABASE_URL')
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Transaction Model


class Transaction(Base):
    __tablename__ = "transactions"

    # Use transaction_id as the primary key
    transaction_id = Column(String, primary_key=True, index=True, unique=True)

    source_account = Column(String)
    destination_account = Column(String)
    amount = Column(Float)
    currency = Column(String)

    status = Column(String, default="PROCESSING")

    created_at = Column(DateTime, default=datetime.datetime.now)
    processed_at = Column(DateTime, nullable=True)

# Create the Table


def create_tables():
    Base.metadata.create_all(bind=engine)

# Helper to get a DB session (like getting a 'req' in Node)


def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
