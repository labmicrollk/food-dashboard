"""
==============================================
 Food Safety Dashboard - Streamlit App
 ช่วงวันที่: 25/04/2569 - 01/05/2569
==============================================

วิธีรัน:
1. ติดตั้ง library ที่ต้องการ (ทำครั้งเดียว):
   pip install streamlit pandas plotly openpyxl

2. วางไฟล์ CSV ทั้ง 3 ไฟล์ ในโฟลเดอร์เดียวกับไฟล์นี้

3. รันด้วยคำสั่ง:
   streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import StringIO
import warnings
warnings.filterwarnings("ignore")

# ==========================================
# ตั้งค่าหน้าตา Dashboard
# ==========================================
st.set_page_config(
    page_title="Food Safety Dashboard",
    page_icon="🦠",
    layout="wide",
)

st.title("🦠 Food Safety Dashboard")
st.caption("ข้อมูลช่วงวันที่ 25 เม.ย. 2569 – 01 พ.ค. 2569")
st.markdown("---")

# ==========================================
# STEP 1: โหลดข้อมูล 3 ไฟล์
# ==========================================

# --- ชื่อไฟล์ (แก้ตรงนี้ถ้าชื่อไฟล์ต่างออกไป) ---
FILE_MODEL   = "database_dashboard_Model25-1_5__.csv"
FILE_FAIL    = "database_dashboard_รายการไม_ผ_าน_อาหาร__.csv"
FILE_SWAB    = "database_dashboard_Swab_25-010569_.csv"

@st.cache_data
def load_data():
    # ---- ไฟล์ 1: สรุปจำนวนตัวอย่างรายวัน ----
    df_model_raw = pd.read_csv(FILE_MODEL)
    plants = ["Plant 1 A", "Plant 1 B", "Plant 2", "Plant 3",
              "Plant 4", "Plant 5", "Plant BNG 1", "Plant BNG 2", "Raw material"]
    
    records = []
    current_date = None
    for _, row in df_model_raw.iterrows():
        if pd.notna(row["Date"]):
            current_date = row["Date"]
        label = row["Unnamed: 1"]
        if label in ["จำนวนตัวอย่าง", "ผ่าน", "ไม่ผ่าน"] and current_date is not None:
            r = {"วันที่": current_date, "ประเภท": label, "รวม": row.get("รวม", 0), "ร้อยละ": row.get("ร้อยละ", 0)}
            for p in plants:
                r[p] = row.get(p, 0)
            records.append(r)
    df_model = pd.DataFrame(records)
    df_model["วันที่"] = pd.to_datetime(df_model["วันที่"], format="%d-%b-%y", errors="coerce")

    # ---- ไฟล์ 2: รายการไม่ผ่าน (อาหาร) ----
    df_fail_raw = pd.read_csv(FILE_FAIL, header=None)
    df_fail_raw.columns = ["วันที่ตรวจ", "Plant", "รายการ", "ประเภท", "Lot", "วันที่ผลิต", "ผลที่ไม่ผ่าน"] + \
                          [f"_extra{i}" for i in range(len(df_fail_raw.columns) - 7)]
    df_fail = df_fail_raw[["วันที่ตรวจ", "Plant", "รายการ", "ประเภท", "Lot", "วันที่ผลิต", "ผลที่ไม่ผ่าน"]].copy()
    # ตัดแถวหัว
    df_fail = df_fail[df_fail["วันที่ตรวจ"] != "Analyzed Date"].dropna(subset=["วันที่ตรวจ"])
    # แปลงวันที่ (รองรับหลายรูปแบบ)
    df_fail["วันที่ตรวจ"] = pd.to_datetime(df_fail["วันที่ตรวจ"], dayfirst=True, errors="coerce")
    df_fail["วันที่ผลิต"] = pd.to_datetime(df_fail["วันที่ผลิต"], dayfirst=True, errors="coerce")

    # ---- ไฟล์ 3: Swab ----
    df_swab = pd.read_csv(FILE_SWAB)
    df_swab.columns = ["Swab No.", "วันที่ตรวจ", "Plant", "จุด Swab", "Report Date", "ผล"]
    df_swab = df_swab.dropna(subset=["Swab No."])
    df_swab["วันที่ตรวจ"] = pd.to_datetime(df_swab["วันที่ตรวจ"], dayfirst=True, errors="coerce")
    df_swab["Report Date"] = pd.to_datetime(df_swab["Report Date"], dayfirst=True, errors="coerce")
    # กรองเฉพาะที่มีผล Listeria
    df_swab = df_swab[df_swab["ผล"].notna()]

    return df_model, df_fail, df_swab

try:
    df_model, df_fail, df_swab = load_data()
except FileNotFoundError as e:
    st.error(f"❌ ไม่พบไฟล์: {e}\n\nกรุณาวางไฟล์ CSV ทั้ง 3 ไฟล์ในโฟลเดอร์เดียวกับ dashboard.py")
    st.stop()

# ==========================================
# STEP 2: กรองวันที่ 25/04/2569 - 01/05/2569
# ==========================================
date_start = pd.Timestamp("2026-04-25")
date_end   = pd.Timestamp("2026-05-01")

df_model_f = df_model[
    (df_model["วันที่"] >= date_start) & (df_model["วันที่"] <= date_end)
]
df_fail_f = df_fail[
    (df_fail["วันที่ตรวจ"] >= date_start) & (df_fail["วันที่ตรวจ"] <= date_end)
]
df_swab_f = df_swab[
    (df_swab["วันที่ตรวจ"] >= date_start) & (df_swab["วันที่ตรวจ"] <= date_end)
]

# ==========================================
# STEP 3: KPI Cards บนสุด
# ==========================================
st.subheader("📊 ภาพรวมช่วงวันที่ 25 เม.ย. – 01 พ.ค. 2569")

df_total  = df_model_f[df_model_f["ประเภท"] == "จำนวนตัวอย่าง"]["รวม"].sum()
df_pass   = df_model_f[df_model_f["ประเภท"] == "ผ่าน"]["รวม"].sum()
df_nopass = df_model_f[df_model_f["ประเภท"] == "ไม่ผ่าน"]["รวม"].sum()
swab_total = len(df_swab_f)

col1, col2, col3, col4 = st.columns(4)
col1.metric("🧪 ตัวอย่างอาหารทั้งหมด", f"{int(df_total):,}")
col2.metric("✅ ผ่านเกณฑ์", f"{int(df_pass):,}")
col3.metric("❌ ไม่ผ่านเกณฑ์", f"{int(df_nopass):,}")
col4.metric("🔬 Swab ที่ติดเชื้อ Listeria", f"{swab_total}")

st.markdown("---")

# ==========================================
# STEP 4: กราฟสรุปรายวัน (ผ่าน/ไม่ผ่าน)
# ==========================================
st.subheader("📅 จำนวนตัวอย่างอาหาร รายวัน (ผ่าน / ไม่ผ่าน)")

df_chart = df_model_f[df_model_f["ประเภท"].isin(["ผ่าน", "ไม่ผ่าน"])].copy()
df_chart["วันที่_str"] = df_chart["วันที่"].dt.strftime("%d/%m/%y")

fig_daily = px.bar(
    df_chart,
    x="วันที่_str",
    y="รวม",
    color="ประเภท",
    barmode="group",
    color_discrete_map={"ผ่าน": "#2ecc71", "ไม่ผ่าน": "#e74c3c"},
    labels={"วันที่_str": "วันที่", "รวม": "จำนวนตัวอย่าง"},
    title="จำนวนตัวอย่างอาหาร แยกตามวันที่"
)
fig_daily.update_layout(xaxis_tickangle=0, legend_title_text="ผลตรวจ")
st.plotly_chart(fig_daily, use_container_width=True)

st.markdown("---")

# ==========================================
# STEP 5: ตารางรายการไม่ผ่าน (อาหาร)
# ==========================================
st.subheader("❌ รายการตัวอย่างอาหารที่ไม่ผ่านเกณฑ์")

if df_fail_f.empty:
    st.info("ไม่มีข้อมูลตัวอย่างที่ไม่ผ่านในช่วงวันที่นี้")
else:
    # จัดรูปแบบวันที่
    display_fail = df_fail_f.copy()
    display_fail["วันที่ตรวจ"] = display_fail["วันที่ตรวจ"].dt.strftime("%d/%m/%Y")
    display_fail["วันที่ผลิต"] = display_fail["วันที่ผลิต"].dt.strftime("%d/%m/%Y").fillna("-")
    display_fail = display_fail.rename(columns={
        "วันที่ตรวจ": "วันที่ตรวจ",
        "Plant": "โรงงาน",
        "รายการ": "ชื่อรายการ",
        "ประเภท": "ประเภทสินค้า",
        "Lot": "Batch/Lot",
        "วันที่ผลิต": "วันที่ผลิต",
        "ผลที่ไม่ผ่าน": "ผลที่ไม่ผ่าน"
    })
    
    # กล่องกรอง (filter) โรงงาน
    plants_fail = ["ทั้งหมด"] + sorted(display_fail["โรงงาน"].dropna().unique().tolist())
    sel_plant_fail = st.selectbox("🔎 กรองตามโรงงาน (รายการไม่ผ่าน):", plants_fail, key="fail_plant")
    if sel_plant_fail != "ทั้งหมด":
        display_fail = display_fail[display_fail["โรงงาน"] == sel_plant_fail]
    
    st.dataframe(
        display_fail[["วันที่ตรวจ", "โรงงาน", "ชื่อรายการ", "ประเภทสินค้า", "Batch/Lot", "วันที่ผลิต", "ผลที่ไม่ผ่าน"]],
        use_container_width=True, hide_index=True
    )
    st.caption(f"พบ {len(display_fail)} รายการที่ไม่ผ่านในช่วงเวลานี้")

st.markdown("---")

# ==========================================
# STEP 6: Swab - ตารางละเอียด + กราฟ
# ==========================================
st.subheader("🔬 ตัวอย่าง Swab ที่ตรวจพบ Listeria")

if df_swab_f.empty:
    st.info("ไม่มีข้อมูล Swab ที่ติดเชื้อในช่วงวันที่นี้")
else:
    # ---- กราฟ: จำนวนแยกตามโรงงาน ----
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.markdown("**จำนวน Swab ติดเชื้อ แยกตามโรงงาน**")
        swab_by_plant = df_swab_f.groupby("Plant").size().reset_index(name="จำนวน")
        fig_plant = px.bar(
            swab_by_plant,
            x="Plant", y="จำนวน",
            color="Plant",
            text="จำนวน",
            color_discrete_sequence=px.colors.qualitative.Set2,
            labels={"Plant": "โรงงาน", "จำนวน": "จำนวน Swab ติดเชื้อ"}
        )
        fig_plant.update_traces(textposition="outside")
        fig_plant.update_layout(showlegend=False)
        st.plotly_chart(fig_plant, use_container_width=True)

    with col_b:
        st.markdown("**จำนวน Swab ติดเชื้อ แยกตามวันที่ตรวจ**")
        swab_by_date = df_swab_f.copy()
        swab_by_date["วันที่_str"] = swab_by_date["วันที่ตรวจ"].dt.strftime("%d/%m/%y")
        swab_by_date2 = swab_by_date.groupby("วันที่_str").size().reset_index(name="จำนวน")
        fig_date = px.bar(
            swab_by_date2,
            x="วันที่_str", y="จำนวน",
            color_discrete_sequence=["#e74c3c"],
            text="จำนวน",
            labels={"วันที่_str": "วันที่ตรวจ", "จำนวน": "จำนวน Swab ติดเชื้อ"}
        )
        fig_date.update_traces(textposition="outside")
        st.plotly_chart(fig_date, use_container_width=True)

    # ---- กราฟ: จำนวนแยกตามโรงงาน + วันที่ ----
    st.markdown("**จำนวน Swab ติดเชื้อ แยกตามโรงงาน และวันที่ตรวจ**")
    swab_cross = df_swab_f.copy()
    swab_cross["วันที่_str"] = swab_cross["วันที่ตรวจ"].dt.strftime("%d/%m/%y")
    swab_cross2 = swab_cross.groupby(["วันที่_str", "Plant"]).size().reset_index(name="จำนวน")
    fig_cross = px.bar(
        swab_cross2,
        x="วันที่_str", y="จำนวน",
        color="Plant",
        barmode="group",
        text="จำนวน",
        labels={"วันที่_str": "วันที่ตรวจ", "จำนวน": "จำนวน Swab", "Plant": "โรงงาน"},
    )
    fig_cross.update_traces(textposition="outside")
    st.plotly_chart(fig_cross, use_container_width=True)

    # ---- ตารางละเอียด Swab ----
    st.markdown("**รายละเอียด Swab ที่ตรวจพบ Listeria**")
    
    plants_swab = ["ทั้งหมด"] + sorted(df_swab_f["Plant"].dropna().unique().tolist())
    sel_plant_swab = st.selectbox("🔎 กรองตามโรงงาน (Swab):", plants_swab, key="swab_plant")
    
    display_swab = df_swab_f.copy()
    if sel_plant_swab != "ทั้งหมด":
        display_swab = display_swab[display_swab["Plant"] == sel_plant_swab]
    
    display_swab["วันที่ตรวจ"] = display_swab["วันที่ตรวจ"].dt.strftime("%d/%m/%Y")
    display_swab["Report Date"] = display_swab["Report Date"].dt.strftime("%d/%m/%Y")
    display_swab = display_swab.rename(columns={
        "Swab No.": "เลข Swab",
        "วันที่ตรวจ": "วันที่ตรวจ",
        "Plant": "โรงงาน",
        "จุด Swab": "จุดที่ Swab",
        "Report Date": "วันที่รายงานผล",
        "ผล": "ผลที่ตรวจพบ"
    })
    
    st.dataframe(
        display_swab[["เลข Swab", "วันที่ตรวจ", "โรงงาน", "จุดที่ Swab", "วันที่รายงานผล", "ผลที่ตรวจพบ"]],
        use_container_width=True, hide_index=True
    )
    st.caption(f"พบ {len(display_swab)} จุด Swab ที่ตรวจพบ Listeria ในช่วงเวลานี้")

st.markdown("---")
st.caption("📁 ข้อมูลจาก: Model25-1_5 | รายการไม่ผ่านอาหาร | Swab 25-010569")