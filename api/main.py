from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor

from scripts.process_data import DB_CONFIG

app = FastAPI(title = "E-Ticaret Analitik API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#dockerdaki vtye baglanma icin
DB_CONFIG = {
    'dbname': 'airflow', 'user': 'airflow', 'password': 'airflow',
    'host': 'localhost', 'port': '5433'
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)


@app.get("/api/dashboard/latest")
def get_latest_dashboard_data():
    print("Istek alindi: En guncel analizler cekiliyor...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor) #RealDictCursor

        query = """
        SELECT k.target_date, k.total_revenue, k.total_orders, k.total_customers, 
                k.aov, k.top_products, k.top_countries, k.rfm_segments, k.hourly_sales,
                a.risk_analysis, a.urgent_action, a.hidden_opportunity
            FROM daily_kpi k 
            LEFT JOIN ai_insights a ON k.target_date = a.target_date
            ORDER BY k.target_date DESC
            LIMIT 1;
        """

        cursor.execute(query)
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Henuz veri tabaninda islenmis bir veri yok.")

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))  #bu sekilde exception yazimi yapilabiliyor:
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()
        
