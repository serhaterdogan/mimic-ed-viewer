import streamlit as st
import pandas as pd
import os

# Set page config first
st.set_page_config(page_title="ED Dashboard", layout="wide")
st.title("Acil Servis (ED) Verileri")

# Filtreler
st.sidebar.header("Filtreler")
icd_filter = st.sidebar.text_input("ICD Kodu veya Tanı Adı ile Filtrele", value="", key="icd_filter")
gender_filter = st.sidebar.selectbox("Cinsiyet Seçin", ("All", "M", "F"), key="gender_filter")
age_min, age_max = st.sidebar.slider("Yaş Aralığı", 0, 120, (18, 90), key="age_slider")

# Hasta ve tanı verilerini yükle
def load_and_filter_data():
    try:
        patients_df = pd.read_csv("data/neuro_psych_patients.csv")
        diagnoses_df = pd.read_csv("data/neuro_psych_diagnoses.csv")
        base_patients_df = pd.read_csv("data/patients.csv") if os.path.exists("data/patients.csv") else pd.DataFrame()

        if not base_patients_df.empty:
            base_patients_df = base_patients_df[["subject_id", "anchor_age"]]
            patients_df = pd.merge(patients_df, base_patients_df, on="subject_id", how="left")

        if gender_filter != "All" and "gender" in patients_df.columns:
            patients_df = patients_df[patients_df["gender"] == gender_filter]

        if "anchor_age" in patients_df.columns:
            patients_df["anchor_age"] = pd.to_numeric(patients_df["anchor_age"], errors="coerce")
            patients_df = patients_df[(patients_df["anchor_age"] >= age_min) & (patients_df["anchor_age"] <= age_max)]

        # ICD filtrelemesi
        if icd_filter:
            icd_cols = ['icd_code', 'icd_title', 'diagnosis', 'long_title']
            matched = False
            for col in icd_cols:
                if col in diagnoses_df.columns:
                    diagnoses_df = diagnoses_df[diagnoses_df[col].astype(str).str.contains(icd_filter, case=False, na=False)]
                    matched = True
                    break
            if not matched:
                st.warning("Filtreleme için uygun tanı sütunu bulunamadı.")

        merged_df = pd.merge(patients_df, diagnoses_df, on=["subject_id"], how="inner")
        return merged_df

    except Exception as e:
        st.error(f"Veri yükleme/filtreleme hatası: {e}")
        return pd.DataFrame()

# Veriyi al
st.subheader("Nöropsikiyatrik Hasta Özeti")
df_summary = load_and_filter_data()

if not df_summary.empty:
    selected_columns = [
        "subject_id", "hadm_id", "stay_id", "gender", "anchor_age",
        "marital_status", "race", "icd_code", "icd_title", "long_title"
    ]
    df_summary = df_summary[[col for col in selected_columns if col in df_summary.columns]]

    pretty_columns = {
        "subject_id": "Hasta ID",
        "hadm_id": "Yatış ID",
        "stay_id": "Klinik Kalış ID",
        "gender": "Cinsiyet",
        "anchor_age": "Yaş",
        "marital_status": "Medeni Durum",
        "race": "Irk",
        "icd_code": "ICD Kodu",
        "icd_title": "ICD Başlığı",
        "long_title": "Tanı Açıklaması"
    }
    df_summary.rename(columns=pretty_columns, inplace=True)

    st.write(f"Toplam sonuç sayısı: {len(df_summary):,}")

    page_size = 50
    page_number = st.number_input("Sayfa numarası", min_value=1, max_value=(len(df_summary) - 1) // page_size + 1, value=1, step=1)
    start_index = (page_number - 1) * page_size
    end_index = start_index + page_size
    st.dataframe(df_summary.iloc[start_index:end_index], use_container_width=True)
else:
    st.warning("Filtrelere uygun veri bulunamadı.")