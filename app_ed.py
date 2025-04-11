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
    diag_full = pd.read_csv("data/neuro_psych_diagnoses.csv")
    icd_options = sorted(diag_full['long_title'].dropna().unique().tolist()) if 'long_title' in diag_full.columns else []
except:
    icd_options = []
chiefcomplaint_filter = st.sidebar.text_input("Hasta Şikayeti ile Filtrele", value="", key="cc_filter", label_visibility="visible")
icd_filter = st.sidebar.multiselect("Tanı Seçin (ICD Açıklaması)", icd_options, key="icd_filter_dropdown")
icd_code_filter = st.sidebar.text_input("ICD Kodu ile Arama", value="", key="icd_code_filter")
gender_filter = st.sidebar.selectbox("Cinsiyet Seçin", ("All", "M", "F"), key="gender_filter")
age_min, age_max = st.sidebar.slider("Yaş Aralığı", 18, 120, (18, 101), key="age_slider")
adm_type_filter = st.sidebar.selectbox("Yatış Türü", ["All"] + filter_options["admission_type"], key="adm_type")
adm_loc_filter = st.sidebar.selectbox("Başvuru Yeri", ["All"] + filter_options["admission_location"], key="adm_loc")
disch_loc_filter = st.sidebar.selectbox("Taburcu Yeri", ["All"] + filter_options["discharge_location"], key="disch_loc")

# Disposition filtrelemesi
try:
    edstays_df = pd.read_csv("data/neuro_psych_patients.csv")
    disposition_options = sorted(edstays_df['disposition'].dropna().unique().tolist()) if 'disposition' in edstays_df.columns else []
except:
    disposition_options = []
disposition_filter = st.sidebar.multiselect("Çıkış Durumu (Disposition)", disposition_options, default=disposition_options)

# Hasta ve tanı verilerini yükle
def load_and_filter_data():
    try:
        patients_df = pd.read_csv("data/neuro_psych_patients.csv")
        diagnoses_df = pd.read_csv("data/neuro_psych_diagnoses.csv")
        base_patients_df = pd.read_csv("data/patients.csv") if os.path.exists("data/patients.csv") else pd.DataFrame()
        admissions_df = pd.read_csv("data/admissions.csv") if os.path.exists("data/admissions.csv") else pd.DataFrame()
        triage_df = pd.read_csv("data/triage.csv") if os.path.exists("data/triage.csv") else pd.DataFrame()

        if not base_patients_df.empty:
            base_patients_df = base_patients_df[["subject_id", "anchor_age"]]
            patients_df = pd.merge(patients_df, base_patients_df, on="subject_id", how="left")

        if not admissions_df.empty:
            admissions_df = admissions_df[["subject_id", "hadm_id", "admission_type", "admission_location", "discharge_location"]]
            patients_df = pd.merge(patients_df, admissions_df, on=["subject_id", "hadm_id"], how="left")

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
            icd_cols = ['long_title']
            matched = False
            for col in icd_cols:
                if col in diagnoses_df.columns:
                    diagnoses_df = diagnoses_df[diagnoses_df[col].isin(icd_filter)]
                    matched = True
                    break
            if not matched:
                st.warning("Filtreleme için uygun tanı açıklaması sütunu bulunamadı.")

        if icd_code_filter:
            if "icd_code" in diagnoses_df.columns:
                diagnoses_df = diagnoses_df[diagnoses_df["icd_code"].astype(str).str.contains(icd_code_filter, case=False, na=False)]

        if chiefcomplaint_filter and "chiefcomplaint" in patients_df.columns:
            patients_df = patients_df[patients_df["chiefcomplaint"].astype(str).str.contains(chiefcomplaint_filter, case=False, na=False)]

        merged_df = pd.merge(patients_df, diagnoses_df, on=["subject_id"], how="inner")
        if 'disposition' in patients_df.columns and disposition_filter:
            merged_df = merged_df[merged_df['disposition'].isin(disposition_filter)]

        return merged_df

    except Exception as e:
        st.error(f"Veri yükleme/filtreleme hatası: {e}")
        return pd.DataFrame()

# Notları yükle (sadece nöropsikiyatrik hastalar için)
def load_notes():
    try:
        notes_df = pd.read_csv("data/neuro_psych_notes.csv")
        return notes_df
    except:
        return pd.DataFrame()

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

notes_df = load_notes()
df_summary = load_and_filter_data()

