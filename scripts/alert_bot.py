import requests
import psycopg2
from psycopg2.extras import RealDictCursor
from airflow.models import Variable
from sqlalchemy.engine import url

DB_CONFIG = {
    'dbname': 'airflow', 'user': 'airflow', 'password': 'airflow',
    'host': 'postgres', 'port': '5432'
}

def check_and_alert():
    print("1. Telegram bot kimlikleri kontrol ediliyor...")
    bot_token = Variable.get("TELEGRAM_BOT_TOKEN", default_var=None)
    chat_id = Variable.get("TELEGRAM_CHAT_ID", default_var=None)
    target_date_str = Variable.get("SIMULASYON_TARIHI", default_var="2010-12-01")

    if not bot_token or not chat_id:
        print("Uyarı: Telegram Token veya Chat ID bulunamadı.")
        return

    print(f"2. {target_date_str} ve dünün verileri karşılaştırılıyor...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""
            SELECT target_date, total_revenue, total_orders 
            FROM daily_kpi 
            WHERE target_date <= %s
            ORDER BY target_date DESC 
            LIMIT 2;
        """, (target_date_str,))

        records = cursor.fetchall()
        if len(records) == 0: return

        today_data = records[0]
        today_rev = float(today_data["total_revenue"])

        alert_message = None

        if today_rev == 0:
            alert_message = (
                f" *BİLGİLENDİRME: İşlemsiz Gün* \n\n"
                f" *Tarih:* {target_date_str}\n\n"
                f"Bugün herhangi bir sipariş veya ciro kaydı bulunamadı (Hafta sonu veya resmi tatil). Veri boru hattı sorunsuz çalıştı ve günü pas geçti."
            )

        elif len(records) == 2:
            yesterday_data = records[1]
            yesterday_rev = float(yesterday_data["total_revenue"])

            if yesterday_rev > 0:
                change_rate = ((today_rev - yesterday_rev) / yesterday_rev) *100

                if change_rate >= 50:
                    alert_message = (
                        f" *GÜNLÜK REKOR: Satışlar Patladı!* \n\n"
                        f" *Tarih:* {target_date_str}\n"
                        f" *Büyüme Oranı:* %{change_rate:.1f}\n\n"
                        f"Dün: £{yesterday_rev:.2f}\n"
                        f"Bugün: £{today_rev:.2f}\n\n"
                        f"Harika bir gün! Bu ivmeyi sağlayan kampanyaları veya en çok satan ürünleri panelden kontrol edin."
                    )

                elif change_rate <= 50:
                    alert_message = (
                        f"⚠️ *ANOMALİ: Satışlarda Sert Düşüş* ⚠️\n\n"
                        f"📅 *Tarih:* {target_date_str}\n"
                        f"📉 *Düşüş Oranı:* %{abs(change_rate):.1f}\n\n"
                        f"Dün: £{yesterday_rev:.2f}\n"
                        f"Bugün: £{today_rev:.2f}\n\n"
                        f"Satışlarda dramatik bir çakılma var. Pazar veya stok durumunu inceleyin."
                    )


        if alert_message:
            print("Alarm mesaji tetiklendi. Telegram'a mesaj gonderiliyor...")
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": alert_message,
                "parse_mode": "Markdown"
            }
            requests.post(url, json=payload)
            print("Telegram mesaji basariyla gonderildi.")
        else:
            print("Standart bir gun ekstra bildirim gonderilmedi.")


    except Exception as e:
        print(f"Hata: {e}")
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

if __name__ == '__main__':
    check_and_alert()








