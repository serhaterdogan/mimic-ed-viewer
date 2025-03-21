import pandas as pd
import os

# Klasörleri belirt
hosp_dir = "hosp"
ed_dir = "ed"
data_dir = "data"
os.makedirs(data_dir, exist_ok=True)

# Gerekli CSV'leri yükle
print("CSV dosyaları yükleniyor...")
diagnosis = pd.read_csv(os.path.join(ed_dir, "diagnosis.csv"))
edstays = pd.read_csv(os.path.join(ed_dir, "edstays.csv"))
triage = pd.read_csv(os.path.join(ed_dir, "triage.csv"))
patients = pd.read_csv(os.path.join(hosp_dir, "patients.csv"))
admissions = pd.read_csv(os.path.join(hosp_dir, "admissions.csv"))
d_icd = pd.read_csv(os.path.join(hosp_dir, "d_icd_diagnoses.csv"))

# FULL PATIENT
print("full_patient.csv oluşturuluyor...")
df_full = diagnosis.merge(edstays, on=["subject_id", "stay_id"], how="left") \
                 .merge(patients, on="subject_id", how="left") \
                 .merge(admissions, on="hadm_id", how="left") \
                 .merge(d_icd, on="icd_code", how="left")
df_full.to_csv(os.path.join(data_dir, "full_patient.csv"), index=False)

# TOP DIAGNOSES
print("top_diagnoses.csv oluşturuluyor...")
df_top = diagnosis.merge(patients, on="subject_id", how="left") \
                 .merge(d_icd, on="icd_code", how="left")
top_diag = df_top.groupby(["icd_code", "long_title"]).size().reset_index(name="frequency")
top_diag = top_diag.sort_values("frequency", ascending=False)
top_diag.to_csv(os.path.join(data_dir, "top_diagnoses.csv"), index=False)

# LOS
print("los.csv oluşturuluyor...")
edstays["intime"] = pd.to_datetime(edstays["intime"])
edstays["outtime"] = pd.to_datetime(edstays["outtime"])
edstays["los_hours"] = (edstays["outtime"] - edstays["intime"]).dt.total_seconds() / 3600
edstays[["subject_id", "stay_id", "los_hours"]].to_csv(os.path.join(data_dir, "los.csv"), index=False)

# TREND
print("trend.csv oluşturuluyor...")
edstays["visit_day"] = edstays["intime"].dt.date
trend = edstays.groupby("visit_day").size().reset_index(name="visits")
trend.to_csv(os.path.join(data_dir, "trend.csv"), index=False)

# TRIAGE
print("triage.csv kaydediliyor...")
triage.to_csv(os.path.join(data_dir, "triage.csv"), index=False)

# DEMO
print("demo.csv oluşturuluyor...")
demo = admissions.merge(patients, on="subject_id", how="left")
demo.to_csv(os.path.join(data_dir, "demo.csv"), index=False)

# COMPLAINT - DIAGNOSIS
print("complaint_diag.csv oluşturuluyor...")
if "chiefcomplaint" in triage.columns:
    complaint_diag = triage[["subject_id", "stay_id", "chiefcomplaint"]].merge(
        diagnosis, on=["subject_id", "stay_id"], how="left")
    complaint_diag = complaint_diag.merge(d_icd, on="icd_code", how="left")
    complaint_diag = complaint_diag.rename(columns={"chiefcomplaint": "complaint", "long_title": "diagnosis"})
    complaint_diag.to_csv(os.path.join(data_dir, "complaint_diag.csv"), index=False)
else:
    print("triage.csv dosyasında 'chiefcomplaint' alanı bulunamadı.")

print("Tüm CSV dosyaları 'data/' klasörüne kaydedildi.")
