"""
==============================================
 Food Safety Dashboard - พร้อม Upload ไฟล์
==============================================

วิธีรัน:
1. pip install streamlit pandas plotly openpyxl
2. streamlit run dashboard.py
   หรือ python -m streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import warnings
warnings.filterwarnings("ignore")

# ==========================================
# ตั้งค่าหน้าตา
# ==========================================
st.set_page_config(
    page_title="Food Safety Dashboard",
    page_icon="🦠",
    layout="wide",
)

st.title("🦠 Food Safety Dashboard")
st.markdown("---")

# ==========================================
# STEP 1: อัปโหลดไฟล์ (ทำได้ทุกครั้ง)
# ==========================================
st.subheader("📂 อัปโหลดไฟล์ข้อมูล")
st.caption("ลากไฟล์ CSV วางได้เลย หรือกดเพื่อเลือกไฟล์")

col_u1, col_u2, col_u3 = st.columns(3)
with col_u1:
    file_model = st.file_uploader(
        "📊 ไฟล์สรุปตัวอย่าง (Model)",
        type=["csv"],
        key="model",
        help="ไฟล์ชื่อ database_dashboard_Model..."
    )
with col_u2:
    file_fail = st.file_uploader(
        "❌ ไฟล์รายการไม่ผ่าน (อาหาร)",
        type=["csv"],
        key="fail",
        help="ไฟล์ชื่อ database_dashboard_รายการไม่ผ่าน..."
    )
with col_u3:
    file_swab = st.file_uploader(
        "🔬 ไฟล์ Swab",
        type=["csv"],
        key="swab",
        help="ไฟล์ชื่อ database_dashboard_Swab..."
    )

# ตรวจสอบว่าอัปโหลดครบหรือยัง
if not file_model or not file_fail or not file_swab:
    st.info("👆 กรุณาอัปโหลดไฟล์ CSV ทั้ง 3 ไฟล์ด้านบนเพื่อดู Dashboard")
    st.stop()

st.success("✅ อัปโหลดไฟล์ครบแล้ว! กำลังโหลดข้อมูล...")
st.markdown("---")

# ==========================================
# STEP 2: โหลดและแปลงข้อมูล
# ==========================================
@st.cache_data
def load_model(f):
    df_raw = pd.read_csv(f)
    plants = ["Plant 1 A", "Plant 1 B", "Plant 2", "Plant 3",
              "Plant 4", "Plant 5", "Plant BNG 1", "Plant BNG 2", "Raw material"]
    records = []
    current_date = None
    for _, row in df_raw.iterrows():
        if pd.notna(row["Date"]):
            current_date = row["Date"]
        label = row["Unnamed: 1"]
        if label in ["จำนวนตัวอย่าง", "ผ่าน", "ไม่ผ่าน"] and current_date is not None:
            r = {"วันที่": current_date, "ประเภท": label,
                 "รวม": row.get("รวม", 0), "ร้อยละ": row.get("ร้อยละ", 0)}
            for p in plants:
                r[p] = row.get(p, 0)
            records.append(r)
    df = pd.DataFrame(records)
    df["วันที่"] = pd.to_datetime(df["วันที่"], format="%d-%b-%y", errors="coerce")
    return df

@st.cache_data
def load_fail(f):
    df_raw = pd.read_csv(f, header=None)
    df_raw.columns = ["วันที่ตรวจ", "Plant", "รายการ", "ประเภท", "Lot", "วันที่ผลิต", "ผลที่ไม่ผ่าน"] + \
                     [f"_x{i}" for i in range(len(df_raw.columns) - 7)]
    df = df_raw[["วันที่ตรวจ", "Plant", "รายการ", "ประเภท", "Lot", "วันที่ผลิต", "ผลที่ไม่ผ่าน"]].copy()
    df = df[df["วันที่ตรวจ"] != "Analyzed Date"].dropna(subset=["วันที่ตรวจ"])
    df["วันที่ตรวจ"] = pd.to_datetime(df["วันที่ตรวจ"], dayfirst=True, errors="coerce")
    df["วันที่ผลิต"] = pd.to_datetime(df["วันที่ผลิต"], dayfirst=True, errors="coerce")
    return df

@st.cache_data
def load_swab(f):
    df = pd.read_csv(f)
    df.columns = ["Swab No.", "วันที่ตรวจ", "Plant", "จุด Swab", "Report Date", "ผล"]
    df = df.dropna(subset=["Swab No."])
    df["วันที่ตรวจ"]  = pd.to_datetime(df["วันที่ตรวจ"],  dayfirst=True, errors="coerce")
    df["Report Date"] = pd.to_datetime(df["Report Date"], dayfirst=True, errors="coerce")
    df = df[df["ผล"].notna()]
    return df

try:
    df_model = load_model(file_model)
    df_fail  = load_fail(file_fail)
    df_swab  = load_swab(file_swab)
except Exception as e:
    st.error(f"❌ เกิดข้อผิดพลาดในการอ่านไฟล์: {e}")
    st.stop()

# ==========================================
# STEP 3: เลือกช่วงวันที่ (Date Picker)
# ==========================================
st.subheader("📅 เลือกช่วงวันที่ที่ต้องการดูข้อมูล")

all_dates = df_model["วันที่"].dropna().sort_values()
min_date = all_dates.min().date() if not all_dates.empty else pd.Timestamp("2026-01-01").date()
max_date = all_dates.max().date() if not all_dates.empty else pd.Timestamp("2026-12-31").date()

col_d1, col_d2 = st.columns(2)
with col_d1:
    date_start = st.date_input("📅 วันที่เริ่มต้น", value=min_date, min_value=min_date, max_value=max_date)
with col_d2:
    date_end   = st.date_input("📅 วันที่สิ้นสุด",  value=max_date, min_value=min_date, max_value=max_date)

date_start = pd.Timestamp(date_start)
date_end   = pd.Timestamp(date_end)

# กรองข้อมูลตามช่วงวันที่
df_model_f = df_model[(df_model["วันที่"] >= date_start) & (df_model["วันที่"] <= date_end)]
df_fail_f  = df_fail[ (df_fail["วันที่ตรวจ"] >= date_start) & (df_fail["วันที่ตรวจ"] <= date_end)]
df_swab_f  = df_swab[ (df_swab["วันที่ตรวจ"] >= date_start) & (df_swab["วันที่ตรวจ"] <= date_end)]

st.markdown("---")

# ==========================================
# STEP 4: KPI Cards
# ==========================================
date_label = f"{date_start.strftime('%d/%m/%y')} – {date_end.strftime('%d/%m/%y')}"
st.subheader(f"📊 ภาพรวม {date_label}")

total  = df_model_f[df_model_f["ประเภท"] == "จำนวนตัวอย่าง"]["รวม"].sum()
passed = df_model_f[df_model_f["ประเภท"] == "ผ่าน"]["รวม"].sum()
failed = df_model_f[df_model_f["ประเภท"] == "ไม่ผ่าน"]["รวม"].sum()
swab_count = len(df_swab_f)

c1, c2, c3, c4 = st.columns(4)
c1.metric("🧪 ตัวอย่างทั้งหมด",           f"{int(total):,}")
c2.metric("✅ ผ่านเกณฑ์",                 f"{int(passed):,}")
c3.metric("❌ ไม่ผ่านเกณฑ์",              f"{int(failed):,}")
c4.metric("🔬 Swab ที่ติดเชื้อ Listeria",  f"{swab_count}")

st.markdown("---")

# ==========================================
# STEP 5: กราฟรายวัน
# ==========================================
st.subheader("📅 จำนวนตัวอย่างอาหาร รายวัน (ผ่าน / ไม่ผ่าน)")

df_chart = df_model_f[df_model_f["ประเภท"].isin(["ผ่าน", "ไม่ผ่าน"])].copy()
df_chart["วันที่_str"] = df_chart["วันที่"].dt.strftime("%d/%m/%y")

if df_chart.empty:
    st.info("ไม่มีข้อมูลในช่วงวันที่นี้")
else:
    fig = px.bar(
        df_chart, x="วันที่_str", y="รวม", color="ประเภท", barmode="group",
        color_discrete_map={"ผ่าน": "#2ecc71", "ไม่ผ่าน": "#e74c3c"},
        labels={"วันที่_str": "วันที่", "รวม": "จำนวนตัวอย่าง"},
    )
    fig.update_layout(legend_title_text="ผลตรวจ")
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# ==========================================
# STEP 6: ตารางรายการไม่ผ่าน
# ==========================================
st.subheader("❌ รายการตัวอย่างอาหารที่ไม่ผ่านเกณฑ์")

if df_fail_f.empty:
    st.info("ไม่มีข้อมูลตัวอย่างที่ไม่ผ่านในช่วงวันที่นี้")
else:
    disp = df_fail_f.copy()
    disp["วันที่ตรวจ"] = disp["วันที่ตรวจ"].dt.strftime("%d/%m/%Y")
    disp["วันที่ผลิต"] = disp["วันที่ผลิต"].dt.strftime("%d/%m/%Y").fillna("-")
    disp = disp.rename(columns={
        "Plant": "โรงงาน", "รายการ": "ชื่อรายการ",
        "ประเภท": "ประเภทสินค้า", "Lot": "Batch/Lot", "ผลที่ไม่ผ่าน": "ผลที่ไม่ผ่าน"
    })

    plants_f = ["ทั้งหมด"] + sorted(disp["โรงงาน"].dropna().unique().tolist())
    sel = st.selectbox("🔎 กรองตามโรงงาน:", plants_f, key="fail_p")
    if sel != "ทั้งหมด":
        disp = disp[disp["โรงงาน"] == sel]

    st.dataframe(
        disp[["วันที่ตรวจ","โรงงาน","ชื่อรายการ","ประเภทสินค้า","Batch/Lot","วันที่ผลิต","ผลที่ไม่ผ่าน"]],
        use_container_width=True, hide_index=True
    )
    st.caption(f"พบ {len(disp)} รายการที่ไม่ผ่านในช่วงเวลานี้")

st.markdown("---")

# ==========================================
# STEP 7: Swab Listeria
# ==========================================
st.subheader("🔬 ตัวอย่าง Swab ที่ตรวจพบ Listeria")

if df_swab_f.empty:
    st.info("ไม่มีข้อมูล Swab ที่ติดเชื้อในช่วงวันที่นี้")
else:
    ca, cb = st.columns(2)

    with ca:
        st.markdown("**แยกตามโรงงาน**")
        g1 = df_swab_f.groupby("Plant").size().reset_index(name="จำนวน")
        fig1 = px.bar(g1, x="Plant", y="จำนวน", color="Plant", text="จำนวน",
                      color_discrete_sequence=px.colors.qualitative.Set2,
                      labels={"Plant": "โรงงาน"})
        fig1.update_traces(textposition="outside")
        fig1.update_layout(showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)

    with cb:
        st.markdown("**แยกตามวันที่ตรวจ**")
        g2 = df_swab_f.copy()
        g2["วันที่_str"] = g2["วันที่ตรวจ"].dt.strftime("%d/%m/%y")
        g2 = g2.groupby("วันที่_str").size().reset_index(name="จำนวน")
        fig2 = px.bar(g2, x="วันที่_str", y="จำนวน", text="จำนวน",
                      color_discrete_sequence=["#e74c3c"],
                      labels={"วันที่_str": "วันที่ตรวจ"})
        fig2.update_traces(textposition="outside")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("**แยกตามโรงงาน + วันที่ตรวจ**")
    g3 = df_swab_f.copy()
    g3["วันที่_str"] = g3["วันที่ตรวจ"].dt.strftime("%d/%m/%y")
    g3 = g3.groupby(["วันที่_str","Plant"]).size().reset_index(name="จำนวน")
    fig3 = px.bar(g3, x="วันที่_str", y="จำนวน", color="Plant", barmode="group",
                  text="จำนวน", labels={"วันที่_str": "วันที่ตรวจ", "Plant": "โรงงาน"})
    fig3.update_traces(textposition="outside")
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("**รายละเอียด Swab**")
    plants_s = ["ทั้งหมด"] + sorted(df_swab_f["Plant"].dropna().unique().tolist())
    sel_s = st.selectbox("🔎 กรองตามโรงงาน (Swab):", plants_s, key="swab_p")

    disp_s = df_swab_f.copy()
    if sel_s != "ทั้งหมด":
        disp_s = disp_s[disp_s["Plant"] == sel_s]

    disp_s["วันที่ตรวจ"]  = disp_s["วันที่ตรวจ"].dt.strftime("%d/%m/%Y")
    disp_s["Report Date"] = disp_s["Report Date"].dt.strftime("%d/%m/%Y")
    disp_s = disp_s.rename(columns={
        "Swab No.": "เลข Swab", "Plant": "โรงงาน",
        "จุด Swab": "จุดที่ Swab", "Report Date": "วันที่รายงานผล", "ผล": "ผลที่ตรวจพบ"
    })
    st.dataframe(
        disp_s[["เลข Swab","วันที่ตรวจ","โรงงาน","จุดที่ Swab","วันที่รายงานผล","ผลที่ตรวจพบ"]],
        use_container_width=True, hide_index=True
    )
    st.caption(f"พบ {len(disp_s)} จุด Swab ที่ตรวจพบ Listeria")

st.markdown("---")
st.caption("📁 Food Safety Dashboard | อัปโหลดไฟล์ใหม่ได้ทุกครั้งที่ด้านบนหน้า")
