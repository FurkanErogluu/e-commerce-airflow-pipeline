import pandas as pd
import os


base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
raw_data_path = os.path.join(base_dir, 'data', 'raw_sales.csv')
processed_data_path = os.path.join(base_dir, 'data', 'sales_summary.json')

def clean_and_summarize_data():
    print('Ham veri okunuyor')
    df = pd.read_csv(raw_data_path, encoding='unicode_escape') #encoding = e ticaret verilerindeki ozel hatalari onlermis

    print('Kalite kontrolu ve Zenginlestirme yapiliyor')
    cleaned_df = df[ (df['Quantity'] > 0) & (df['CustomerID'].notnull())].copy() #iptal siparisleri cikart
    cleaned_df['Net_Revenue'] = cleaned_df['Quantity'] * cleaned_df['UnitPrice']

    print('KPI - Analitik Ozet Uretiliyor')
    # Ülkelere göre Toplam Ciro ve Toplam Benzersiz Sipariş sayısını hesapla

    summary_df = cleaned_df.groupby('Country').agg(   #name aggretation yapisidir
        TotalRevenue = ('Net_Revenue', 'sum'),
        TotalOrder = ('InvoiceNo', 'nunique')     #count ile nunique farkli; nunique:benzersiz bakiyor
    ).reset_index() #sart eger olmazsa country bizim indeks kisminda yani normal sutunlarin 1 alt satirinda yer alir ve df['Country'] ile ulasamayiz
    #indeks kismini resetleyerek 0 1 2 3 4... seklinde yeni indeksler olusmus olur

    # En yüksek ciro yapan ilk 5 ülkeyi seç (LLM'in kafası çok fazla veriyle karışmasın diye)
    top5_countries = summary_df.sort_values(by=['TotalRevenue'], ascending=False).head(5)

    # Bu kisimda orient python->json ciktisinin nasil yapilandirilacagini belirler(record - split - index - column)
    top5_countries.to_json(processed_data_path, orient='records')
    print(f"\nİşlem Başarılı! Özet veri şuraya kaydedildi: {processed_data_path}")
    print("\nİşte İlk 5 Ülkenin Çıktısı:")
    print(top5_countries)

if __name__ == "__main__":
    clean_and_summarize_data()