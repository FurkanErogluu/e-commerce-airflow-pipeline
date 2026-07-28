#amacimiz yazilan python scriptlerini airflowun yonetebilecegi tasklara bolme ve birbirine baglama
from airflow.cli.cli_config import TASKS_COMMANDS
from airflow.decorators import dag, task
from datetime import datetime
import os
import sys
from airflow.models import Variable
import pandas as pd



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
from scripts.ai_action import generate_ai_insight
from scripts.alert_bot import check_and_alert

#macimdeki data klasoru docker da ->./data:/opt/airflow/data  yani /opt/airflow/data klasorune denk gelir
raw_data_path = "/opt/airflow/data/raw_sales.csv"

"""
bu kisimda alttaki basit bir fonksiyonu resmi bir airflow dag yapisina donusturuyor airflow web UI bu etiketi okur
SCHEDULAR birkac saniye de bir dags klasorunu kontrol eder bu sayede yeni eklenilen dagi fark eder ve calisma sekliyle 
beraber arayuze yansitir .
"""

@dag(
    dag_id='ecommerce_time_machine_pipeline',     #arayuzde sol kisimda gozukecek benzersiz dag adi
    start_date=datetime(2023,1,1),   #BUNU YAZMAK ZORUNLU
    schedule=None,    #zamansiz calisacak manuel olarak yani
    catchup=False,    #(True :start datein belirttigi tarihten bu yana gecmis gunler icin de calisir), gecmise bakma demis oluyoruz
    tags=["ecommerce", "etl", "best_practice", "llm", "time_windowing"]
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


    #TASK 3: VERILER ICIN YZ CIKTISINI ALMA
    @task
    def ai_insight_task():
        generate_ai_insight()


    @task
    def advance_simulation_date():
        current_date_str = Variable.get("SIMULASYON_TARIHI", default_var="2010-12-01")
        #Bu sekilde tarih kisminda herhangi bir yanlislik yasanmiyormus!
        current_date = pd.to_datetime(current_date_str)
        next_date = current_date + pd.Timedelta(days=1)
        next_date_str = next_date.strftime("%Y-%m-%d")

        Variable.set("SIMULASYON_TARIHI", next_date_str) #set!
        print(f"Zaman 1 gun ileri alindi: Sistem {current_date_str} tarihinden {next_date_str} tarihine başarıyla geçirildi!")


    @task
    def anomaly_alert_task():
        check_and_alert()


    #TASK BAGIMLILIKLARI
    check_raw_data() >> process_data_task() >> ai_insight_task() >> anomaly_alert_task() >> advance_simulation_date()
    #right shift (>>) operatoru gorevlerin sirasini belirler

#DAG'i tanimla ve baslat! SART(Normal fonk cagirmak gibi)
ecommerce_pipeline()








