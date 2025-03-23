import streamlit as st
import pandas as pd
import os

# Hafıza dostu CSV filtreleme fonksiyonu
def get_filtered_data(path, gender_filter, age_min, age_max, icd_filter):
    chunks = []
    try:
        for chunk in pd.read_csv(path, chunksize=5000):
            if 'gender' in chunk.columns and 'anchor_age' in chunk.columns:
                if gender_filter != "All":
                    chunk = chunk[chunk["gender"] == gender_filter]
                chunk = chunk[(chunk["anchor_age"] >= age_min) & (chunk["anchor_age"] <= age_max)]
                if icd_filter:
                    if 'icd_code' in chunk.columns:
                        chunk = chunk[chunk['icd_code'].astype(str).str.contains(icd_filter)]
                chunks.append(chunk)
    except Exception as e:
        st.error(f"CSV parça okuma hatası: {e}")
        return pd.DataFrame()
    return pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()

st.set_page_config(page_title="ED Dashboard", layout="wide")
st.title("Acil Servis (ED) Verileri")

# Filtreler
st.sidebar.header("Filtreler")
icd_filter = st.sidebar.text_input("ICD Kodu ile Filtrele", value="7840", key="icd_filter")
gender_filter = st.sidebar.selectbox("Cinsiyet Seçin", ("All", "M", "F"), key="gender_filter")
age_min, age_max = st.sidebar.slider("Yaş Aralığı", 0, 120, (18, 35), key="age_slider")

# Nöropsikiyatrik Hasta Bilgileri Tablosu
st.subheader("Nöropsikiyatrik Hasta Özeti")
df_summary = get_filtered_data("data/neuro_psych_patients.csv", gender_filter, age_min, age_max, icd_filter)
if not df_summary.empty:
    pretty_columns = {
        "subject_id": "Hasta ID",
        "hadm_id": "Yatış ID",
        "gender": "Cinsiyet",
        "anchor_age": "Yaş",
        "race": "Irk",
        "arrival_transport": "Transfer Yolu",
        "disposition": "Son Durum",
        "intime": "ED Giriş Zamanı",
        "outtime": "ED Çıkış Zamanı"
    }
    df_summary.rename(columns=pretty_columns, inplace=True)

    st.write(f"Toplam sonuç sayısı: {len(df_summary):,}")

    # Sayfalama
    page_size = 50
    page_number = st.number_input("Sayfa numarası", min_value=1, max_value=(len(df_summary) - 1) // page_size + 1, value=1, step=1)
    start_index = (page_number - 1) * page_size
    end_index = start_index + page_size
    st.dataframe(df_summary.iloc[start_index:end_index], use_container_width=True)
else:
    st.warning("Filtrelere uygun veri bulunamadı.")