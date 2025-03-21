import streamlit as st
import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv
import plotly.express as px

# Load environment variables
load_dotenv()
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "mimic"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "password"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432")
}

def get_data(query):
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"SQL Hatası: {e}")
        return pd.DataFrame()

st.set_page_config(page_title="ED Dashboard", layout="wide")
st.title("🏥 Acil Servis (ED) Verileri")

# Sekmeler
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🧾 Hasta Özeti",
    "📊 En Sık Tanılar",
    "🩺 Triyaj Verileri",
    "⏱ Kalış Süresi",
    "🧠 Şikayet-Tanı"
])

# Bilgi kartları veriler öncesine taşındı

# 🔍 Filtreler
st.sidebar.header("🔍 Filtreler")
icd_filter = st.sidebar.text_input("ICD Kodu ile Filtrele", key="icd_filter")
gender_filter = st.sidebar.selectbox("Cinsiyet Seçin", ("All", "M", "F"), key="gender_filter")
age_min, age_max = st.sidebar.slider("Yaş Aralığı", 0, 120, (18, 20), key="age_slider")

# 🔍 Genişletilmiş Hasta Bilgileri Tablosu
full_patient_query = f"""
    SELECT d.subject_id, e.hadm_id, p.gender, p.anchor_age AS age, e.race,
           a.marital_status, p.dod AS date_of_death,
           a.admission_type, a.admission_location, a.discharge_location,
           d.icd_code, dd.long_title AS diagnosis,
           e.arrival_transport, e.disposition,
           e.intime AS ed_intime, e.outtime AS ed_outtime,
           a.admittime AS hosp_admittime, a.dischtime AS hosp_dischtime
    FROM mimiciv_ed.diagnosis d
    JOIN mimiciv_ed.edstays e ON d.subject_id = e.subject_id AND d.stay_id = e.stay_id
    JOIN mimiciv_hosp.patients p ON d.subject_id::text = p.subject_id::text
    JOIN mimiciv_hosp.admissions a ON e.hadm_id = a.hadm_id
    LEFT JOIN mimiciv_hosp.d_icd_diagnoses dd ON d.icd_code = dd.icd_code
    WHERE p.anchor_age BETWEEN {age_min} AND {age_max}
    {f"AND p.gender = '{gender_filter}'" if gender_filter != 'All' else ""}
    {f"AND d.icd_code = '{icd_filter}'" if icd_filter else ""}
    
"""

with tab1:
    st.subheader("🧾 Hasta Özeti Tablosu")
