import streamlit as st
import pandas as pd
import os

# Hafıza dostu CSV filtreleme fonksiyonu
def get_filtered_data(path, gender_filter, age_min, age_max):
    chunks = []
    try:
        for chunk in pd.read_csv(path, chunksize=5000):
            # Gerekli sütunları kontrol et
            if 'gender' in chunk.columns and 'anchor_age' in chunk.columns:
                if gender_filter != "All":
                    chunk = chunk[chunk["gender"] == gender_filter]
                chunk = chunk[(chunk["anchor_age"] >= age_min) & (chunk["anchor_age"] <= age_max)]
                chunks.append(chunk)
    except Exception as e:
        st.error(f"CSV parça okuma hatası: {e}")
        return pd.DataFrame()
    return pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()

st.set_page_config(page_title="ED Dashboard", layout="wide")
st.title("\ud83c\udfe5 Acil Servis (ED) Verileri")

# \ud83d\udd0d Filtreler
st.sidebar.header("\ud83d\udd0d Filtreler")
icd_filter = st.sidebar.text_input("ICD Kodu ile Filtrele", key="icd_filter")
gender_filter = st.sidebar.selectbox("Cinsiyet Se\u00e7in", ("All", "M", "F"), key="gender_filter")
age_min, age_max = st.sidebar.slider("Ya\u015f Aral\u0131\u011f\u0131", 0, 120, (18, 33), key="age_slider")

# \ud83d\udd0d N\u00f6ropsikiyatrik Hasta Bilgileri Tablosu
st.subheader("\ud83d\udcff N\u00f6ropsikiyatrik Hasta \u00d6zeti")
df_summary = get_filtered_data("data/neuro_psych_patients.csv", gender_filter, age_min, age_max)
if not df_summary.empty:
    pretty_columns = {
        "subject_id": "Hasta ID",
        "hadm_id": "Yat\u0131\u015f ID",
        "gender": "Cinsiyet",
        "anchor_age": "Ya\u015f",
        "race": "Irk",
        "arrival_transport": "Transfer Yolu",
        "disposition": "Son Durum",
        "intime": "ED Giri\u015f Zaman\u0131",
        "outtime": "ED \u00c7\u0131k\u0131\u015f Zaman\u0131"
    }
    df_summary.rename(columns=pretty_columns, inplace=True)

    st.write(f"Toplam sonu\u00e7 say\u0131s\u0131: {len(df_summary):,}")

    # Sayfalama
    page_size = 50
    page_number = st.number_input("Sayfa numaras\u0131", min_value=1, max_value=(len(df_summary) - 1) // page_size + 1, value=1, step=1)
    start_index = (page_number - 1) * page_size
    end_index = start_index + page_size
    st.dataframe(df_summary.iloc[start_index:end_index], use_container_width=True)
else:
    st.warning("Filtrelere uygun veri bulunamad\u0131.")