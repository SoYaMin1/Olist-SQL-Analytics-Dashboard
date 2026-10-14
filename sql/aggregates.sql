-- 1. KPI по месяцам
WITH monthly AS (
    SELECT
        order_month,
        COUNT(*) AS orders_cnt,
        COUNT(DISTINCT customer_unique_id) AS unique_customers,
        ROUND(SUM(order_total), 2) AS revenue,
        ROUND(AVG(order_total), 2) AS avg_check,
        ROUND(AVG(review_score), 2) AS avg_review,
        ROUND(AVG(delivery_days), 1) AS avg_delivery_days,
        SUM(CASE WHEN late_delivery = 1 THEN 1 ELSE 0 END) AS late_orders
    FROM orders
    WHERE order_status = 'delivered'
    GROUP BY order_month
)
SELECT
    order_month,
    orders_cnt,
    unique_customers,
    revenue,
    avg_check,
    avg_review,
    avg_delivery_days,
    late_orders,
    ROUND(100.0 * late_orders / orders_cnt, 2) AS late_pct,
    -- LAG: сравнение с прошлым месяцем
    ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY order_month))
          / NULLIF(LAG(revenue) OVER (ORDER BY order_month), 0), 2) AS revenue_growth_pct
FROM monthly
ORDER BY order_month;