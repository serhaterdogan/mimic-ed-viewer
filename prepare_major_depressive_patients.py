import pandas as pd
import os

# Dosya yolları
DIAGNOSIS_PATH = "data/diagnosis.csv"
ICD_DEF_PATH = "data/d_icd_diagnoses.csv"
EDSTAYS_PATH = "data/edstays.csv"

OUTPUT_DIAG = "data/depress_diagnoses.csv"
OUTPUT_PATIENTS = "data/depress_patients.csv"

# Anahtar kelimelerle eşleşme yapacağız
keywords = [
    "depress"
]

# Dosyaları yükle
try:
    diagnosis_df = pd.read_csv(DIAGNOSIS_PATH)
    icd_df = pd.read_csv(ICD_DEF_PATH)
    edstays_df = pd.read_csv(EDSTAYS_PATH)
except Exception as e:
    print(f"Dosya yüklenirken hata: {e}")
    exit(1)

# ICD tanıları ile eşleştir
merged_df = diagnosis_df.merge(icd_df, on="icd_code", how="left")

# Nörolojik / psikiyatrik ICD tanılarını filtrele
filtered_df = merged_df[merged_df["long_title"].str.lower().str.contains("|".join(keywords), na=False)]

# Hasta listesini filtrele
filtered_patients_df = edstays_df[edstays_df["subject_id"].isin(filtered_df["subject_id"])]

# Çıktıları kaydet
os.makedirs("data", exist_ok=True)
filtered_df.to_csv(OUTPUT_DIAG, index=False)
filtered_patients_df.to_csv(OUTPUT_PATIENTS, index=False)

print(f"✅ {OUTPUT_DIAG} ve {OUTPUT_PATIENTS} dosyaları oluşturuldu.")
