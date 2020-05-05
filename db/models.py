# coding: utf-8
from sqlalchemy import BigInteger, Column, Date, DateTime, Float, ForeignKey, Index, Integer, Numeric, String, Table, Text, text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()
metadata = Base.metadata


class AccountHistory(Base):
    __tablename__ = 'account_histories'
    __table_args__ = (
        Index('index_account_histories_on_deleted_at_and_account_id_and_date', 'deleted_at', 'account_id', 'date', unique=True),
    )

    id = Column(Integer, primary_key=True)
    account_id = Column(ForeignKey('accounts.id', ondelete='RESTRICT', onupdate='RESTRICT'), nullable=False, index=True)
    date = Column(DateTime, nullable=False)
    math = Column(Float)
    russian = Column(Integer)
    biology = Column(Integer)
    physics = Column(Integer)
    liteerature = Column(Integer)

