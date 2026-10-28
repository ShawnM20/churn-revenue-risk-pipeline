import sqlite3
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_predict, StratifiedKFold
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder
from datetime import datetime

DB_PATH = 'churn.db'
EXPORT_PATH = 'churn_export.csv'


def load_data():
    conn = sqlite3.connect(DB_PATH)
    customers = pd.read_sql('SELECT * FROM customers', conn)
    conn.close()
    return customers


def build_features(df):
    df = df.copy()
    df['gender_enc'] = LabelEncoder().fit_transform(df['gender'])
    df['contract_enc'] = LabelEncoder().fit_transform(df['contract'])

    features = ['tenure', 'monthly_charges', 'total_charges', 'senior',
                'gender_enc', 'contract_enc']
    return df, features


def score_customers(df, features):
    # 5-fold cross-validation: every customer is scored by a model trained on
    # the other 80% of customers, so no one is scored by a model that saw them.
    X = df[features]
    y = df['churn']

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    probs = cross_val_predict(model, X, y, cv=cv, method='predict_proba')[:, 1]
    preds = (probs >= 0.5).astype(int)

    acc = accuracy_score(y, preds)
    print(f"  Cross-validated accuracy: {acc*100:.1f}%")
    print(classification_report(y, preds, target_names=['Retained', 'Churned']))
    return preds, probs, acc


def save_predictions(df, preds, probs, acc):
    out = df[['customer_id', 'contract', 'tenure', 'monthly_charges', 'total_charges']].copy()
    out['actual_churn'] = df['churn']
    out['churn_predicted'] = preds
    out['churn_probability'] = probs.round(4)
    # expected annual revenue lost, counted only for customers flagged as likely to churn
    out['revenue_at_risk'] = (df['monthly_charges'] * 12 * probs * preds).round(2)
    out['model_accuracy'] = round(float(acc), 4)

    conn = sqlite3.connect(DB_PATH)
    conn.execute('DROP TABLE IF EXISTS churn_predictions')
    conn.execute('''
        CREATE TABLE churn_predictions (
            customer_id      TEXT PRIMARY KEY,
            churn_actual     INTEGER,
            churn_predicted  INTEGER,
            churn_probability REAL,
            revenue_at_risk  REAL,
            model_accuracy   REAL,
            predicted_at     TEXT
        )
    ''')
    now = str(datetime.now())
    rows = [
        (r.customer_id, int(r.actual_churn), int(r.churn_predicted),
         float(r.churn_probability), float(r.revenue_at_risk), float(r.model_accuracy), now)
        for r in out.itertuples()
    ]
    conn.executemany('INSERT INTO churn_predictions VALUES (?,?,?,?,?,?,?)', rows)
    conn.commit()
    conn.close()

    # this CSV feeds the Tableau dashboard
    out.to_csv(EXPORT_PATH, index=False)

    flagged = int(out['churn_predicted'].sum())
    print(f"  {len(out)} predictions saved, {flagged} customers flagged as high risk")
    print(f"  Total annual revenue at risk: ${out['revenue_at_risk'].sum():,.0f}")


if __name__ == '__main__':
    print("Loading data...")
    customers = load_data()

    print("Building features...")
    df, features = build_features(customers)

    print("Scoring customers with cross-validated Random Forest...")
    preds, probs, acc = score_customers(df, features)

    print("Saving predictions...")
    save_predictions(df, preds, probs, acc)

    print("Done.")