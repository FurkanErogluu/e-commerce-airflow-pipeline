import json
import psycopg2
import google.generativeai as genai
from airflow.models import Variable

DB_CONFIG = {
'dbname': 'airflow', 'user': 'airflow', 'password': 'airflow',
    'host': 'postgres', 'port': '5432'
}


def generate_ai_insight():
    print("1. Aktif Simülasyon Tarihi Alınıyor...")
    target_date_str = Variable.get("SIMULASYON_TARIHI", default_var="2010-12-01")
    print(f"---> AI HEDEF TARİH: {target_date_str} <---")


    print("2. Veritabanından (daily_kpi) Günün Verileri Çekiliyor...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        #DIKKAT BU KISIMDA EXECUTE TUPLE BEKLIYORMUS BIZ DE TEK ELEMANLI TUPLE OLMASI ICIN target_date_str ye , ekledik
        cursor.execute("""
        SELECT total_revenue, total_orders, total_customers, aov, top_products, top_countries, 
            rfm_segments, hourly_sales
            FROM daily_kpi 
            WHERE target_date = %s
            """, (target_date_str,))

        row = cursor.fetchone()
        if not row:
            print(f"Uyarı: {target_date_str} tarihi için KPI verisi bulunamadı. AI analizi atlanıyor.")
            return

        #cekilen vt satirini llmin okuyabilecegi JSON formatina donusturuyoruz
        # Not: PostgreSQL'deki JSONB kolonları psycopg2 sayesinde otomatik olarak Python 'dict' formatında gelir.
        kpi_data = {
            "Toplam_Ciro": float(row[0]),
            "Toplam_Siparis": row[1],
            "Tekil_Musteri": row[2],
            "Ortalama_Sepet_Tutari": float(row[3]),
            "En_Iyi_Urunler": row[4],     #JSONB kolonlarini psycopg2, otomatik dict haline getirdi
            "En_Iyi_Ulkeler": row[5],
            "Musteri_Segmentleri": row[6],
            "Saatlik_Satislar": row[7]
        }

        # dumps: dicti -> json stringe ceviriyor bu sayede turkce karakterler bozulmadan kaliyor
        veri_metni = json.dumps(kpi_data, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"Veritabanı Okuma Hatası: {e}")
        raise e
    finally:
        """
        Biz try blogunun icerisinde conn = psycopg2.connect(**DB_CONFIG) bunu yazdik eger biz burada hata alirsak direkt
        exception icine atiyor exception sonrasi finally gececek ama biz conn kismini olusturamadigimiz icin sonraki adim olan
        cursor kismi hic olusmayacak bu yuzden finally blogunda direkt cursor_close() yazsaydik boyle bir degisken
        yok diyip cokecekti bu yuzden finally kisminda bu sekilde cursor adli degisken olusturulduysa kapat kontrolu
        ekledik.
        """
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()


    print("3. Gemini Api' ye baglaniliyor....")
    api_key = Variable.get("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-3.5-flash")

    prompt = f"""
    Sen kıdemli bir e-ticaret veri analisti ve stratejistisin. 
    Aşağıda şirketimizin {target_date_str} tarihine ait kümülatif ve günlük verileri yer almaktadır:

    {veri_metni}

    GÖREVİN:
    Bu veriyi derinlemesine incele ve yönetime sunulmak üzere kritik içgörüler çıkar.

    KURALLAR:
    1. Yorumlarında genel e-ticaret tavsiyeleri verme; doğrudan verideki SAYILARA, ÜRÜN İSİMLERİNE, ÜLKELERE veya SEGMENTLERE atıfta bulun.
    2. Kısa, net ve aksiyona dönüştürülebilir cümleler kur.
    3. Yalnızca aşağıdaki JSON şemasına birebir uyan bir yanıt ver:

    {{
        "risk_analysis": "Verideki en kritik risk/zayıflık nedir? (Örn: Cironun tek ülkeye bağımlı olması, 'Risk Altındakiler' segmentindeki müşteri sayısı veya belli saatlerdeki sipariş düşüşü). 1-2 cümle ile açıklayınız. ",
        "urgent_action": "Bugün ciro/müşteri kaybını önlemek için atılması gereken tek bir ACİL stratejik adım nedir?",
        "hidden_opportunity": "Veride ilk bakışta fark edilmeyen en büyük potansiyel fırsat nedir? (Örn: Belli saatlerdeki pik satışlar, belirli ürünlerin AOV'ye katkısı)."
    }}
    """

    print("4. Yapay Zekadan Analiz Bekleniyor...")
    response = model.generate_content(prompt)
    temiz_json_metni = response.text.replace("```json", "").replace("```", "").strip()


    print("5. Sonuclar PostgreSQL Veri tabanina (ai_insight) Kaydediliyor...")
    try:
        parsed_json = json.loads(temiz_json_metni)

        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        #insert metod !
        insert_query = """
        INSERT INTO ai_insights (
            target_date, risk_analysis, urgent_action, hidden_opportunity
        )
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (target_date) DO UPDATE SET
            risk_analysis = EXCLUDED.risk_analysis,
            urgent_action = EXCLUDED.urgent_action,
            hidden_opportunity = EXCLUDED.hidden_opportunity;
        """
        cursor.execute(insert_query, (
            target_date_str,
            parsed_json.get("risk_analysis", ""),
            parsed_json.get("urgent_action", ""),
            parsed_json.get("hidden_opportunity", "")
        ))

        conn.commit()
        print(f"Başarılı! AI içgörüleri {target_date_str} tarihi için veritabanına işlendi. ✅")

    except json.JSONDecodeError:
        print("HATA: Gemini geçerli bir JSON üretmedi. Gelen yanıt:\n", response.text)
        raise ValueError("Yapay zeka çıktısı JSON formatında değil.")
    except Exception as e:
        print(f"Veritabanı Yazma Hatası: {e}")
        raise e
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    generate_ai_insight()

