import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, BigInteger, String, JSON
# Твоя ссылка подключения (с добавленным +asyncpg)
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()
# Таблица, где будут храниться данные пар
class Couple(Base):
    __tablename__ = "couples"
    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(BigInteger, nullable=False)
    user2_id = Column(BigInteger, nullable=True)
    invite_code = Column(String, unique=True, index=True)
    data_json = Column(JSON, default={})
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
