# Makine Öğrenmesi için veri hazırlık scripti
import pandas as pd
import os

# Gerekli dosyaları yükle
patients_df = pd.read_csv("data/depress_patients.csv")
admissions_df = pd.read_csv("data/admissions.csv")
diag_df = pd.read_csv("data/depress_diagnoses.csv")
labs_df = pd.read_csv("data/depress_labs.csv")

# hadm_id sütunlarını normalize et, varsa uygula
for df in [patients_df, admissions_df]:
    if 'hadm_id' in df.columns:
        df['hadm_id'] = df['hadm_id'].astype(str).str.extract(r'(\d+)')

if 'hadm_id' in diag_df.columns:
    diag_df['hadm_id'] = diag_df['hadm_id'].astype(str).str.extract(r'(\d+)')

# Gerekli birleştirmeleri yap
if 'hadm_id' in diag_df.columns and 'hadm_id' in patients_df.columns:
    base = pd.merge(patients_df, admissions_df, on=["subject_id", "hadm_id"], how="left")
    base = pd.merge(base, diag_df, on=["subject_id", "hadm_id"], how="left")
else:
    base = pd.merge(patients_df, admissions_df, on=["subject_id"], how="left")
    base = pd.merge(base, diag_df, on=["subject_id"], how="left")

# Laboratuvar sonuçlarını ortalama değerler olarak grupla
if not labs_df.empty:
    lab_agg = labs_df.groupby("subject_id")["valuenum"].mean().reset_index()
    lab_agg.rename(columns={"valuenum": "lab_mean"}, inplace=True)
    base = pd.merge(base, lab_agg, on="subject_id", how="left")

# Gereksiz sütunları temizle
base = base.drop(columns=["icd_title", "long_title"], errors="ignore")

# Eksik verileri işle
base = base.dropna(subset=["disposition"])  # hedef değişken eksikse çıkar
base.fillna("unknown", inplace=True)

# Veriyi kaydet
base.to_csv("data/ml_input_data.csv", index=False)

print("Makine öğrenmesi için veri hazırlandı ve 'ml_input_data.csv' dosyasına kaydedildi.")
