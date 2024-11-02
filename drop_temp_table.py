import os
from sqlalchemy import create_engine, text

# Get the current script's directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to the database file
db_path = os.path.join(current_dir, 'app.db')

# Create the SQLAlchemy engine with the correct URI
DATABASE_URI = f"sqlite:///{db_path}"
engine = create_engine(DATABASE_URI)

with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS _alembic_tmp_session"))
    conn.commit()

print("Temporary table dropped successfully.")