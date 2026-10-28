import sqlite3
import pandas as pd
from textblob import TextBlob
from datetime import datetime

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
    conn.execute('''
        CREATE TABLE IF NOT EXISTS sentiment_scores (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id    TEXT,
            review_text    TEXT,
            polarity       REAL,
            subjectivity   REAL,
            sentiment      TEXT,
            scored_at      TEXT
        )
    ''')


def load_customers(conn):
    df = pd.read_csv(CSV_PATH)

    df.columns = df.columns.str.strip()
    df['Churn'] = (df['Churn'] == 'Yes').astype(int)
    df['SeniorCitizen'] = df['SeniorCitizen'].astype(int)
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


def generate_reviews(df):
    review_templates = {
        0: [
            "Great service, very happy with the plan.",
            "Reliable connection and fair pricing.",
            "Customer support was helpful and fast.",
            "No complaints, service works perfectly.",
            "Very satisfied, will stay long term.",
        ],
        1: [
            "Terrible service, thinking of leaving.",
            "Too expensive for what you get.",
            "Connection drops constantly, very frustrated.",
            "Support never resolves my issues.",
            "Cancelling soon, not worth the price.",
        ]
    }

    import random
    random.seed(42)
    records = []
    sample = df.sample(min(500, len(df)), random_state=42)

    for _, row in sample.iterrows():
        churn = int(row['Churn'])
        text = random.choice(review_templates[churn])
        blob = TextBlob(text)
        sentiment = 'positive' if blob.sentiment.polarity > 0 else ('negative' if blob.sentiment.polarity < 0 else 'neutral')
        records.append((
            str(row['customerID']),
            text,
            round(blob.sentiment.polarity, 4),
            round(blob.sentiment.subjectivity, 4),
            sentiment,
            str(datetime.now()),
        ))

    return records


def save_sentiment(conn, records):
    conn.execute('DELETE FROM sentiment_scores')
    conn.executemany(
        'INSERT INTO sentiment_scores (customer_id, review_text, polarity, subjectivity, sentiment, scored_at) VALUES (?,?,?,?,?,?)',
        records
    )
    print(f"  {len(records)} sentiment scores saved")


if __name__ == '__main__':
    print("Setting up database...")
    conn = sqlite3.connect(DB_PATH)
    setup_db(conn)

    print("Loading customer data...")
    df = load_customers(conn)

    print("Scoring sentiment...")
    records = generate_reviews(df)
    save_sentiment(conn, records)

    conn.commit()
    conn.close()
    print("Done.")
