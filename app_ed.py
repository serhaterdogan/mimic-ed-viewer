import streamlit as st
import pandas as pd
import os
import plotly.express as px

# CSV veri yükleme fonksiyonu
def get_data_csv(path):
    try:
        return pd.read_csv(path)
    except Exception as e:
        st.error(f"CSV yükleme hatası: {e}")
        return pd.DataFrame()

st.set_page_config(page_title="ED Dashboard", layout="wide")
st.title("🏥 Acil Servis (ED) Verileri")

# Sekmeler
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📟 Hasta Özeti",
    "📊 En Sık Tanılar",
    "🪥 Triyaj Verileri",
    "⏱ Kalış Süresi",
    "🧠 Şikayet-Tanı"
])

# 🔍 Filtreler
st.sidebar.header("🔍 Filtreler")
icd_filter = st.sidebar.text_input("ICD Kodu ile Filtrele", key="icd_filter")
gender_filter = st.sidebar.selectbox("Cinsiyet Seçin", ("All", "M", "F"), key="gender_filter")
age_min, age_max = st.sidebar.slider("Yaş Aralığı", 0, 120, (18, 20), key="age_slider")

# 🔍 Nöropsikiyatrik Hasta Bilgileri Tablosu
with tab1:
    st.subheader("📟 Nöropsikiyatrik Hasta Özeti")
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

# 📊 En Sık Tanılar
with tab2:
    st.subheader("📊 En Sık Görülen Tanılar")
    df = get_data_csv("data/top_diagnoses.csv")
    st.dataframe(df, use_container_width=True)

# ⏱ LOS (Length of Stay)
df_los = get_data_csv("data/los.csv")
with tab4:
    st.subheader("⏱ ED Kalış Süresi (LOS) Dağılımı")
    if not df_los.empty:
        st.bar_chart(df_los['los_hours'])
        st.write(f"Ortalama Kalış Sürezi: {df_los['los_hours'].mean():.2f} saat")
    else:
        st.info("Veri bulunamadı veya yeterli değil.")

# 📈 Zaman Trendleri
df_trend = get_data_csv("data/trend.csv")
st.subheader("📊 Zamana Göre Başvuru Trendleri")
if not df_trend.empty:
    fig = px.line(df_trend, x="visit_day", y="visits", title="Günlük ED Başvuru Sayısı")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Zaman trend verisi bulunamadı.")

# 🪥 Triyaj Verileri
df_triage = get_data_csv("data/triage.csv")
with tab3:
    st.subheader("🪥 Triyaj Bulguları")
    if not df_triage.empty:
        st.write("Ortalama Değerler:")
        st.write(df_triage.mean(numeric_only=True))
        st.write("📈 Dağılım Grafikleri:")
        numeric_cols = df_triage.select_dtypes(include='number').columns
        st.line_chart(df_triage[numeric_cols])
    else:
        st.info("Triyaj verisi bulunamadı.")

# 👤 Demografi ve Taburcu Bilgileri
st.subheader("📊 Yaş, Cinsiyet, Giriş Tipi ve Taburcu Durumu Analizi")
df_demo = get_data_csv("data/demo.csv")
if not df_demo.empty:
    st.write("👥 Cinsiyet Dağılımı:")
    st.bar_chart(df_demo['gender'].value_counts())

    st.write("🎂 Yaş Dağılımı:")
    st.histogram_chart = px.histogram(df_demo, x="anchor_age", nbins=30, title="Yaş Dağılımı")
    st.plotly_chart(st.histogram_chart, use_container_width=True)

    st.write("🚪 Giriş Tipi:")
    st.dataframe(df_demo['admission_type'].value_counts().rename_axis('Giriş Tipi').reset_index(name='Hasta Sayısı'))

    st.write("🌞 Taburcu Lokasyonu:")
    st.dataframe(df_demo['discharge_location'].value_counts().rename_axis('Taburcu Yeri').reset_index(name='Hasta Sayısı'))
else:
    st.info("Demografik ve taburcu bilgileri için yeterli veri bulunamadı.")

# 🧠 Şikayet - Tanı Eşleşmesi
with tab5:
    st.subheader("🧠 Şikayet - Tanı Eşleşmesi")
    df_complaint_diag = get_data_csv("data/complaint_diag.csv")
    if not df_complaint_diag.empty:
        st.dataframe(df_complaint_diag, use_container_width=True)
    else:
        st.info("Şikayet ve tanı eşleşmesi için yeterli veri bulunamadı.")
