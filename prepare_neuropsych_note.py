import pandas as pd

# Nöropsikiyatrik hastaların subject_id'lerini al
neuro_psych_ids = pd.read_csv("data/migraine.csv")["Hasta ID"].unique()

# Discharge ve radyoloji notlarını yükle
try:
    discharge = pd.read_csv("data/discharge.csv")
    radiology = pd.read_csv("data/radiology.csv")
except FileNotFoundError:
    print("Discharge veya Radiology dosyası bulunamadı")
    exit()

# Nöropsikiyatrik hastalara ait notları filtrele
neuro_notes_discharge = discharge[discharge["subject_id"].isin(neuro_psych_ids)]
neuro_notes_radiology = radiology[radiology["subject_id"].isin(neuro_psych_ids)]

# Kategori sütunu ekleyelim
neuro_notes_discharge["category"] = "Discharge"
neuro_notes_radiology["category"] = "Radiology"

# Ortak sütunları birleştirecek şekilde normalize et (text, subject_id, hadm_id, charttime)
common_cols = ["note_id", "Hasta ID", "hadm_id", "note_type", "note_seq", "charttime", "storetime", "text", "category"]
all_neuro_notes = pd.concat([
    neuro_notes_discharge[common_cols],
    neuro_notes_radiology[common_cols]
], ignore_index=True)

# Dosyayı kaydet
all_neuro_notes.to_csv("data/neuro_psych_notes.csv", index=False)
print("neuro_psych_notes.csv dosyası başarıyla oluşturuldu.")
