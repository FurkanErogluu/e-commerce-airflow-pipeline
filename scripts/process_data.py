import pandas as pd
import os
import json


base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
raw_data_path = os.path.join(base_dir, 'data', 'raw_sales.csv')
processed_data_path = os.path.join(base_dir, 'data', 'sales_summary.json')

def clean_and_summarize_data():
    print('Ham veri okunuyor')
    df = pd.read_csv(raw_data_path, encoding='unicode_escape') #encoding = e ticaret verilerindeki ozel hatalari onlermis

    print('Kalite kontrolu ve Zenginlestirme yapiliyor')
    cleaned_df = df[ (df['Quantity'] > 0) & (df['CustomerID'].notnull())].copy() #iptal siparisleri cikart
    cleaned_df['Net_Revenue'] = cleaned_df['Quantity'] * cleaned_df['UnitPrice']
    cleaned_df['InvoiceDate'] = pd.to_datetime(cleaned_df['InvoiceDate']) #tarih kolonunu pandasin anlayacagi sekle donusturduk

    print('KPI - Analitik Ozet Uretiliyor')
    total_revenue = cleaned_df['Net_Revenue'].sum()
    total_orders = cleaned_df['InvoiceNo'].nunique()
    total_customers = cleaned_df['CustomerID'].nunique()
    aov = total_revenue / total_orders if total_orders > 0 else 0  #Average Order Value


    general_kpis = {
        "Toplam_Ciro": round(total_revenue, 2),
        "Toplam_Siparis": round(total_orders, 2),
        "Tekil_Musteri_Sayisi": total_customers,
        "Ortalama_Siparis_Tutari": round(aov, 2)
    }


    top_products = cleaned_df.groupby('Description').agg(
        Urun_Ciro=('Net_Revenue', 'sum'),
        Urun_Siparis_Adedi=('Quantity', 'sum')
    ).sort_values(by='Urun_Ciro', ascending=False).head(5).reset_index()


    # Ülkelere göre Toplam Ciro ve Toplam Benzersiz Sipariş sayısını hesapla
    top_countries = (cleaned_df.groupby('Country').agg(   #name aggretation yapisidir(agg...)
        Ulke_Ciro = ('Net_Revenue', 'sum'),
        Ulke_Siparis_Adedi = ('InvoiceNo', 'nunique')   #count ile nunique farkli; nunique:benzersiz bakiyor
    ).sort_values(by=['Ulke_Ciro'], ascending=False).head(5).reset_index())
    """
    reset_index() sart eger olmazsa country bizim indeks kisminda yani normal sutunlarin 1 alt satirinda yer alir ve df['Country'] ile ulasamayiz
    reset index ile --> indeks kismini resetleyerek 0 1 2 3 4... seklinde yeni indeksler olusmus olur
    """


    print('RFM Analiz ve Musteri Segmentasyonu Yapiliyor...')
    snapshot_date = cleaned_df['InvoiceDate'].max() + pd.Timedelta(days=1)
    """
    recency = Son siparis tarihinden bugune kadar gecen gun sayisini hesaplar eger burada snapshot
    alacagimiz tarihi bugunun tarihi olarak secsek eski bir veri seti oldugu icin butun veriler churn 
    sinifina atilacakti
    """

    #Her musteri icin rfm hesaplamasi
    rfm = cleaned_df.groupby('CustomerID').agg(   # RECENCY - FREQUENCY - MONETARY
        {
            'InvoiceDate' : lambda x: (snapshot_date- x.max()).days, #RECENCY
            'InvoiceNo' : 'nunique',   #FREQUENCY
            'Net_Revenue' : 'sum'  #MONETARY
        }
    ).rename(columns={'InvoiceDate' : 'RECENCY', 'InvoiceNo' : 'FREQUENCY', 'Net_Revenue' : 'MONETARY'})

    def rfm_segment(row):
        if row['RECENCY'] <= 30 and row['FREQUENCY'] >=3:
            return 'Sık Musteri'
        elif row['RECENCY'] > 90 and row['FREQUENCY'] ==1:
            return 'Kaybedilen'
        elif row['RECENCY'] >60:
            return 'Risk Altindaki (Churn Uyarisi)'
        else:
            return 'Potansiyel Sadik'

    rfm['SEGMENT'] = rfm.apply(rfm_segment, axis=1)   #   ! rfm.apply(rfm_segment, axis=1)
    segment_counts = rfm['SEGMENT'].value_counts().to_dict()
    #Bu kisimda value_counts ciktisi bir series bunu dicte cevirmemiz lazim cunku json: series, df tanimaz

    #json modulu hicbir pandas objesini dogrudan JSON yapmaz bunlari bir sekilde list ve dict yapisina cevirmeliyiz.
    dashboard_data = {
        'Genel KPI': general_kpis,   #SOZLUK-DICT YAPIDA
        'En iyi Urunler' : top_products.to_dict(orient='records'), #LISTE-[] yani sozluk listesi YAPISINDA
        'En iyi Ulkeler' : top_countries.to_dict(orient='records'),#LISTE-[] yani sozluk listesi YAPISINDA
        'Musteri Segmentleri' : segment_counts #SOZLUK-DICT YAPIDA
    }

    print('Detayli Veriler JSON olarak kaydediliyor...')
    with open(processed_data_path, 'w', encoding='utf-8') as f:
        json.dump(dashboard_data, f, ensure_ascii=False, indent=4)

    print(f'\nIslem Basarili! Analiz Ciktilari suraya kaydedildi: {processed_data_path}')


if __name__ == "__main__":
    clean_and_summarize_data()