import streamlit as st
import pandas as pd
import os

# CSV veri yükleme fonksiyonu
def get_data_csv(path):
    try:
        return pd.read_csv(path)
    except Exception as e:
        st.error(f"CSV yükleme hatası: {e}")
        return pd.DataFrame()

st.set_page_config(page_title="ED Dashboard", layout="wide")
st.title("🏥 Acil Servis (ED) Verileri")

# 🔍 Filtreler
st.sidebar.header("🔍 Filtreler")
icd_filter = st.sidebar.text_input("ICD Kodu ile Filtrele", key="icd_filter")
gender_filter = st.sidebar.selectbox("Cinsiyet Seçin", ("All", "M", "F"), key="gender_filter")
age_min, age_max = st.sidebar.slider("Yaş Aralığı", 0, 120, (18, 33), key="age_slider")

# 🔍 Nöropsikiyatrik Hasta Bilgileri Tablosu
st.subheader("📿 Nöropsikiyatrik Hasta Özeti")
df_summary = get_data_csv("data/neuro_psych_patients.csv")
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

    # Filtre uygula
    if gender_filter != "All":
        df_summary = df_summary[df_summary["Cinsiyet"] == gender_filter]
    df_summary = df_summary[(df_summary["Yaş"] >= age_min) & (df_summary["Yaş"] <= age_max)]

    st.write(f"Toplam sonuç sayısı: {len(df_summary):,}")

    # Sayfalama
    page_size = 50
    page_number = st.number_input("Sayfa numarası", min_value=1, max_value=(len(df_summary) - 1) // page_size + 1, value=1, step=1)
    start_index = (page_number - 1) * page_size
    end_index = start_index + page_size
    st.dataframe(df_summary.iloc[start_index:end_index], use_container_width=True)
else:
    st.warning("Filtrelere uygun veri bulunamadı.")