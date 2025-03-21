import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
from dotenv import load_dotenv
import os
from functools import lru_cache

# .env dosyasından veritabanı bilgilerini yükle
load_dotenv()
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "mimic"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "password"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432")
}

def get_data(query):
    """ PostgreSQL'den veri çekme fonksiyonu """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"SQL Hatası: {e}")
        return pd.DataFrame()

@lru_cache(maxsize=128)
def get_cached_data(query):
    return get_data(query)

st.set_page_config(layout="wide")  # Sayfa genişliğini geniş hale getir

st.title("📊 MIMIC-IV Veri Görüntüleyici")

# Sayfalama (Pagination) seçenekleri
st.sidebar.header("🔍 Filtre Seçenekleri ve Sayfalama")
page_size = st.sidebar.slider("Sayfa Boyutu", min_value=10, max_value=100, value=25, step=5)
if 'page_number' not in st.session_state:
    st.session_state['page_number'] = 1
page_number = st.session_state['page_number']
offset = (page_number - 1) * page_size

# Kullanıcıya sıralama seçenekleri sunma
sort_options = {
    "Yaş": "mimiciv_hosp.patients.anchor_age::INTEGER",
    "Cinsiyet": "mimiciv_hosp.patients.gender",
    "Kabul Türü": "mimiciv_hosp.admissions.admission_type",
    "ICD Kodu": "mimiciv_hosp.diagnoses_icd.icd_code"
}
sort_by = st.sidebar.selectbox("Sıralama Ölçütü Seçin", list(sort_options.keys()))
sort_column = sort_options[sort_by]
sort_order = st.sidebar.radio("Sıralama Düzeni", ["Artan", "Azalan"])
sort_order_sql = "ASC" if sort_order == "Artan" else "DESC"

# Filtreleme seçenekleri
gender_filter = st.sidebar.selectbox("Cinsiyet Seçiniz", ["All"] + get_cached_data("SELECT DISTINCT gender FROM mimiciv_hosp.patients")['gender'].tolist())
gender_query = "" if gender_filter == "All" else f"AND mimiciv_hosp.patients.gender = '{gender_filter}'"

# Yaş aralığı filtresi
default_min_age, default_max_age = get_cached_data("SELECT MIN(anchor_age), MAX(anchor_age) FROM mimiciv_hosp.patients").iloc[0]
min_age, max_age = st.sidebar.slider("Yaş Aralığı Seçin", int(default_min_age), int(default_max_age), (int(default_min_age), int(default_max_age)))
age_query = f"AND patients.anchor_age::INTEGER BETWEEN {min_age} AND {max_age}"

icd_code_options = get_cached_data("SELECT DISTINCT icd_code FROM mimiciv_hosp.diagnoses_icd")['icd_code'].tolist()
icd_code_filter = st.sidebar.multiselect("ICD Koduyla Filtrele", icd_code_options)
icd_name_options = get_cached_data("SELECT DISTINCT long_title FROM mimiciv_hosp.d_icd_diagnoses")['long_title'].tolist()
icd_name_filter = st.sidebar.multiselect("Hastalık İsmiyle Filtrele", icd_name_options)

icd_filter_conditions = []
if icd_code_filter:
    icd_filter_conditions.append(f"diagnoses_icd.icd_code IN ({','.join([f'\'{code}\'' for code in icd_code_filter])})")
if icd_name_filter:
    icd_filter_conditions.append(f"d_icd_diagnoses.long_title IN ({','.join([f'\'{name}\'' for name in icd_name_filter])})")
icd_filter_query = " AND ".join(icd_filter_conditions)
icd_filter_query = f"AND {icd_filter_query}" if icd_filter_query else ""

# Ekstra filtreleme
admission_types = get_cached_data("SELECT DISTINCT admission_type FROM mimiciv_hosp.admissions")['admission_type'].tolist()
admission_type_filter = st.sidebar.multiselect("Kabul Türü Seçin", admission_types)
admission_type_query = f"AND admissions.admission_type IN ({','.join([f'\'{t}\'' for t in admission_type_filter])})" if admission_type_filter else ""

total_count_query = f"""
    SELECT COUNT(*) FROM mimiciv_hosp.patients
    LEFT JOIN mimiciv_hosp.admissions ON patients.subject_id = admissions.subject_id
    LEFT JOIN mimiciv_icu.icustays ON admissions.hadm_id = icustays.hadm_id
    LEFT JOIN mimiciv_hosp.diagnoses_icd ON admissions.hadm_id = diagnoses_icd.hadm_id
    LEFT JOIN mimiciv_hosp.d_icd_diagnoses ON diagnoses_icd.icd_code = d_icd_diagnoses.icd_code
    WHERE patients.anchor_age::INTEGER IS NOT NULL 
    {gender_query} 
    {age_query} 
    {icd_filter_query}
    {admission_type_query}
"""
total_count_df = get_data(total_count_query)
total_records = total_count_df.iloc[0, 0] if not total_count_df.empty else 0

query = f"""
    SELECT 
        row_number() OVER (ORDER BY {sort_column} {sort_order_sql}) AS row_num,
        patients.subject_id,
        admissions.hadm_id,
        patients.gender,
        patients.anchor_age::INTEGER,
        admissions.race,
        admissions.marital_status,
        patients.dod AS date_of_death,
        icustays.first_careunit AS first_care_unit,
        icustays.last_careunit AS last_care_unit,
        admissions.admission_type,
        admissions.admission_location,
        admissions.discharge_location,
        diagnoses_icd.icd_code,
        d_icd_diagnoses.long_title
    FROM mimiciv_hosp.patients
    LEFT JOIN mimiciv_hosp.admissions ON patients.subject_id = admissions.subject_id AND admissions.admission_type IS NOT NULL
    LEFT JOIN mimiciv_icu.icustays ON admissions.hadm_id = icustays.hadm_id
    LEFT JOIN mimiciv_hosp.diagnoses_icd ON admissions.hadm_id = diagnoses_icd.hadm_id AND diagnoses_icd.icd_code IS NOT NULL
    LEFT JOIN mimiciv_hosp.d_icd_diagnoses ON diagnoses_icd.icd_code = d_icd_diagnoses.icd_code AND d_icd_diagnoses.long_title IS NOT NULL
    WHERE patients.anchor_age::INTEGER IS NOT NULL 
    {gender_query} 
    {age_query} 
    {icd_filter_query}
    {admission_type_query}
    LIMIT {page_size} OFFSET {offset};
"""

df = get_data(query)

st.write(f"### İlk {page_size} kayıt (Sayfa {page_number} / Toplam {total_records})")
st.dataframe(df, height=600)  # Tablo yüksekliği artırıldı

# Sayfanın altına sayfalama ekleme
col1, col2, col3 = st.columns([1, 4, 1])
with col2:
    if st.button("⬅️ Önceki Sayfa") and page_number > 1:
        st.session_state['page_number'] -= 1
        page_number -= 1
    st.write(f"**Sayfa {page_number}**")
    if st.button("Sonraki Sayfa ➡️"):
        st.session_state['page_number'] += 1
        page_number += 1