df_summary = get_data(full_patient_query)
if not df_summary.empty:
    pretty_columns = {
        "subject_id": "Hasta ID",
        "hadm_id": "Yatış ID",
        "gender": "Cinsiyet",
        "age": "Yaş",
        "race": "Irk",
        "marital_status": "Medeni Durum",
        "date_of_death": "Ölüm Tarihi",
        "admission_type": "Geliş Tipi",
        "admission_location": "Kabul Lokasyonu",
        "discharge_location": "Çıkış Lokasyonu",
        "icd_code": "ICD Kodu",
        "diagnosis": "Tanı",
        "arrival_transport": "Transfer Yolu",
        "disposition": "Son Durum",
        "ed_intime": "ED Giriş Zamanı",
        "ed_outtime": "ED Çıkış Zamanı",
        "hosp_admittime": "Hastane Giriş",
        "hosp_dischtime": "Hastane Çıkış"
    }
    df_summary.rename(columns=pretty_columns, inplace=True)
    
    st.write(f"Toplam sonuç sayısı: {len(df_summary):,}")

    # Sayfalama
    page_size = 50
    page_number = st.number_input("Sayfa numarası", min_value=1, max_value=(len(df_summary) - 1) // page_size + 1, value=1, step=1)
    start_index = (page_number - 1) * page_size
    end_index = start_index + page_size
    st.dataframe(df_summary.iloc[start_index:end_index], use_container_width=True)
else:
    st.warning("Filtrelere uygun veri bulunamadı.")

with tab2:
    st.subheader("📊 En Sık Görülen Tanılar")
top_diagnoses_query = f"""
    SELECT d.icd_code, dd.long_title, COUNT(*) AS frequency
    FROM mimiciv_ed.diagnosis d
    LEFT JOIN mimiciv_hosp.d_icd_diagnoses dd ON d.icd_code = dd.icd_code
    JOIN mimiciv_hosp.patients p ON d.subject_id::text = p.subject_id::text
    WHERE p.anchor_age BETWEEN {age_min} AND {age_max}
    {f"AND p.gender = '{gender_filter}'" if gender_filter != 'All' else ""}
    {f"AND d.icd_code = '{icd_filter}'" if icd_filter else ""}
    GROUP BY d.icd_code, dd.long_title
    ORDER BY frequency DESC
    
"""
df = get_data(top_diagnoses_query)
st.dataframe(df, use_container_width=True)

# LOS Hesaplama ve Zaman Analizi
df_los = get_data("""
    SELECT subject_id, stay_id, intime, outtime,
           EXTRACT(EPOCH FROM (outtime - intime))/3600 AS los_hours
    FROM mimiciv_ed.edstays
    WHERE intime IS NOT NULL AND outtime IS NOT NULL
    ORDER BY intime DESC
    
""")

with tab4:
    st.subheader("⏱ ED Kalış Süresi (LOS) Dağılımı")
if not df_los.empty:
    st.bar_chart(df_los['los_hours'])
    st.write(f"Ortalama Kalış Sürezi: {df_los['los_hours'].mean():.2f} saat")
else:
    st.info("Veri bulunamadı veya yeterli değil.")

# Zaman Trend Analizi
df_trend = get_data("""
    SELECT DATE_TRUNC('day', intime) AS visit_day, COUNT(*) AS visits
    FROM mimiciv_ed.edstays
    WHERE intime IS NOT NULL
    GROUP BY visit_day
    ORDER BY visit_day;
""")

st.subheader("📊 Zamana Göre Başvuru Trendleri")
if not df_trend.empty:
    fig = px.line(df_trend, x="visit_day", y="visits", title="Günlük ED Başvuru Sayısı")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Zaman trend verisi bulunamadı.")

# Triyaj Verileri Analizi
df_triage = get_data("""
    SELECT temperature, heartrate, resprate, o2sat, sbp, dbp
    FROM mimiciv_ed.triage
    WHERE temperature IS NOT NULL
    LIMIT 1000;
""")

with tab3:
    st.subheader("🩺 Triyaj Bulguları")
if not df_triage.empty:
    st.write("Ortalama Değerler:")
    st.write(df_triage.mean(numeric_only=True))
    st.write("📈 Dağılım Grafikleri:")
    st.line_chart(df_triage)
else:
    st.info("Triyaj verisi bulunamadı.")

# Yaş / Cinsiyet / Giriş Tipi / Taburcu Durumu Analizi
st.subheader("📊 Yaş, Cinsiyet, Giriş Tipi ve Taburcu Durumu Analizi")
df_demo = get_data("""
    SELECT e.subject_id, p.gender, p.anchor_age, e.intime AS admittime, e.disposition AS discharge_location, e.arrival_transport AS admission_type
    FROM mimiciv_ed.edstays e
    JOIN mimiciv_hosp.patients p ON e.subject_id::text = p.subject_id::text
    WHERE p.anchor_age IS NOT NULL
    LIMIT 1000;
""")

if not df_demo.empty:
    st.write("👥 Cinsiyet Dağılımı:")
    st.bar_chart(df_demo['gender'].value_counts())

    st.write("🎂 Yaş Dağılımı:")
    st.histogram_chart = px.histogram(df_demo, x="anchor_age", nbins=30, title="Yaş Dağılımı")
    st.plotly_chart(st.histogram_chart, use_container_width=True)

    st.write("🚪 Giriş Tipi:")
    st.dataframe(df_demo['admission_type'].value_counts().rename_axis('Giriş Tipi').reset_index(name='Hasta Sayısı'))

    st.write("🏁 Taburcu Lokasyonu:")
    st.dataframe(df_demo['discharge_location'].value_counts().rename_axis('Taburcu Yeri').reset_index(name='Hasta Sayısı'))
else:
    st.info("Demografik ve taburcu bilgileri için yeterli veri bulunamadı.")

# Şikayet - Tanı Eşleşmesi
with tab5:
    st.subheader("🧠 Şikayet - Tanı Eşleşmesi")
df_complaint_diag = get_data("""
    SELECT t.chiefcomplaint, d.icd_code, dd.long_title, COUNT(*) AS vaka_sayisi
    FROM mimiciv_ed.triage t
    JOIN mimiciv_ed.diagnosis d ON t.subject_id = d.subject_id AND t.stay_id = d.stay_id
    LEFT JOIN mimiciv_hosp.d_icd_diagnoses dd ON d.icd_code = dd.icd_code
    WHERE t.chiefcomplaint IS NOT NULL
    GROUP BY t.chiefcomplaint, d.icd_code, dd.long_title
    ORDER BY vaka_sayisi DESC
    
""")

if not df_complaint_diag.empty:
    st.dataframe(df_complaint_diag, use_container_width=True)
else:
    st.info("Şikayet ve tanı eşleşmesi için yeterli veri bulunamadı.")
