import sqlite3
import pandas as pd

DB_PATH = 'churn.db'
CSV_PATH = 'telecom_churn.csv'


def setup_db(conn):
    conn.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            customer_id    TEXT PRIMARY KEY,
            gender         TEXT,
            senior         INTEGER,
            tenure         INTEGER,
            contract       TEXT,
            monthly_charges REAL,
            total_charges  REAL,
            churn          INTEGER
        )
    ''')


def load_customers(conn):
    df = pd.read_csv(CSV_PATH)

    df.columns = df.columns.str.strip()
    df['Churn'] = (df['Churn'] == 'Yes').astype(int)
    df['SeniorCitizen'] = df['SeniorCitizen'].astype(int)
    # 11 new customers (tenure 0) have a blank TotalCharges, so set those to 0
    df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce').fillna(0)

    rows = []
    for _, row in df.iterrows():
        rows.append((
            str(row['customerID']),
            str(row['gender']),
            int(row['SeniorCitizen']),
            int(row['tenure']),
            str(row['Contract']),
            float(row['MonthlyCharges']),
            float(row['TotalCharges']),
            int(row['Churn']),
        ))

    conn.execute('DELETE FROM customers')
    conn.executemany(
        'INSERT OR REPLACE INTO customers VALUES (?,?,?,?,?,?,?,?)',
        rows
    )
    print(f"  {len(rows)} customers loaded")
    return df


if __name__ == '__main__':
    print("Setting up database...")
    conn = sqlite3.connect(DB_PATH)
    setup_db(conn)

    print("Loading customer data...")
    load_customers(conn)

    conn.commit()
    conn.close()
    print("Done.")
