import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "mimiciv"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "serhat"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432")
}

def create_table_if_not_exists(cursor, table_name, df):
    """Dynamically create a table based on CSV structure if it does not exist."""
    column_types = []
    for col in df.columns:
        sample_value = df[col].dropna().iloc[0] if not df[col].dropna().empty else ""
        if isinstance(sample_value, int):
            column_types.append(f"{col} INT")
        elif isinstance(sample_value, float):
            column_types.append(f"{col} FLOAT")
        elif "time" in col.lower():  # Handle timestamp columns
            column_types.append(f"{col} TIMESTAMP")
        else:
            column_types.append(f"{col} TEXT")

    create_table_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({', '.join(column_types)});"
    cursor.execute(create_table_query)

def insert_csv_to_postgres(csv_path, table_name):
    """Insert a CSV file into a PostgreSQL table."""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    if not os.path.exists(csv_path):
        print(f"⚠️ File {csv_path} not found! Skipping...")
        return

    df = pd.read_csv(csv_path)

    # Ensure the table exists
    create_table_if_not_exists(cursor, table_name, df)

    for _, row in df.iterrows():
        columns = ', '.join(row.index)
        values = ', '.join(f"%s" if pd.notna(v) else 'NULL' for v in row.values)
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({values}) ON CONFLICT DO NOTHING;"
        cursor.execute(query, tuple(row.values))

    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Successfully imported {csv_path} into {table_name}")

# Example usage
csv_file_path = "D:/NeuroScience/mimicived/diagnosis.csv"  # Change this path
table_name = "diagnosis"

insert_csv_to_postgres(csv_file_path, table_name)
