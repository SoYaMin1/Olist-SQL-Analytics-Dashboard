-- RFM-анализ с window functions + CTE
WITH snapshot AS (
    SELECT DATE(MAX(order_purchase_timestamp), '+1 day') AS snapshot_date
    FROM orders
),
customer_rfm AS (
    SELECT
        o.customer_unique_id,
        CAST(
            JULIANDAY((SELECT snapshot_date FROM snapshot)) -
            JULIANDAY(MAX(DATE(o.order_purchase_timestamp)))
            AS INTEGER
        ) AS recency_days,
        COUNT(DISTINCT o.order_id) AS frequency,
        ROUND(SUM(o.order_total), 2) AS monetary
    FROM orders o
    WHERE o.order_status = 'delivered'
    GROUP BY o.customer_unique_id
),
scored AS (
    SELECT
        customer_unique_id,
        recency_days,
        frequency,
        monetary,
        NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,
        NTILE(5) OVER (ORDER BY frequency ASC)  AS f_score,
        NTILE(5) OVER (ORDER BY monetary ASC)   AS m_score
    FROM customer_rfm
),
segmented AS (
    SELECT
        customer_unique_id,
        recency_days,
        frequency,
        monetary,
        r_score, f_score, m_score,
        (r_score + f_score + m_score) AS rfm_total,
        CASE
            WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
            WHEN r_score >= 3 AND f_score >= 3 THEN 'Loyal'
            WHEN r_score >= 4 AND f_score <= 2 THEN 'New Customers'
            WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk'
            WHEN r_score <= 2 AND f_score <= 2 AND m_score <= 2 THEN 'Lost'
            ELSE 'Potential Loyalist'
        END AS segment
    FROM scored
)
SELECT
    segment,
    COUNT(*) AS customers,
    ROUND(AVG(recency_days), 0) AS avg_recency,
    ROUND(AVG(frequency), 2) AS avg_frequency,
    ROUND(AVG(monetary), 2) AS avg_monetary,
    ROUND(SUM(monetary), 2) AS total_revenue,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM segmented), 2) AS pct_customers
FROM segmented
GROUP BY segment
ORDER BY total_revenue DESC;