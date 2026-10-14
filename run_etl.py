"""Точка входа ETL: загрузка → очистка → запись в SQLite."""
from etl.loader import load_csv
from etl.cleaner import clean_sellers, clean_orders
from etl.db_writer import get_engine, init_schema, write_df


def main():
    engine = get_engine()
    init_schema(engine)

    print("Загружаем sellers...")
    sellers = clean_sellers(load_csv("sellers_clean.csv"))

    print("Загружаем orders (может занять ~10 сек)...")
    orders = clean_orders(load_csv("master_orders.csv"))

    # Справочник клиентов (уникальные customer_id)
    customers = (
        orders[
            [
                "customer_id",
                "customer_unique_id",
                "customer_zip_code_prefix",
                "customer_city",
                "customer_state",
            ]
        ]
        .drop_duplicates(subset=["customer_id"])
        .reset_index(drop=True)
    )

    write_df(sellers, "sellers", engine)
    write_df(customers, "customers", engine)
    write_df(orders, "orders", engine)
    print("ETL завершён")
    

if __name__ == "__main__":
    main()