if not df_summary.empty:
    st.subheader("📋 Hasta Özeti")
    selected_columns = [
         "intime", "subject_id", "hadm_id", "stay_id", "gender", "anchor_age",
         "marital_status", "race", "admission_type", "admission_location", "discharge_location",
         "chiefcomplaint", "icd_code", "icd_title", "long_title"
     ]
    df_summary = df_summary[[col for col in selected_columns if col in df_summary.columns]]
    df_summary.rename(columns={
         "intime": "Başvuru Zamanı", "subject_id": "Hasta ID", "hadm_id": "Yatış ID",
         "stay_id": "Klinik Kalış ID", "gender": "Cinsiyet", "anchor_age": "Yaş",
         "marital_status": "Medeni Durum", "race": "Irk", "admission_type": "Yatış Türü",
         "admission_location": "Başvuru Yeri", "discharge_location": "Taburcu Yeri",
         "chiefcomplaint": "Hasta Şikayeti", "icd_code": "ICD Kodu",
         "icd_title": "ICD Başlığı", "long_title": "Tanı Açıklaması"
    }, inplace=True)
    st.dataframe(df_summary, use_container_width=True)

    total_rows = len(df_summary)
    unique_patients = df_summary['Hasta ID'].nunique()
  
    st.write(f"Toplam sonuç sayısı: {total_rows:,} | Toplam hasta sayısı: {unique_patients:,}")

    selected_row = st.selectbox("Detayını görüntülemek istediğiniz hastayı seçin:", df_summary["Hasta ID"].unique())
    hasta_detay = df_summary[df_summary["Hasta ID"] == selected_row]

    st.subheader("📊 En Sık Görülen Tanılar ve Şikayetler")
    col1, col2 = st.columns(2)

    with col1:
        if "long_title" in df_summary.columns:
            top_diagnoses = df_summary['long_title'].value_counts().head(10)
            st.markdown("**En Sık Tanılar**")
            fig, ax = plt.subplots()
            top_diagnoses.plot(kind='barh', ax=ax)
            ax.invert_yaxis()
            ax.set_xlabel("Hasta Sayısı")
            st.pyplot(fig)

    with col2:
        if "chiefcomplaint" in df_summary.columns:
            top_complaints = df_summary['chiefcomplaint'].value_counts().head(10)
            st.markdown("**En Sık Şikayetler**")
            fig, ax = plt.subplots()
            top_complaints.plot(kind='barh', ax=ax, color='orange')
            ax.invert_yaxis()
            ax.set_xlabel("Hasta Sayısı")
            st.pyplot(fig)

    selected_row = st.selectbox("Detayını görüntülemek istediğiniz hastayı seçin:", df_summary["Hasta ID"].unique())
    hasta_detay = df_summary[df_summary["Hasta ID"] == selected_row]

    with st.expander("📋 Hasta Profili Detayı"):
        if not hasta_detay.empty:
            try:
                genel_bilgiler = hasta_detay.iloc[0]
                st.markdown(f"""
                <div style='padding: 15px; background-color: #eef6ff; border-radius: 10px; margin-bottom: 20px;'>
                    <h4>Hasta: {genel_bilgiler['Hasta ID']}</h4>
                    <b>Yaş:</b> {genel_bilgiler.get('anchor_age', '-')} &nbsp;&nbsp;
                    <b>Cinsiyet:</b> {genel_bilgiler.get('gender', '-')} &nbsp;&nbsp;
                    <b>Irk:</b> {genel_bilgiler.get('race', '-')} &nbsp;&nbsp;
                    <b>Medeni Durum:</b> {genel_bilgiler.get('marital_status', '-')}
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.warning(f"Hasta detayı gösterilemedi: {e}")

        try:
            labs_df = pd.read_csv("data/neuro_psych_labs.csv")
            hasta_labs = labs_df[labs_df['subject_id'] == selected_row]
            if not hasta_labs.empty:
                st.markdown("### 🔬 Laboratuvar Sonuçları")
                st.dataframe(hasta_labs, use_container_width=True)
        except Exception as e:
            st.warning(f"Laboratuvar verisi gösterilemedi: {e}")

        hasta_notes = notes_df[notes_df['subject_id'] == selected_row]
        note_search_query = st.text_input("🔍 Klinik Notlarda Ara", value="", placeholder="örneğin: stroke, discharge...")
        if note_search_query:
            hasta_notes = hasta_notes[hasta_notes['text'].str.contains(note_search_query, case=False, na=False)]

        if not hasta_notes.empty:
            st.markdown("### 📝 Klinik Notlar")
            for _, note in hasta_notes.iterrows():
                try:
                    formatted_note = highlight_keywords(note['text'])
                    st.markdown(f"<div style='white-space: pre-wrap; font-family: monospace; background-color: #f4f4f4; padding: 10px; border-radius: 5px;'>\n<b>Zaman:</b> {note['charttime']}<br><b>Not Tipi:</b> {note['note_type']}<br><b>Yatış ID:</b> {note.get('hadm_id', '-')}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='white-space: pre-wrap; font-family: monospace; background-color: #fdfdfd; padding: 10px; border-radius: 5px;'>{formatted_note}</div>", unsafe_allow_html=True)
                    st.markdown("---")
                except Exception as e:
                    st.warning(f"Not gösterilemedi: {e}")
else:
    st.warning("Filtrelere uygun veri bulunamadı.")