import psycopg2
import pandas as pd
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "mimiciv"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "password"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432")
}

# Base folder where CSV files are stored
base_path = "D:\\NeuroScience\\mimicived"  # Update this if your path is different

def create_table_if_not_exists(cursor, table_name, df):
    """Create table dynamically based on CSV file structure if it does not exist."""
    column_types = []
    for col in df.columns:
        sample_value = df[col].dropna().iloc[0] if not df[col].dropna().empty else ""
        if isinstance(sample_value, int):
            column_types.append(f"{col} BIGINT")
        elif isinstance(sample_value, float):
            column_types.append(f"{col} FLOAT")
        elif "time" in col.lower():  # Handle timestamp columns
            column_types.append(f"{col} TIMESTAMP")
        else:
            column_types.append(f"{col} TEXT")

    create_table_query = f"CREATE TABLE IF NOT EXISTS mimiciv_ed.{table_name} ({', '.join(column_types)});"
    cursor.execute(create_table_query)

def import_csv_to_postgres(csv_path, table_name):
    """Import a CSV file into PostgreSQL."""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    if not os.path.exists(csv_path):
        print(f"⚠️ File {csv_path} not found! Skipping...")
        return

    df = pd.read_csv(csv_path)

    # Ensure the table exists before inserting data
    create_table_if_not_exists(cursor, table_name, df)

    for _, row in df.iterrows():
        columns = ', '.join(row.index)
        values_placeholders = ', '.join(['%s'] * len(row.values))  # Ensure all values are properly placed
        escaped_values = [str(v).replace("'", "''") if isinstance(v, str) else v for v in row.values]
        query = f"INSERT INTO mimiciv_ed.{table_name} ({columns}) VALUES ({values_placeholders}) ON CONFLICT DO NOTHING;"
        cursor.execute(query, tuple(row.values))




    conn.commit()
    cursor.close()
    conn.close()
    print(f"✅ Imported {csv_path} into {table_name}")

# Define folders and tables
data_folders = {"ed": ["diagnosis", "edstays", "medrecon","pyxis","triage","vitalsign"]}

for folder, tables in data_folders.items():
    for table in tables:
        csv_path = os.path.join(base_path, folder, f"{table}.csv")
        import_csv_to_postgres(csv_path, table)
