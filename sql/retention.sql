-- Retention: доля клиентов, вернувшихся за повторной покупкой
WITH customer_orders AS (
    SELECT
        customer_unique_id,
        customer_state,
        COUNT(DISTINCT order_id) AS total_orders,
        MIN(order_purchase_timestamp) AS first_order,
        MAX(order_purchase_timestamp) AS last_order
    FROM orders
    WHERE order_status = 'delivered'
    GROUP BY customer_unique_id, customer_state
)
SELECT
    customer_state,
    COUNT(*) AS customers,
    SUM(CASE WHEN total_orders > 1 THEN 1 ELSE 0 END) AS returning_customers,
    ROUND(100.0 * SUM(CASE WHEN total_orders > 1 THEN 1 ELSE 0 END)
          / COUNT(*), 2) AS retention_pct,
    ROUND(AVG(total_orders), 2) AS avg_orders_per_customer
FROM customer_orders
GROUP BY customer_state
HAVING customers >= 50
ORDER BY retention_pct DESC;