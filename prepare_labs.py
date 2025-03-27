import pandas as pd

# Nöropsikiyatrik hastaların olduğu dosyayı yükle
neuro_df = pd.read_csv("data/S06.csv")
subject_ids = set(neuro_df["subject_id"])  # Hızlı filtreleme için set'e çeviriyoruz

# Yalnızca gerekli sütunları belirleyin
cols = ["subject_id", "hadm_id", "charttime", "itemid", "value", "valuenum", "valueuom", "flag"]

# labevents.csv dosyasını parça parça oku
chunksize = 100000
filtered_chunks = []

for chunk in pd.read_csv("data/labevents.csv", usecols=cols, chunksize=chunksize):
    # Nöropsikiyatrik hastaları filtrele
    filtered_chunk = chunk[chunk["subject_id"].isin(subject_ids)]
    filtered_chunks.append(filtered_chunk)

# Parçaları birleştir
filtered_labs = pd.concat(filtered_chunks, ignore_index=True)

# Test ismini itemid ile eşleştir
labitems_df = pd.read_csv("data/d_labitems.csv")
if "itemid" in filtered_labs.columns and "itemid" in labitems_df.columns:
    labitems_df = labitems_df[["itemid", "label"]].drop_duplicates()
    filtered_labs = filtered_labs.merge(labitems_df, on="itemid", how="left")
    filtered_labs.rename(columns={"label": "test_name"}, inplace=True)

# Sonuçları kaydet
filtered_labs.to_csv("data/neuro_psych_labs.csv", index=False)
print(f"✅ Filtered lab data saved. Total rows: {len(filtered_labs)}")
