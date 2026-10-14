-- Когорты по первому заказу клиента + retention по месяцам
WITH first_order AS (
    SELECT
        customer_unique_id,
        MIN(order_month) AS cohort_month
    FROM orders
    WHERE order_status = 'delivered'
    GROUP BY customer_unique_id
),
activity AS (
    SELECT DISTINCT
        o.customer_unique_id,
        f.cohort_month,
        o.order_month AS activity_month,
        -- Номер периода относительно когорты
        (
            (CAST(SUBSTR(o.order_month, 1, 4) AS INTEGER) -
             CAST(SUBSTR(f.cohort_month, 1, 4) AS INTEGER)) * 12
            + (CAST(SUBSTR(o.order_month, 6, 2) AS INTEGER) -
               CAST(SUBSTR(f.cohort_month, 6, 2) AS INTEGER))
        ) AS month_offset
    FROM orders o
    JOIN first_order f USING (customer_unique_id)
    WHERE o.order_status = 'delivered'
),
cohort_size AS (
    SELECT cohort_month, COUNT(*) AS size
    FROM first_order
    GROUP BY cohort_month
)
SELECT
    a.cohort_month,
    a.month_offset,
    COUNT(DISTINCT a.customer_unique_id) AS active_customers,
    cs.size AS cohort_size,
    ROUND(100.0 * COUNT(DISTINCT a.customer_unique_id) / cs.size, 2) AS retention_pct
FROM activity a
JOIN cohort_size cs USING (cohort_month)
WHERE a.month_offset BETWEEN 0 AND 12
GROUP BY a.cohort_month, a.month_offset, cs.size
ORDER BY a.cohort_month, a.month_offset;