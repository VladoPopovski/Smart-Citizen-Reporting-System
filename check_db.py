import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
db_url = os.getenv('DATABASE_URL')
# Use the synchronous driver if psycopg[binary] was installed
if db_url.startswith('postgresql+psycopg://'):
    db_url = db_url.replace('postgresql+psycopg://', 'postgresql://')

engine = create_engine(db_url)

target_tables = ['reports', 'categories', 'statuses', 'users']

query = text("""
    SELECT table_name, column_name, data_type, is_nullable
    FROM information_schema.columns
    WHERE table_name IN :tables AND table_schema = 'public'
    ORDER BY table_name, ordinal_position;
""")

with engine.connect() as conn:
    result = conn.execute(query, {'tables': tuple(target_tables)})
    for row in result:
        print(f"Table: {row.table_name} | Column: {row.column_name} | Type: {row.data_type} | Nullable: {row.is_nullable}")
