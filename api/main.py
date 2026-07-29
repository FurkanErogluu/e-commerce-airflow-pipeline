from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor

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
    'host': 'postgres', 'port': '5432'
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


@app.get("/api/dashboard/history")
def get_historical_data():
    print("İstek alındı: Geçmiş 14 günün trend verisi çekiliyor...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Son 14 günün verisini al, ancak grafikte soldan sağa doğru (eskiden yeniye)
        # düzgün çizilebilmesi için alt sorgu (subquery) ile ASC (artan) sıraya diz.
        query = """
            SELECT target_date, total_revenue, total_orders 
            FROM (
                SELECT target_date, total_revenue, total_orders 
                FROM daily_kpi 
                ORDER BY target_date DESC 
                LIMIT 14
            ) AS subquery
            ORDER BY target_date ASC;
        """
        cursor.execute(query)
        results = cursor.fetchall()

        if not results:
            raise HTTPException(status_code=404, detail="Geçmiş veri bulunamadı.")

        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()