import streamlit as st
import pandas as pd
import os
import re
import matplotlib.pyplot as plt

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

# Ek verileri yükle

def load_optional_data(filename):
    return pd.read_csv(filename) if os.path.exists(filename) else pd.DataFrame()

notes_df = load_optional_data("data/depress_notes.csv")
meds_df = load_optional_data("data/depress_meds.csv")
medrecon_df = load_optional_data("data/depress_medrecon.csv")
pyxis_df = load_optional_data("data/depress_pyxis.csv")
labs_df = load_optional_data("data/depress_labs.csv")

# Highlight fonksiyonu
def highlight_keywords(text):
    keywords = [
        "History of Present Illness", "Past Medical History", "Social History",
        "Physical Exam", "Hospital Course", "Discharge Diagnosis",
        "Discharge Medications", "Followup Instructions"
    ]
    for kw in keywords:
        pattern = re.compile(rf"(\b{re.escape(kw)}\b)", re.IGNORECASE)
        text = pattern.sub(r"\n\n### \1\n", text)
    return text

# Chiefcomplaint filtresi merge sonrası da uygulanmalı
def apply_post_merge_filter(df):
    if chiefcomplaint_filter and "Hasta Şikayeti" in df.columns:
        pattern = rf"(?<!\\w){re.escape(chiefcomplaint_filter)}(?!\\w)"
        df = df[df["Hasta Şikayeti"].fillna("").astype(str).str.contains(pattern, case=False, na=False, regex=True)]
    return df

# Hasta detayında notlar, lab, ilaçları göster

def show_patient_details(subject_id):
    if not subject_id:
        return

    if not labs_df.empty:
        hasta_labs = labs_df[labs_df['subject_id'] == subject_id]
        if not hasta_labs.empty:
            st.markdown("### 🔬 Laboratuvar Sonuçları")
            st.dataframe(hasta_labs, use_container_width=True)

    if not meds_df.empty:
        hasta_meds = meds_df[meds_df['subject_id'] == subject_id]
        if not hasta_meds.empty:
            st.markdown("### 💊 Kullanılan İlaçlar")
            st.dataframe(hasta_meds, use_container_width=True)

    if not medrecon_df.empty:
        hasta_medrec = medrecon_df[medrecon_df['subject_id'] == subject_id]
        if not hasta_medrec.empty:
            st.markdown("### 🗂️ İlaç Geçmişi (Medication Reconciliation)")
            st.dataframe(hasta_medrec, use_container_width=True)

    if not pyxis_df.empty:
        hasta_pyxis = pyxis_df[pyxis_df['subject_id'] == subject_id]
        if not hasta_pyxis.empty:
            st.markdown("### 💉 Acil Serviste Verilen İlaçlar (Pyxis)")
            st.dataframe(hasta_pyxis, use_container_width=True)

    if not notes_df.empty:
        hasta_notes = notes_df[notes_df['subject_id'] == subject_id]
        if not hasta_notes.empty:
            st.markdown("### 📝 Klinik Notlar")
            for _, note in hasta_notes.iterrows():
                formatted_note = highlight_keywords(note['text'])
                st.markdown(f"<div style='white-space: pre-wrap; font-family: monospace; background-color: #f4f4f4; padding: 10px; border-radius: 5px;'>\n<b>Zaman:</b> {note['charttime']}<br><b>Not Tipi:</b> {note['note_type']}<br><b>Yatış ID:</b> {note.get('hadm_id', '-')}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='white-space: pre-wrap; font-family: monospace; background-color: #fdfdfd; padding: 10px; border-radius: 5px;'>{formatted_note}</div>", unsafe_allow_html=True)
                st.markdown("---")

# Yeni kod: Veriyi yükle ve göster
@st.cache_data

def load_filtered_summary():
    try:
        df = pd.read_csv("data/depress_summary.csv")
        df = apply_post_merge_filter(df)
        return df
    except:
        return pd.DataFrame()

df_summary = load_filtered_summary()

if not df_summary.empty:
    st.subheader("📋 Major Depresif Hasta Özeti")
    st.dataframe(df_summary, use_container_width=True)

    total_rows = len(df_summary)
    unique_patients = df_summary['Hasta ID'].nunique()
    st.write(f"Toplam sonuç sayısı: {total_rows:,} | Toplam hasta sayısı: {unique_patients:,}")

    selected_id = st.selectbox("Detayını görüntülemek istediğiniz hastayı seçin:", df_summary["Hasta ID"].unique())
    show_patient_details(selected_id)
else:
    st.warning("Major Depresif tanısı almış hasta bulunamadı.")