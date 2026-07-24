import psycopg2

DB_CONFIG = {
    'dbname': 'airflow',
    'user': 'airflow',
    'password': 'airflow',
    'host': 'localhost',
    'port': '5433'
}

def create_tables():
    print("1. PostgreSQL veritabanına bağlanılıyor...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        print("2. 'daily_kpi' tablosu (JSONB destekli) oluşturuluyor...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_kpi (
                id SERIAL PRIMARY KEY,
                target_date DATE UNIQUE NOT NULL,
                total_revenue NUMERIC(15, 2),
                total_orders INTEGER,
                total_customers INTEGER,
                aov NUMERIC(10, 2),
                top_products JSONB,     
                top_countries JSONB,
                rfm_segments JSONB,  
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        print("3. 'ai_insights' tablosu oluşturuluyor...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ai_insights (
                id SERIAL PRIMARY KEY,
                target_date DATE UNIQUE NOT NULL,
                risk_analysis TEXT,
                urgent_action TEXT,
                hidden_opportunity TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        conn.commit()
        cursor.close()
        conn.close()
        print("İşlem Başarılı! Veritabanı tabloları modern mimari için hazırlandı. ✅")

    except Exception as e:
        print(f"HATA OLUŞTU: {e}")

if __name__ == "__main__":
    create_tables()