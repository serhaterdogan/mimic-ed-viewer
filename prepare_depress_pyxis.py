import pandas as pd

# Dosyaları yükle
depress_patients = pd.read_csv("data/depress_patients.csv")
pyxis = pd.read_csv("data/pyxis.csv")

# Filtrele: sadece depresyon hastalarına ait kayıtlar
filtered_pyxis = pyxis[pyxis['subject_id'].isin(depress_patients['subject_id'].unique())]

# Kolonları yeniden adlandır (uygulamadaki görsel tutarlılık için)
filtered_pyxis = filtered_pyxis.rename(columns={
    "charttime": "starttime",
    "name": "medication"
})

# İsteğe bağlı: sadece kullanılan kolonları tut
columns_to_keep = ["subject_id", "stay_id", "starttime", "medication"]
filtered_pyxis = filtered_pyxis[columns_to_keep]

# Kaydet
filtered_pyxis.to_csv("data/depress_pyxis.csv", index=False)

print("✅ depress_pyxis.csv dosyası başarıyla oluşturuldu.")
