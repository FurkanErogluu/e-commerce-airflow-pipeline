import pandas as pd
import os
import json
import psycopg2
from airflow.models import Variable


base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
raw_data_path = os.path.join(base_dir, 'data', 'raw_sales.csv')

DB_CONFIG = {
'dbname': 'airflow', 'user': 'airflow', 'password': 'airflow',
    'host': 'postgres', 'port': '5432'
}

def clean_and_summarize_data():
    print('Zaman imleci kontrol ediliyor...')
    target_date_str = Variable.get('SIMULASYON_TARIHI', default_var="2010-12-01")
    target_date = pd.to_datetime(target_date_str).date() #bir stringi datetime cevirip o ogesinden sadece date i aliyor
    print(f"\n--->Aktif oldugu dusunulen gun: {target_date} ")

    print('Ham veri okunuyor')
    df = pd.read_csv(raw_data_path, encoding='unicode_escape') #encoding = e ticaret verilerindeki ozel hatalari onlermis

    print('Kalite kontrolu ve Zenginlestirme yapiliyor')
    df['InvoiceDatetime'] = pd.to_datetime(df['InvoiceDate'])
    df['InvoiceDate'] = df['InvoiceDatetime'].dt.date  # Sadece gün (Filtreleme için)
    df['InvoiceHour'] = df['InvoiceDatetime'].dt.hour  #Gruplama icin

    cleaned_df = df[(df['Quantity'] > 0) & (df['CustomerID'].notnull())].copy()
    cleaned_df['Net_Revenue'] = cleaned_df['Quantity'] * cleaned_df['UnitPrice']

    # GECMIS TREND ANALIZLERI   --     (Gelecekten veri sızmasını önlemek için)
    historical_df = cleaned_df[cleaned_df['InvoiceDate'] <= target_date]

    #GUNLUK ANALIZLER  --  (Günlük ciro ve ürünler için)
    daily_df = historical_df[historical_df['InvoiceDate'] == target_date]

    if daily_df.empty:
        print(f"Uyarı: {target_date} tarihinde hiç sipariş bulunamadı. Veritabanına 0 olarak işleniyor.")
        # Burada boş veri işleme senaryosu eklenebilir!



    """
    bu kisimda oncekine gore float int gibi degerlerinin eklenme sebebi vtye kaydederken sikinti yasamamak
    total_revenue = daily_df['Net_Revenue'].sum() ------> numpy.float64   dondururdu
    """
    print('2. Detayli Analiz Gunluk Olarak Hesaplaniyor...')

    #Genel gunluk toplam analiz
    total_revenue = float(daily_df['Net_Revenue'].sum())
    total_orders = int(daily_df['InvoiceNo'].nunique())
    total_customers = int(daily_df['CustomerID'].nunique())
    aov = float(total_revenue / total_orders) if total_orders > 0 else 0.0    #Average Order Value


    #top urun ilk 5
    top_products = daily_df.groupby('Description').agg(
        Urun_Cirosu=('Net_Revenue', 'sum'),
        Satis_Adedi=('Quantity', 'sum'),
    ).sort_values(by='Urun_Cirosu', ascending=False).head(5).reset_index() #yeni olusturdugu kolon isminden sortlama yapiyor
    # PostgreSQL JSONB için df->list of dict -> json
    top_products_json = json.dumps(top_products.to_dict(orient='records'))


    #saatlik siparis sayisi
    hourly_sales = daily_df.groupby('InvoiceHour').agg(
        Siparis_Sayisi=('InvoiceNo', 'nunique')
    ).reset_index()
    hourly_sales_json = json.dumps(hourly_sales.to_dict(orient='records'))


    #top ulke ilk 5
    top_countries = daily_df.groupby('Country').agg(
        Ulke_Cirosu = ('Net_Revenue', 'sum'),
        Ulke_Siparis_Sayisi=('InvoiceNo', 'nunique')
    ).sort_values(by = 'Ulke_Cirosu', ascending=False).head(5).reset_index()
    top_countries_json = json.dumps(top_countries.to_dict(orient='records'))



    # RFM analizi, geçmişten bugüne (target_date) kadar olan tüm verilerle yapılır, reset_index() kullanmadik!
    print('3. Kümülatif RFM Segmentasyonu Hesaplanıyor...')
    snapshot_date = target_date + pd.Timedelta(days=1)
    rfm = historical_df.groupby('CustomerID').agg(
        Recency=('InvoiceDate', lambda x: (snapshot_date - x.max()).days),
        Frequency=('InvoiceNo', 'nunique'),
        Monetary=('Net_Revenue', 'sum')
    )
    """
    rfm segment rf score hesaplamasinda ilk denedigim yontem ===> qcut hesabi verisetinin baslangic tarihlerini 
    ifade edemeyecekti, 
    Bu nedenle e ticaret icin sabit zaman ve frekans ayarlari belirleyip cesitli durumlarda tepkilerini manuel
    buna gore sekillendiririz.
    """
    # 1. Recency Puanlaması
    def rate_recency(r):
        if r <= 7:
            return 5
        elif r <= 14:
            return 4
        elif r <= 30:
            return 3
        elif r <= 60:
            return 2
        else:
            return 1

    # 2. Frequency Puanlaması
    def rate_frequency(f):
        if f >= 5:
            return 5
        elif f >= 3:
            return 4
        elif f == 2:
            return 3
        else:
            return 1  # Tek sipariş verenler

    rfm['R_Score'] = rfm['Recency'].apply(rate_recency)
    rfm['F_Score'] = rfm['Frequency'].apply(rate_frequency)
    rfm['RF_Score'] = rfm['R_Score'].astype(str) + rfm['F_Score'].astype(str) # R ve F Skorlarını Birleştirme (Örn: '55', '31')

    # 4. 5 ANA SEGMENT HARİTASI
    seg_map = {
        r'[1-2][1-2]': 'Kaybedilenler', #11, 12, 21, 22 yani [1-2] => 1 veya 2 demek
        r'[1-2][3-5]': 'Risk Altındakiler', #okumayi kolaylastirabilmek icin 2 tane Risk Altindakileri yazdik
        r'3[1-3]': 'Risk Altındakiler',
        r'[3-4][4-5]': 'Sadık Musteriler',
        r'[4-5][1-3]': 'Potansiyel / Yeni Musteriler',
        r'5[4-5]': 'En Degerli Musteriler'
    }
    #normalde replace({'55': 'Sampiyon'}) seklinde birebir eslesme arar ama bu regex eslemeyle toplu eslesme yapabiliyorsun
    rfm['Segment'] = rfm['RF_Score'].replace(seg_map, regex=True)



    # 5. VIP ETİKETİ (Geçmiş verideki %10'luk en yüksek harcama)
    if len(rfm) >= 10: # %10 hesabinda patlama olmasin diye koruma amacli ekledim
        vip_threshold = rfm['Monetary'].quantile(0.90)   # top %10'un esik degeri  (quantile - interpolasyon hesabi)
        rfm.loc[rfm['Monetary'] >= vip_threshold, 'Segment'] += ' (VIP)'

    #Sözlük yapısına dönüştürme ve ardindan dumpla
    segment_counts = rfm['Segment'].value_counts().to_dict()
    rfm_json = json.dumps(segment_counts)

    print('4. Veriler PostgreSQL Veritabanına (daily_kpi) Kaydediliyor...')
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Idempotent (Tekrarlanabilir) Veritabanı Yazımı:
        # Eğer bu tarihe ait veri varsa hata verme, üzerine yaz (UPSERT mantığı)
        insert_query = """
                INSERT INTO daily_kpi (
                target_date, total_revenue, total_orders, total_customers, aov, top_products, 
                top_countries, rfm_segments, hourly_sales
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (target_date) DO UPDATE SET
                    total_revenue = EXCLUDED.total_revenue,
                    total_orders = EXCLUDED.total_orders,
                    total_customers = EXCLUDED.total_customers,
                    aov = EXCLUDED.aov,
                    top_products = EXCLUDED.top_products,
                    top_countries = EXCLUDED.top_countries,
                    rfm_segments = EXCLUDED.rfm_segments,
                    hourly_sales = EXCLUDED.hourly_sales;
            """

        cursor.execute(insert_query, (
            target_date_str, total_revenue, total_orders, total_customers, aov, top_products_json,top_countries_json,
            rfm_json, hourly_sales_json
        ))

        conn.commit()
        print(f"Başarılı! {target_date_str} gününün verileri veritabanına kalıcı olarak işlendi. ✅")

    except Exception as e:
        print(f"Veritabanı Hatası: {e}")
        raise e

    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()


if __name__ == "__main__":
    clean_and_summarize_data()