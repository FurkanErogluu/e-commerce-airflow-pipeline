import json

import pandas as pd
import google.generativeai as genai
import os
from airflow.models import Variable

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
processed_data_path = os.path.join(base_dir, 'data', 'sales_summary.json')
ai_output_path = os.path.join(base_dir, 'data', 'ai_insights.json')

def generate_ai_insights():
    print('1- Dosya Kontrol Ediliyor..')
    if not os.path.exists(processed_data_path):
        raise FileNotFoundError("Ozet icin bir veri bulunamadi")

    print('2- Ozet Veri Okunuyor..')
    #geminiye giden metini duzeltmek ve okunabilirligi arttirmak:

    #pd.read_json yapisindan dosya ile okuma yapisina gectik.
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
        Aşağıda şirketimizin güncel KPI'ları, en çok satan ürünleri, en iyi ülkeleri ve müşteri RFM segmentleri bulunuyor:
        
        {veri_metni}
        
        Lütfen bu veriyi incele (özellikle Churn Riski Taşıyan ve Kaybedilen müşterilere dikkat et) ve 
        bana SADECE aşağıdaki formata birebir uyan, geçerli bir JSON çıktısı ver. 
        Lütfen markdown işaretleri (```json) veya ekstra açıklamalar KULLANMA, doğrudan süslü parantez ile başla:
        
        {{
            "risk_analizi": "Verideki en büyük risk veya zayıf nokta nedir? Birkaç cümleyle özetle.",
            "acil_aksiyon": "Satışları artırmak veya müşteri kaybını önlemek için hemen yapılması gereken eylem nedir?",
            "gizli_firsat": "Verideki en büyük potansiyel veya fırsat alanı nedir?"
        }}
        """

    print('4- Yapay Zekadan Analiz Bekleniyor...')
    response = model.generate_content(prompt)

    #Gemininin ekledigi markdown bloklarini
    temiz_json_metni = response.text.replace("```json", "").replace("```", "").strip()

    print("5- Yanıt alındı, diske kaydediliyor...")
    # Çıktının gerçekten geçerli bir JSON olup olmadığını kontrol edip kaydediyoruz
    try:
        parsed_json = json.loads(temiz_json_metni)
        with open(ai_output_path, "w", encoding="utf-8") as f:
            json.dump(parsed_json, f, ensure_ascii=False, indent=4)
        print(f"\nİşlem Başarılı! AI Analizi JSON olarak kaydedildi: {ai_output_path}")
    except json.JSONDecodeError:
        print("HATA: Gemini geçerli bir JSON üretmedi. Gelen yanıt:\n", response.text)
        raise ValueError("Yapay zeka çıktısı JSON formatında değil.")

if __name__ == "__main__":
    generate_ai_insights()