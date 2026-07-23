import os
import json
from jinja2 import Environment, FileSystemLoader

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(base_dir, 'data')
templates_dir = os.path.join(base_dir, 'templates')

def create_html_report():
    print('1- JSON veri dosyalari okunuyor...')
    with open(os.path.join(data_dir, 'sales_summary.json'), 'r', encoding='utf-8') as f:
        sales_data = json.load(f)

    with open(os.path.join(data_dir, 'ai_insights.json'), 'r', encoding='utf-8') as f:
        ai_data = json.load(f)



    """
    Jinja motorunu calistirma:
    bu kisimda jinjaya git benim templates adli klasorume bak bu klasorde dashboard_template.html adinda
    ici bos hook(kanca)larla dolu iskelet goreceksin bunu bastan sona oku icindeki butun {{..}} ve {%...%} 
    kancalarini tek tek tespit et ve bir haritasini cikart tum bu yapiyi RAM'e al ve templeate adinda beklet.
    """
    print('2- JINJA2 sablonu yukleniyor... ')
    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template('dashboard_template.html')


    print('3- Veriler HTML icine render ediliyor...')
    # jinja2ye templeatede data ile baslayan biryer gorursen sales_data json yapisina bak ai ile baslayan gorursen
    # ai_data isimli dosyaya bak.
    html_content = template.render(data=sales_data, ai=ai_data)

    print('4-Nihai Dashboard Kaydediliyor...')
    output_path = os.path.join(data_dir, 'Final_Dashboard.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"İşlem Başarılı! Rapor oluşturuldu: {output_path}")

if __name__ == "__main__":
    create_html_report()