import streamlit as st
import pandas as pd
import os

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

        # ICD filtrelemesi
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
                st.warning("Filtreleme için uygun tanı sütunu bulunamadı.")

        if chiefcomplaint_filter and "chiefcomplaint" in patients_df.columns:
            patients_df = patients_df[patients_df["chiefcomplaint"].astype(str).str.contains(chiefcomplaint_filter, case=False, na=False)]

        merged_df = pd.merge(patients_df, diagnoses_df, on=["subject_id"], how="inner")
        if 'disposition' in patients_df.columns and disposition_filter:
            patients_df = patients_df[patients_df['disposition'].isin(disposition_filter)]

        return merged_df

    except Exception as e:
        st.error(f"Veri yükleme/filtreleme hatası: {e}")
        return pd.DataFrame()

# Veriyi al
st.subheader("Nöropsikiyatrik Hasta Özeti")
df_summary = load_and_filter_data()

if not df_summary.empty:
    selected_columns = [
        "intime",
        "subject_id", "hadm_id", "stay_id", "gender", "anchor_age",
        "marital_status", "race", "admission_type", "admission_location", "discharge_location",
        "chiefcomplaint",
        "icd_code", "icd_title", "long_title"
    ]
    df_summary = df_summary[[col for col in selected_columns if col in df_summary.columns]]

    pretty_columns = {
        "intime": "Başvuru Zamanı",
        "subject_id": "Hasta ID",
        "hadm_id": "Yatış ID",
        "stay_id": "Klinik Kalış ID",
        "gender": "Cinsiyet",
        "anchor_age": "Yaş",
        "marital_status": "Medeni Durum",
        "race": "Irk",
        "admission_type": "Yatış Türü",
        "admission_location": "Başvuru Yeri",
        "discharge_location": "Taburcu Yeri",
        "chiefcomplaint": "Hasta Şikayeti",
        "icd_code": "ICD Kodu",
        "icd_title": "ICD Başlığı",
        "long_title": "Tanı Açıklaması"
    }
    df_summary.rename(columns=pretty_columns, inplace=True)

    total_rows = len(df_summary)
    unique_patients = df_summary['Hasta ID'].nunique()

    st.write(f"Toplam sonuç sayısı: {total_rows:,} | Toplam hasta sayısı: {unique_patients:,}")

    page_size = 100
    page_number = st.number_input("Sayfa numarası", min_value=1, max_value=(total_rows - 1) // page_size + 1, value=1, step=1)
    start_index = (page_number - 1) * page_size
    end_index = start_index + page_size
    selected_row = st.selectbox("Detayını görüntülemek istediğiniz hastayı seçin:", df_summary["Hasta ID"].unique())
    hasta_detay = df_summary[df_summary["Hasta ID"] == selected_row]

    with st.expander("📋 Hasta Profili Detayı"):
        if not hasta_detay.empty:
            genel_bilgiler = hasta_detay.iloc[0]
            st.markdown(f"""
            <div style='padding: 15px; background-color: #eef6ff; border-radius: 10px; margin-bottom: 20px;'>
                <h4>Hasta: {genel_bilgiler['Hasta ID']}</h4>
                <b>Yaş:</b> {genel_bilgiler.get('Yaş', '-')} &nbsp;&nbsp; 
                <b>Cinsiyet:</b> {genel_bilgiler.get('Cinsiyet', '-')} &nbsp;&nbsp;
                <b>Irk:</b> {genel_bilgiler.get('Irk', '-')} &nbsp;&nbsp;
                <b>Medeni Durum:</b> {genel_bilgiler.get('Medeni Durum', '-')}
            </div>
            """, unsafe_allow_html=True)

            for _, row in hasta_detay.iterrows():
                st.markdown(f"""
                <div style='padding: 10px; background-color: #f9f9f9; border-radius: 10px; margin-bottom: 10px;'>
                    <h5>Yatış ID: {row.get('Yatış ID', '-')} | Klinik Kalış ID: {row.get('Klinik Kalış ID', '-')}</h5>
                    <ul>
                        <li><b>Yatış Türü:</b> {row.get('Yatış Türü', '-')}</li>
                        <li><b>Başvuru Yeri:</b> {row.get('Başvuru Yeri', '-')}</li>
                        <li><b>Taburcu Yeri:</b> {row.get('Taburcu Yeri', '-')}</li>
                        <li><b>Hasta Şikayeti:</b> {row.get('Hasta Şikayeti', '-')}</li>
                        <li><b>Tanı:</b> {row.get('Tanı Açıklaması', '-')} ({row.get('ICD Kodu', '-')})</li>
                    </ul>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.write("Hasta bilgisi bulunamadı.")
        st.markdown("---")

    st.dataframe(df_summary.iloc[start_index:end_index], use_container_width=True)

    # 📥 CSV olarak indirme özelliği
    csv_download = df_summary.to_csv(index=False).encode('utf-8')
    st.download_button(
"📥 Filtrelenmiş Veriyi İndir", data=csv_download, file_name="filtrelenmis_hasta_verisi.csv", mime="text/csv")
else:
    st.warning("Filtrelere uygun veri bulunamadı.")
