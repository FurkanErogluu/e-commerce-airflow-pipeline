#amacimiz yazilan python scriptlerini airflowun yonetebilecegi tasklara bolme ve birbirine baglama

from airflow.decorators import dag, task
from datetime import datetime
import os
import sys


"""
Pyhona nereye bakmasi gerektigini soyluyoruz;
Bunu daha oncesinden soyluyoruz yoksa konteynir icinde clean_and_summarize dosyasini bulamaz

Cunku docker isin icine girdiginde benim tum proje klasorlerim konteynir icindeki /opt/airflow/ a kopyalanir(MOUNT EDILIR)
DAG dosyaların: /opt/airflow/dags/ klasöründedir.
Script dosyaların: /opt/airflow/scripts/ klasöründedir.

Benim airflowda bu scriptin bulundugu dizinin bir ust dizine cikmam gerekirki process_datayi gorsun
"""
sys.path.append('/opt/airflow')
from scripts.process_data import clean_and_summarize_data


#macimdeki data klasoru docker da ->./data:/opt/airflow/data  yani /opt/airflow/data klasorune denk gelir
raw_data_path = "/opt/airflow/data/raw_sales.csv"

"""
bu kisimda alttaki basit bir fonksiyonu resmi bir airflow dag yapisina donusturuyor airflow web UI bu etiketi okur
SCHEDULAR birkac saniye de bir dags klasorunu kontrol eder bu sayede yeni eklenilen dagi fark eder ve calisma sekliyle 
beraber arayuze yansitir .
"""

@dag(
    dag_id='ecommerce_sales_pipeline_modular',     #arayuzde sol kisimda gozukecek benzersiz dag adi
    start_date=datetime(2023,1,1),   #BUNU YAZMAK ZORUNLU
    schedule=None,    #zamansiz calisacak manuel olarak yani
    catchup=False,    #(True :start datein belirttigi tarihten bu yana gecmis gunler icin de calisir), gecmise bakma demis oluyoruz
    tags=["ecommerce", "etl", "best_practice"]
)

def ecommerce_pipeline():

    # TASK 1: KAYNAK VERI KONTROLU
    @task
    def check_raw_data():
        if not os.path.exists(raw_data_path):
            raise FileNotFoundError(f"HATA: {raw_data_path} konumunda veri bulunamadı!")
        print("Veri dosyası sistemde mevcut, veri işleme adımına geçiliyor.")


    #TASK 2: VERI ISLEME SCRIPTINI TETIKLEME
    @task
    def process_data_task():
        """scripts/process_data.py içindeki clean_and_summarize_data fonksiyonunu çalıştırır."""
        clean_and_summarize_data()


    #TASK BAGIMLILIKLARI
    check_raw_data() >> process_data_task() #right shift (>>) operatoru gorevlerin sirasini belirler

#DAG'i tanimla ve baslat! SART(Normal fonk cagirmak gibi)
ecommerce_pipeline()








