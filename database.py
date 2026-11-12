from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, JSON

# Твоя ссылка подключения (с добавленным +asyncpg)
DATABASE_URL = "postgresql+asyncpg://kaiki_c_6f31aa45b9def0ef010b6f20:Kk1!1DpGqiRLIY7rKvdvPAqv2VFUYUU1@ep-aeeaa01eba61.kaiki.ru:5432/love-app-db?sslmode=require"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# Таблица, где будут храниться данные пар
class Couple(Base):
    __tablename__ = "couples"
    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(Integer, nullable=False) # Telegram ID первого
    user2_id = Column(Integer, nullable=True)  # Telegram ID второго
    invite_code = Column(String, unique=True, index=True) # Код приглашения
    data_json = Column(JSON, default={}) # Сами планы, заметки и т.д.

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
