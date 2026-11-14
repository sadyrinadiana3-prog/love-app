import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, BigInteger, String, JSON, text

# Берем ссылку из настроек Render
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "postgresql+asyncpg://kaiki_c_6f31aa45b9def0ef010b6f20:Kk1!1DpGqiRLIY7rKvdvPAqv2VFUYUU1@ep-aeeaa01eba61.kaiki.ru:5432/love-app-db?ssl=require"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class Couple(Base):
    __tablename__ = "couples"
    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(BigInteger, nullable=False)  # Исправлено на BigInteger
    user2_id = Column(BigInteger, nullable=True)   # Исправлено на BigInteger
    invite_code = Column(String, unique=True, index=True)
    data_json = Column(JSON, default={})

async def init_db():
    async with engine.begin() as conn:
        # УДАЛЯЕМ старую таблицу (если она есть)
        await conn.execute(text('DROP TABLE IF EXISTS couples;'))
        # СОЗДАЕМ новую таблицу с правильными типами
        await conn.run_sync(Base.metadata.create_all)
