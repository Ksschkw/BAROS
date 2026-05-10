import ssl
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from .config import settings

# Convert postgresql:// to postgresql+asyncpg://
database_url = settings.DATABASE_URL
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif database_url.startswith("postgresql+asyncpg://"):
    pass
else:
    raise ValueError("Invalid DATABASE_URL scheme. Expected postgresql:// or postgresql+asyncpg://")

# Supabase requires SSL. asyncpg needs an explicit SSL context on some cloud environments.
ssl_context = ssl.create_default_context(cafile=None)
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

engine = create_async_engine(
    database_url,
    echo=False,
    future=True,
    connect_args={"ssl": ssl_context},
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))

        from sqlalchemy import inspect as schema_inspect

        def add_missing_columns(sync_conn):
            inspector = schema_inspect(sync_conn)
            for table_name, table_class in Base.metadata.tables.items():
                try:
                    existing_cols = [col["name"] for col in inspector.get_columns(table_name)]
                except Exception:
                    continue
                for col in table_class.columns:
                    if col.name not in existing_cols:
                        col_type = col.type.compile(sync_conn.dialect)
                        nullable = "" if col.nullable else " NOT NULL"
                        default = f" DEFAULT {col.default.arg}" if col.default and col.default.arg is not None else ""
                        sync_conn.execute(
                            text(
                                f'ALTER TABLE {table_name} ADD COLUMN "{col.name}" {col_type}{nullable}{default}'
                            )
                        )
                        print(f"Added column {col.name} to {table_name}")

        await conn.run_sync(add_missing_columns)