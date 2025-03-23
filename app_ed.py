import streamlit as st
import pandas as pd
import os

# Set page config first
st.set_page_config(page_title="ED Dashboard", layout="wide")
st.title("Acil Servis (ED) Verileri")

# Örnek veri gösterimi
if os.path.exists("data/neuro_psych_patients.csv"):
    st.success("Hasta verisi bulundu.")
    try:
        sample_df = pd.read_csv("data/neuro_psych_patients.csv", nrows=5)
        st.write("📋 Örnek Hasta Verisi:", sample_df)
    except Exception as e:
        st.error(f"Hasta verisi okunamadı: {e}")
else:
    st.error("Hasta verisi dosyası bulunamadı!")

if os.path.exists("data/neuro_psych_diagnoses.csv"):
    st.success("Tanı verisi bulundu.")
else:
    st.error("Tanı verisi dosyası bulunamadı!")

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

        # anchor_age hesapla (örnek amaçlı)
        if "anchor_age" not in patients_df.columns and "intime" in patients_df.columns:
            patients_df["anchor_age"] = pd.to_datetime(patients_df["intime"], errors="coerce").dt.year - 1950

        # Filtrele
        if gender_filter != "All":
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

        # Hasta verisi ile eşleştir
        merged_df = pd.merge(patients_df, diagnoses_df, on=["subject_id", "stay_id"], how="inner")
        return merged_df

    except Exception as e:
        st.error(f"Veri yükleme/filtreleme hatası: {e}")
        return pd.DataFrame()

# Veriyi al
st.subheader("Nöropsikiyatrik Hasta Özeti")
df_summary = load_and_filter_data()

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
        "outtime": "ED Çıkış Zamanı",
        "icd_code": "ICD Kodu",
        "long_title": "Tanı Açıklaması"
    }
    df_summary.rename(columns={k: v for k, v in pretty_columns.items() if k in df_summary.columns}, inplace=True)

    st.write(f"Toplam sonuç sayısı: {len(df_summary):,}")

    # Sayfalama
    page_size = 50
    page_number = st.number_input("Sayfa numarası", min_value=1, max_value=(len(df_summary) - 1) // page_size + 1, value=1, step=1)
    start_index = (page_number - 1) * page_size
    end_index = start_index + page_size
    st.dataframe(df_summary.iloc[start_index:end_index], use_container_width=True)
else:
    st.warning("Filtrelere uygun veri bulunamadı.")
