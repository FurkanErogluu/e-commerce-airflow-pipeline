import json

import pandas as pd
import google.generativeai as genai
import os
from airflow.models import Variable

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
processed_data_path = os.path.join(base_dir, 'data', 'sales_summary.json')
ai_output_path = os.path.join(base_dir, 'data', 'ai_insights.txt')

def generate_ai_insights():
    print('1- Dosya Kontrol Ediliyor..')
    if not os.path.exists(processed_data_path):
        raise FileNotFoundError("Ozet icin bir veri bulunamadi")

    print('2- Ozet Veri Okunuyor..')
    #geminiye giden metini duzeltmek ve okunabilirligi arttirmak:

    with open(processed_data_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    veri_metni = json.dumps(data, ensure_ascii=False, indent=2)

    print('3- Gemini Apiye Baglaniliyor...')
    api_key = Variable.get('GEMINI_API_KEY')
    genai.configure(api_key=api_key)   #Bu kisimda bu configureyi yapmayi kacirmamak lazim!
    # --- BURAYI EKLE ---
    print("--- SENİN HESABINA AÇIK OLAN MODELLER ---")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
    print("------------------------------------------")
    model = genai.GenerativeModel("gemini-3.5-flash")  #dikkat GenerativeModel olacak dogrusu!

    prompt = f"""
        Sen kıdemli bir e-ticaret veri analisti ve stratejistisin. 
        Aşağıda şirketimizin en çok ciro (TotalRevenue) getiren ilk 5 ülkesinin özet satış verileri bulunuyor:
        
        {veri_metni}
        
        Lütfen bu veriyi incele ve satışları daha da artırmak, pazarlama stratejimizi optimize etmek için 
        bize uygulanabilir, net ve 3 maddelik bir aksiyon planı çıkar.
        """

    print('4- Yapay Zekadan Analiz Bekleniyor...')
    response = model.generate_content(prompt)

    print("5- Yanıt alındı, diske kaydediliyor...")
    # AI'ın ürettiği metni klasörümüze .txt olarak kaydediyoruz
    with open(ai_output_path, "w", encoding="utf-8") as f:
        f.write(response.text)

    print(f"\nİşlem Başarılı! Yapay zeka analizi şuraya kaydedildi: {ai_output_path}")
    print("\n--- GEMINI AKSİYON PLANI ---\n", response.text)






