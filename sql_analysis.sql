-- Churn rate by contract type
SELECT
    contract,
    COUNT(*) AS total_customers,
    SUM(churn) AS churned,
    ROUND(SUM(churn) * 100.0 / COUNT(*), 1) AS churn_rate_pct,
    ROUND(AVG(monthly_charges), 2) AS avg_monthly_charge
FROM customers
GROUP BY contract
ORDER BY churn_rate_pct DESC;


-- Revenue at risk by contract segment
SELECT
    c.contract,
    COUNT(p.customer_id) AS at_risk_customers,
    ROUND(SUM(p.revenue_at_risk), 2) AS total_revenue_at_risk,
    ROUND(AVG(p.churn_probability) * 100, 1) AS avg_churn_prob_pct
FROM churn_predictions p
JOIN customers c ON p.customer_id = c.customer_id
WHERE p.churn_predicted = 1
GROUP BY c.contract
ORDER BY total_revenue_at_risk DESC;


-- High risk customers (top revenue at risk)
SELECT
    p.customer_id,
    c.contract,
    c.tenure,
    c.monthly_charges,
    ROUND(p.churn_probability * 100, 1) AS churn_prob_pct,
    ROUND(p.revenue_at_risk, 2) AS annual_revenue_at_risk
FROM churn_predictions p
JOIN customers c ON p.customer_id = c.customer_id
WHERE p.churn_predicted = 1
ORDER BY p.revenue_at_risk DESC
LIMIT 20;
