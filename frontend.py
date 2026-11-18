import os
import json
import requests
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

raw_api_url = os.getenv("API_BASE_URL", "http://localhost:8000").strip().rstrip("/")
if raw_api_url and not raw_api_url.startswith("http"):
    raw_api_url = f"https://{raw_api_url}"
API_BASE_URL = raw_api_url

st.set_page_config(
    page_title="Smart Solar Farm 3D Telemetry Portal",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- CUSTOM 3D HOLOGRAPHIC & GLASSMORPHISM CSS ---
st.markdown(
    """
    <style>
    .stApp {
        background: radial-gradient(circle at 20% 20%, #0f1b2e 0%, #070b14 60%, #04070d 100%);
        color: #e2e8f0;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    section[data-testid="stSidebar"] {
        background: rgba(11, 18, 32, 0.85);
        backdrop-filter: blur(14px);
        border-right: 1px solid rgba(56, 189, 248, 0.2);
    }
    .holo-header {
        background: linear-gradient(135deg, rgba(15, 28, 48, 0.85), rgba(10, 17, 30, 0.9));
        border: 1px solid rgba(56, 189, 248, 0.35);
        box-shadow: 0 0 25px rgba(56, 189, 248, 0.15), inset 0 0 15px rgba(245, 158, 11, 0.08);
        border-radius: 14px;
        padding: 18px 26px;
        margin-bottom: 22px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .holo-title {
        font-size: 1.7rem;
        font-weight: 800;
        letter-spacing: 1.5px;
        background: linear-gradient(90deg, #38bdf8, #fbbf24);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    .holo-sub {
        color: #94a3b8;
        font-size: 0.85rem;
        letter-spacing: 0.8px;
        margin-top: 4px;
    }
    .kpi-card {
        background: linear-gradient(145deg, rgba(18, 30, 52, 0.85), rgba(9, 15, 28, 0.95));
        border: 1px solid rgba(56, 189, 248, 0.3);
        border-top: 2px solid #38bdf8;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 12px 24px rgba(0, 0, 0, 0.55), 0 0 15px rgba(56, 189, 248, 0.12);
        transition: transform 0.25s ease, box-shadow 0.25s ease;
        text-align: center;
    }
    .kpi-card:hover {
        transform: translateY(-5px) scale(1.01);
        box-shadow: 0 16px 30px rgba(0, 0, 0, 0.7), 0 0 22px rgba(245, 158, 11, 0.3);
        border-top-color: #fbbf24;
    }
    .kpi-card-amber {
        border-color: rgba(245, 158, 11, 0.45);
        border-top: 2px solid #fbbf24;
        box-shadow: 0 12px 24px rgba(0, 0, 0, 0.55), 0 0 20px rgba(245, 158, 11, 0.18);
    }
    .kpi-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1.4px;
        color: #94a3b8;
        margin-bottom: 6px;
    }
    .kpi-value {
        font-size: 2.0rem;
        font-weight: 800;
        color: #f8fafc;
        text-shadow: 0 0 12px rgba(56, 189, 248, 0.5);
    }
    .kpi-value-amber {
        color: #fbbf24;
        text-shadow: 0 0 14px rgba(245, 158, 11, 0.6);
    }
    .glass-panel {
        background: rgba(13, 22, 38, 0.78);
        border: 1px solid rgba(56, 189, 248, 0.22);
        border-radius: 12px;
        padding: 14px 18px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        margin-bottom: 16px;
    }
    .panel-header {
        font-size: 0.9rem;
        font-weight: 700;
        letter-spacing: 1.1px;
        text-transform: uppercase;
        color: #38bdf8;
        border-bottom: 1px solid rgba(56, 189, 248, 0.2);
        padding-bottom: 8px;
        margin-bottom: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- HEADER BANNER ---
st.markdown(
    """
    <div class="holo-header">
        <div>
            <div class="holo-title">☀️ SMART SOLAR FARM — 3D TELEMETRY COMMAND PORTAL</div>
            <div class="holo-sub">POLYMORPHIC BSON INGESTION • MONGODB AGGREGATION PIPELINES • DIGITAL TWIN</div>
        </div>
        <div style="text-align:right;">
            <span style="background:rgba(16,185,129,0.18); border:1px solid #10b981; color:#34d399; padding:5px 12px; border-radius:20px; font-size:0.78rem; font-weight:700;">
                ● MOTOR ASYNC STREAM LIVE
            </span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- SIDEBAR CONTROLS ---
with st.sidebar:
    st.markdown("### ⚡ GRID OPERATIONS")
    if st.button("🌱 Seed 60 Multi-Vendor BSON Logs", use_container_width=True):
        try:
            res = requests.post(f"{API_BASE_URL}/api/v1/seed?count=60", timeout=25)
            res.raise_for_status()
            st.success(f"Injected {res.json()['seeded_records']} BSON documents!")
            st.rerun()
        except Exception as e:
            st.error(f"Backend error: {e}")

    st.divider()
    st.markdown("### 📡 PUSH LIVE INVERTER PAYLOAD")
    with st.form("ingest_form"):
        inv_id = st.text_input("Inverter ID", value="INV-SMA-109")
        vendor = st.selectbox("Manufacturer", ["SMA Solar", "Sungrow", "Huawei FusionSolar", "Enphase"])
        zone = st.selectbox("Plant Zone", ["North-Array-A", "South-Array-B", "East-Tracker-C"])
        status = st.selectbox("Status", ["ONLINE", "DEGRADED", "FAULT"])
        kw = st.number_input("Power Output (kW)", min_value=0.0, max_value=150.0, value=44.8)
        custom_json = st.text_area(
            "Vendor-Specific Nested BSON",
            value='{"error_code": 0, "heatsink_temp_c": 42.1, "string_voltage_v": 710}',
        )
        submitted = st.form_submit_button("Transmit BSON Packet", use_container_width=True)
        if submitted:
            try:
                diag_dict = json.loads(custom_json)
                payload = {
                    "inverter_id": inv_id,
                    "manufacturer": vendor,
                    "plant_zone": zone,
                    "status": status,
                    "power_output_kw": kw,
                    "firmware_meta": {"fw_version": "v4.5-3D", "protocol": "Modbus-TCP"},
                    "vendor_diagnostics": diag_dict,
                    "weather_context": {"irradiance_wm2": 920, "ambient_temp_c": 31.4},
                }
                r = requests.post(f"{API_BASE_URL}/api/v1/telemetry", json=payload, timeout=15)
                r.raise_for_status()
                st.success("BSON Telemetry Stored!")
                st.rerun()
            except Exception as e:
                st.error(f"Ingestion failed: {e}")

# --- FETCH AGGREGATED DATA ---
try:
    agg_res = requests.get(f"{API_BASE_URL}/api/v1/analytics/uptime-by-manufacturer", timeout=20)
    agg_res.raise_for_status()
    uptime_data = agg_res.json()
except Exception as e:
    st.warning(f"Connecting to FastAPI Backend (`{API_BASE_URL}`). If on Render free tier, wait ~30s for wake-up and refresh. Error: {e}")
    st.stop()

if not uptime_data:
    st.info("Database is empty. Click **🌱 Seed 60 Multi-Vendor BSON Logs** in the left sidebar to initialize the 3D portal.")
    st.stop()

df_uptime = pd.DataFrame(uptime_data)

# --- TOP 3D HOLOGRAPHIC KPI CARDS ---
avg_uptime = df_uptime["uptime_percentage"].mean()
total_inverters = int(df_uptime["inverter_count"].sum())
total_gen_kw = round((df_uptime["avg_power_kw"] * df_uptime["inverter_count"]).sum(), 1)
fault_count = int(df_uptime["fault_pings"].sum())

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(
        f'<div class="kpi-card"><div class="kpi-label">Fleet Avg Uptime</div><div class="kpi-value">{avg_uptime:.2f}%</div></div>',
        unsafe_allow_html=True,
    )
with k2:
    st.markdown(
        f'<div class="kpi-card"><div class="kpi-label">Active Inverters</div><div class="kpi-value">{total_inverters:,}</div></div>',
        unsafe_allow_html=True,
    )
with k3:
    st.markdown(
        f'<div class="kpi-card kpi-card-amber"><div class="kpi-label">Total Generation</div><div class="kpi-value kpi-value-amber">{total_gen_kw} kW</div></div>',
        unsafe_allow_html=True,
    )
with k4:
    st.markdown(
        f'<div class="kpi-card"><div class="kpi-label">Fault Alerts Logged</div><div class="kpi-value" style="color:#f87171; text-shadow:0 0 12px rgba(248,113,113,0.6);">{fault_count}</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# --- MIDDLE ROW: BAR CHARTS ---
c1, c2 = st.columns(2)

with c1:
    st.markdown('<div class="glass-panel"><div class="panel-header">📊 Uptime Percentage by Manufacturer</div>', unsafe_allow_html=True)
    fig_up = go.Figure()
    colors = ["#fbbf24", "#38bdf8", "#818cf8", "#34d399"]
    for idx, row in df_uptime.iterrows():
        col = colors[idx % len(colors)]
        fig_up.add_trace(
            go.Bar(
                x=[row["manufacturer"]],
                y=[row["uptime_percentage"]],
                name=row["manufacturer"],
                text=[f"{row['uptime_percentage']}%"],
                textposition="outside",
                marker=dict(color=col, line=dict(color="#ffffff", width=1.2), opacity=0.9),
            )
        )
    fig_up.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.4)",
        font=dict(color="#e2e8f0"),
        yaxis=dict(range=[0, 112], gridcolor="rgba(56,189,248,0.15)", title="Uptime (%)"),
        xaxis=dict(title=""),
        showlegend=False,
        height=310,
        margin=dict(l=20, r=20, t=20, b=20),
    )
    st.plotly_chart(fig_up, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown('<div class="glass-panel"><div class="panel-header">⚡ Power Output (kW) & Ping Volume by Vendor</div>', unsafe_allow_html=True)
    fig_kw = go.Figure()
    fig_kw.add_trace(
        go.Bar(
            x=df_uptime["manufacturer"],
            y=df_uptime["avg_power_kw"],
            name="Avg Power (kW)",
            text=df_uptime["avg_power_kw"].apply(lambda v: f"{v} kW"),
            textposition="outside",
            marker=dict(color="#fbbf24", line=dict(color="#fef3c7", width=1)),
        )
    )
    fig_kw.add_trace(
        go.Bar(
            x=df_uptime["manufacturer"],
            y=df_uptime["total_pings"],
            name="Telemetry Pings",
            text=df_uptime["total_pings"],
            textposition="outside",
            marker=dict(color="#38bdf8", line=dict(color="#e0f2fe", width=1)),
        )
    )
    fig_kw.update_layout(
        barmode="group",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15,23,42,0.4)",
        font=dict(color="#e2e8f0"),
        yaxis=dict(gridcolor="rgba(56,189,248,0.15)"),
        legend=dict(orientation="h", y=1.12, x=0.5, xanchor="center"),
        height=310,
        margin=dict(l=20, r=20, t=30, b=20),
    )
    st.plotly_chart(fig_kw, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# --- BOTTOM ROW: DATA MATRIX TABLE + BSON STREAM INSPECTOR ---
b1, b2 = st.columns([1.15, 1])

with b1:
    st.markdown('<div class="glass-panel"><div class="panel-header">📋 Data Matrix Table (MongoDB Aggregation Output)</div>', unsafe_allow_html=True)
    st.dataframe(df_uptime, use_container_width=True, hide_index=True, height=290)
    st.markdown("</div>", unsafe_allow_html=True)

with b2:
    st.markdown('<div class="glass-panel"><div class="panel-header">🧬 BSON Live Stream Inspector (Polymorphic Schemas)</div>', unsafe_allow_html=True)
    selected_vendor = st.selectbox(
        "Filter by Manufacturer",
        ["All"] + df_uptime["manufacturer"].tolist(),
        label_visibility="collapsed",
    )
    recent_res = requests.get(
        f"{API_BASE_URL}/api/v1/telemetry/recent",
        params={"manufacturer": selected_vendor, "limit": 10},
        timeout=15,
    )
    recent_logs = recent_res.json()
    for log in recent_logs[:3]:
        badge = "🟢" if log["status"] == "ONLINE" else ("🟡" if log["status"] == "DEGRADED" else "🔴")
        with st.expander(f"{badge} {log['inverter_id']} | {log['manufacturer']} | {log['power_output_kw']} kW"):
            st.json(log)
    st.markdown("</div>", unsafe_allow_html=True)

# --- 3D INTERACTIVE SOLAR FARM ARRAY DIGITAL TWIN ---
st.markdown('<div class="glass-panel"><div class="panel-header">🛰️ 3D Solar Farm Array & Central Inverter Hub Digital Twin (Drag to Rotate)</div>', unsafe_allow_html=True)

fig_3d = go.Figure()
fig_3d.add_trace(
    go.Scatter3d(
        x=[0],
        y=[0],
        z=[0.8],
        mode="markers+text",
        text=["CENTRAL BSON INVERTER HUB"],
        textposition="top center",
        textfont=dict(color="#fbbf24", size=11),
        marker=dict(size=14, color="#fbbf24", symbol="diamond", line=dict(color="#ffffff", width=2)),
        name="Central Hub",
    )
)

sectors = [
    ("SMA Solar", -4, 4, "#38bdf8"),
    ("Sungrow", 4, 4, "#fbbf24"),
    ("Huawei FusionSolar", -4, -4, "#34d399"),
    ("Enphase", 4, -4, "#a78bfa"),
]

for vendor_name, cx, cy, color in sectors:
    px_list, py_list, pz_list = [], [], []
    for dx in np.linspace(-1.5, 1.5, 4):
        for dy in np.linspace(-1.5, 1.5, 4):
            px, py, pz = cx + dx, cy + dy, 0.2
            px_list.append(px)
            py_list.append(py)
            pz_list.append(pz)
            fig_3d.add_trace(
                go.Scatter3d(
                    x=[px, 0],
                    y=[py, 0],
                    z=[pz, 0.6],
                    mode="lines",
                    line=dict(color="rgba(251, 191, 36, 0.25)", width=2),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )
    fig_3d.add_trace(
        go.Scatter3d(
            x=px_list,
            y=py_list,
            z=pz_list,
            mode="markers",
            marker=dict(size=7, color=color, symbol="square", opacity=0.9),
            name=f"{vendor_name} Array",
        )
    )

fig_3d.update_layout(
    paper_bgcolor="rgba(0,0,0,0)",
    scene=dict(
        xaxis=dict(showgrid=True, gridcolor="rgba(56,189,248,0.15)", showbackground=False, title="East-West (m)"),
        yaxis=dict(showgrid=True, gridcolor="rgba(56,189,248,0.15)", showbackground=False, title="North-South (m)"),
        zaxis=dict(range=[0, 2.5], showgrid=False, showbackground=False, title="Telemetry Elevation"),
        camera=dict(eye=dict(x=1.5, y=-1.6, z=1.1)),
    ),
    font=dict(color="#e2e8f0"),
    legend=dict(orientation="h", y=1.02, x=0.5, xanchor="center"),
    height=420,
    margin=dict(l=0, r=0, t=10, b=0),
)
st.plotly_chart(fig_3d, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)
