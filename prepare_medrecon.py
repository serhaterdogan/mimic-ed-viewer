# depress_medrecon_create.py
import pandas as pd

# Gerekli dosyaları yükle
depress_patients = pd.read_csv("data/depress_patients.csv")
medrecon = pd.read_csv("data/medrecon.csv")

# Gerekli kolon varsa, NaN olmayan subject_id değerleri üzerinden filtrele
if 'subject_id' in depress_patients.columns and 'subject_id' in medrecon.columns:
    filtered_medrecon = medrecon[medrecon['subject_id'].isin(depress_patients['subject_id'].unique())]
    
    # Yeni dosyaya kaydet
    filtered_medrecon.to_csv("data/depress_medrecon.csv", index=False)
    print("depress_medrecon.csv başarıyla oluşturuldu.")
else:
    print("Hatalı sütun adı: 'subject_id' bazı dosyalarda bulunamadı.")
