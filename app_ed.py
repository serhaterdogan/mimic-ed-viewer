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
    if chiefcomplaint_filter and "chiefcomplaint" in df.columns:
        df = df[df["chiefcomplaint"].astype(str).str.contains(chiefcomplaint_filter, case=False, na=False)]
    return df

# Hasta ve tanı verilerini yükle
def load_and_filter_data():
    try:
        patients_df = pd.read_csv("data/depress_patients.csv")
        diagnoses_df = pd.read_csv("data/depress_diagnoses.csv")
        base_patients_df = load_optional_data("data/patients.csv")
        admissions_df = load_optional_data("data/admissions.csv")
        triage_df = load_optional_data("data/triage.csv")

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

        merge_keys = ["subject_id"]
        if "hadm_id" in patients_df.columns and "hadm_id" in diagnoses_df.columns:
            merge_keys.append("hadm_id")

        merged_df = pd.merge(patients_df, diagnoses_df, on=merge_keys, how="inner")

        if 'disposition' in patients_df.columns and disposition_filter:
            merged_df = merged_df[merged_df['disposition'].isin(disposition_filter)]

        merged_df.drop_duplicates(subset=["subject_id", "hadm_id", "icd_code"], inplace=True)

        return merged_df

    except Exception as e:
        st.error(f"Veri yükleme/filtreleme hatası: {e}")
        return pd.DataFrame()

# df_summary oluşturulduktan sonra filtre uygulama
df_summary = load_and_filter_data()
df_summary = apply_post_merge_filter(df_summary)

if not df_summary.empty:
    st.subheader("📋 Major Depresif Hasta Özeti")
    st.dataframe(df_summary, use_container_width=True)

    total_rows = len(df_summary)
    unique_patients = df_summary['subject_id'].nunique()
    st.write(f"Toplam sonuç sayısı: {total_rows:,} | Toplam hasta sayısı: {unique_patients:,}")

    selected_row = st.selectbox("Detayını görüntülemek istediğiniz hastayı seçin:", df_summary["subject_id"].unique())
    hasta_detay = df_summary[df_summary["subject_id"] == selected_row]

    with st.expander("📋 Hasta Profili Detayı"):
        if not hasta_detay.empty:
            genel_bilgiler = hasta_detay.iloc[0]
            st.markdown(f"""
            <div style='padding: 15px; background-color: #eef6ff; border-radius: 10px; margin-bottom: 20px;'>
                <h4>Hasta: {genel_bilgiler['subject_id']}</h4>
                <b>Yaş:</b> {genel_bilgiler.get('anchor_age', '-')} &nbsp;&nbsp;
                <b>Cinsiyet:</b> {genel_bilgiler.get('gender', '-')} &nbsp;&nbsp;
                <b>Irk:</b> {genel_bilgiler.get('race', '-')} &nbsp;&nbsp;
                <b>Medeni Durum:</b> {genel_bilgiler.get('marital_status', '-')}
            </div>
            """, unsafe_allow_html=True)

        try:
            labs_df = load_optional_data("data/depress_labs.csv")
            hasta_labs = labs_df[labs_df['subject_id'] == selected_row]
            if not hasta_labs.empty:
                st.markdown("### 🔬 Laboratuvar Sonuçları")
                st.dataframe(
                    hasta_labs[["charttime", "test_name", "valuenum", "valueuom", "flag"]]
                    .rename(columns={
                        "charttime": "Zaman", "test_name": "Test", "valuenum": "Sonuç",
                        "valueuom": "Birim", "flag": "Durum"
                    }),
                    use_container_width=True
                )
        except Exception as e:
            st.warning(f"Laboratuvar verisi gösterilemedi: {e}")

        hasta_meds = meds_df[meds_df['subject_id'] == selected_row] if 'subject_id' in meds_df.columns else pd.DataFrame()
        if not hasta_meds.empty:
            st.markdown("### 💊 Kullanılan İlaçlar")
            st.dataframe(hasta_meds, use_container_width=True)

        hasta_medrec = medrecon_df[medrecon_df['subject_id'] == selected_row] if 'subject_id' in medrecon_df.columns else pd.DataFrame()
        if not hasta_medrec.empty:
            st.markdown("### 🗂️ İlaç Geçmişi (Medication Reconciliation)")
            st.dataframe(hasta_medrec, use_container_width=True)

        hasta_pyxis = pyxis_df[pyxis_df['subject_id'] == selected_row] if 'subject_id' in pyxis_df.columns else pd.DataFrame()
        if not hasta_pyxis.empty:
            st.markdown("### 💉 Acil Serviste Verilen İlaçlar (Pyxis)")
            st.dataframe(
                hasta_pyxis[["charttime", "name"]]
                .rename(columns={
                    "charttime": "Zaman", "name": "İlaç"
                }),
                use_container_width=True
            )

        hasta_notes = notes_df[notes_df['subject_id'] == selected_row]

        note_search_query = st.text_input("🔍 Klinik Notlarda Ara", value="", placeholder="örneğin: chest pain, discharge plan...")
        if note_search_query:
            hasta_notes = hasta_notes[hasta_notes['text'].str.contains(note_search_query, case=False, na=False)]

        if not hasta_notes.empty:
            st.markdown("### 📝 Klinik Notlar")
            for _, note in hasta_notes.iterrows():
                formatted_note = highlight_keywords(note['text'])
                st.markdown(f"<div style='white-space: pre-wrap; font-family: monospace; background-color: #f4f4f4; padding: 10px; border-radius: 5px;'>\n<b>Zaman:</b> {note['charttime']}<br><b>Not Tipi:</b> {note['note_type']}<br><b>Yatış ID:</b> {note.get('hadm_id', '-')}</div>", unsafe_allow_html=True)
                st.markdown(f"<div style='white-space: pre-wrap; font-family: monospace; background-color: #fdfdfd; padding: 10px; border-radius: 5px;'>{formatted_note}</div>", unsafe_allow_html=True)
                st.markdown("---")
else:
    st.warning("Major Depresif tanısı almış hasta bulunamadı.")
