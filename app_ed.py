import streamlit as st
import pandas as pd
import os
import re

# Set page config first
st.set_page_config(page_title="ED Dashboard", layout="wide")
st.title("Acil Servis (ED) Verileri")

# Hasta ve tanı verilerini yüklemeden önce boş filtre kutuları oluşturmak için değerleri çekelim
def load_unique_filters():
    admissions_df = pd.read_csv("data/admissions.csv") if os.path.exists("data/admissions.csv") else pd.DataFrame()
    if not admissions_df.empty:
        return {
            "admission_type": sorted(admissions_df["admission_type"].dropna().unique().tolist()),
            "admission_location": sorted(admissions_df["admission_location"].dropna().unique().tolist()),
            "discharge_location": sorted(admissions_df["discharge_location"].dropna().unique().tolist()),
        }
    return {"admission_type": [], "admission_location": [], "discharge_location": []}

filter_options = load_unique_filters()

# Filtreler
st.sidebar.header("Filtreler")

# ICD kodları dropdown için ICD başlıkları yükleniyor
try:
    diag_full = pd.read_csv("data/depress_diagnoses.csv")
    icd_options = sorted(diag_full['long_title'].dropna().unique().tolist()) if 'long_title' in diag_full.columns else []
    icd_code_options = sorted(diag_full['icd_code'].dropna().unique().tolist()) if 'icd_code' in diag_full.columns else []
except:
    icd_options = []
    icd_code_options = []

chiefcomplaint_filter = st.sidebar.text_input("Hasta Şikayeti ile Filtrele", value="", key="cc_filter", label_visibility="visible")
icd_filter = st.sidebar.multiselect("Tanı Seçin (ICD Açıklaması)", icd_options, key="icd_filter_dropdown")
icd_code_filter = st.sidebar.multiselect("ICD Kodu Seçin", icd_code_options, key="icd_code_filter_dropdown")
gender_filter = st.sidebar.selectbox("Cinsiyet Seçin", ("All", "M", "F"), key="gender_filter")
age_min, age_max = st.sidebar.slider("Yaş Aralığı", 18, 120, (18, 101), key="age_slider")
adm_type_filter = st.sidebar.selectbox("Yatış Türü", ["All"] + filter_options["admission_type"], key="adm_type")
adm_loc_filter = st.sidebar.selectbox("Başvuru Yeri", ["All"] + filter_options["admission_location"], key="adm_loc")
disch_loc_filter = st.sidebar.selectbox("Taburcu Yeri", ["All"] + filter_options["discharge_location"], key="disch_loc")

# Disposition filtrelemesi
try:
    edstays_df = pd.read_csv("data/depress_patients.csv")
    disposition_options = sorted(edstays_df['disposition'].dropna().unique().tolist()) if 'disposition' in edstays_df.columns else []
except:
    disposition_options = []
disposition_filter = st.sidebar.multiselect("Çıkış Durumu (Disposition)", disposition_options, default=disposition_options)

# Hasta ve tanı verilerini yükle
def load_and_filter_data():
    try:
        patients_df = pd.read_csv("data/depress_patients.csv")
        diagnoses_df = pd.read_csv("data/depress_diagnoses.csv")
        base_patients_df = pd.read_csv("data/patients.csv") if os.path.exists("data/patients.csv") else pd.DataFrame()
        admissions_df = pd.read_csv("data/admissions.csv") if os.path.exists("data/admissions.csv") else pd.DataFrame()
        triage_df = pd.read_csv("data/triage.csv") if os.path.exists("data/triage.csv") else pd.DataFrame()

        if not base_patients_df.empty:
            base_patients_df = base_patients_df[["subject_id", "anchor_age"]]
            patients_df = pd.merge(patients_df, base_patients_df, on="subject_id", how="left")

        if not admissions_df.empty:
            admissions_df = admissions_df[["subject_id", "hadm_id", "admission_type", "admission_location", "discharge_location"]]
            if "hadm_id" in patients_df.columns:
                patients_df = pd.merge(patients_df, admissions_df, on=["subject_id", "hadm_id"], how="left")
            else:
                patients_df = pd.merge(patients_df, admissions_df, on="subject_id", how="left")

        if not triage_df.empty and "chiefcomplaint" in triage_df.columns:
            triage_df = triage_df[["subject_id", "stay_id", "chiefcomplaint"]]
            patients_df = pd.merge(patients_df, triage_df, on=["subject_id", "stay_id"], how="left")

        if gender_filter != "All" and "gender" in patients_df.columns:
            patients_df = patients_df[patients_df["gender"] == gender_filter]

        if "anchor_age" in patients_df.columns:
            patients_df["anchor_age"] = pd.to_numeric(patients_df["anchor_age"], errors="coerce")
            patients_df = patients_df[(patients_df["anchor_age"] >= age_min) & (patients_df["anchor_age"] <= age_max)]

        if adm_type_filter != "All" and "admission_type" in patients_df.columns:
            patients_df = patients_df[patients_df["admission_type"] == adm_type_filter]

        if adm_loc_filter != "All" and "admission_location" in patients_df.columns:
            patients_df = patients_df[patients_df["admission_location"] == adm_loc_filter]

        if disch_loc_filter != "All" and "discharge_location" in patients_df.columns:
            patients_df = patients_df[patients_df["discharge_location"] == disch_loc_filter]

        if icd_filter:
            diagnoses_df = diagnoses_df[diagnoses_df['long_title'].isin(icd_filter)]

        if icd_code_filter:
            diagnoses_df = diagnoses_df[diagnoses_df['icd_code'].isin(icd_code_filter)]

        if chiefcomplaint_filter and "chiefcomplaint" in patients_df.columns:
            patients_df = patients_df[patients_df["chiefcomplaint"].astype(str).str.contains(chiefcomplaint_filter, case=False, na=False)]

        merge_keys = ["subject_id"]
        if "hadm_id" in patients_df.columns and "hadm_id" in diagnoses_df.columns:
            merge_keys.append("hadm_id")

        merged_df = pd.merge(patients_df, diagnoses_df, on=merge_keys, how="inner")

        if 'disposition' in patients_df.columns and disposition_filter:
            merged_df = merged_df[merged_df['disposition'].isin(disposition_filter)]

        merged_df.drop_duplicates(subset=["subject_id", "hadm_id", "icd_code"], inplace=True)

        # 💡 Add ML label for admission prediction
        merged_df["admitted"] = merged_df["admission_type"].apply(lambda x: 0 if pd.isna(x) or x == "" else 1)

        # Klinik notları ekle
        try:
            notes_df = pd.read_csv("data/depress_notes.csv")
            merged_df = pd.merge(merged_df, notes_df, on=["subject_id", "hadm_id"], how="left")
        except:
            st.warning("Klinik notlar yüklenemedi.")

        # Laboratuvar verilerini ekle
        try:
            labs_df = pd.read_csv("data/depress_labs.csv")
            merged_df = pd.merge(merged_df, labs_df, on=["subject_id", "hadm_id"], how="left")
        except:
            st.warning("Laboratuvar verileri yüklenemedi.")

        # Save for ML
        merged_df.to_csv("data/ml_admission_dataset.csv", index=False)

        return merged_df

    except Exception as e:
        st.error(f"Veri yükleme/filtreleme hatası: {e}")
        return pd.DataFrame()

# 👁️‍🗨️ Görüntüleme
st.subheader("📋 Filtrelenmiş Veriler")
df_summary = load_and_filter_data()
if not df_summary.empty:
    st.dataframe(df_summary, use_container_width=True)
else:
    st.warning("Filtrelere uygun veri bulunamadı.")
