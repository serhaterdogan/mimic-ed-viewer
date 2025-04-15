import pandas as pd

# Dosyaları oku
depress_patients = pd.read_csv("data/depress_patients.csv")  # major depresif hastalar
prescriptions = pd.read_csv("data/prescriptions.csv")  # tüm ilaçlar

# Yalnızca major depresif hastalara ait ilaçları al
filtered_meds = prescriptions[prescriptions["subject_id"].isin(depress_patients["subject_id"].unique())]

# Yeni dosya olarak kaydet
filtered_meds.to_csv("data/depress_meds.csv", index=False)

print("depress_meds.csv başarıyla oluşturuldu.")
