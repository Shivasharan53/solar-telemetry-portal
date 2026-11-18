import os
from datetime import datetime, timezone
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from pymongo import MongoClient

from app.demo_data import SAMPLE_INVERTERS, demo_telemetry

load_dotenv()
st.set_page_config(page_title="SOLARA | Solar Intelligence", page_icon="☀️", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: Manrope, sans-serif; }
.stApp { background: radial-gradient(circle at 88% 0%, #183b32 0, #091711 36%, #07110e 78%); color: #e9f4ee; }
section[data-testid="stSidebar"] { background: #0c1d17; border-right: 1px solid #244436; }
div[data-testid="stMetric"] { background: linear-gradient(135deg,#142b21,#102119); border: 1px solid #2b4a3a; padding: 17px; border-radius: 15px; }
h1,h2,h3 { color: #edf7f0; letter-spacing: -0.035em; }
.brand { color:#b9f36b; font-size:.76rem; font-weight:800; letter-spacing:.2em; }
.hero { padding:22px 25px; border:1px solid #315441; border-radius:18px; background:linear-gradient(110deg,rgba(34,76,55,.72),rgba(12,31,24,.72)); margin:12px 0 20px; }
.muted {color:#a8beb0;font-size:.9rem}
div[data-testid="stDataFrame"] {border:1px solid #294738;border-radius:12px;overflow:hidden}
</style>
""", unsafe_allow_html=True)

DB_NAME = os.getenv("DATABASE_NAME", "solar_farm_db")
MONGODB_URI = os.getenv("MONGODB_URI", "").strip()
USE_MONGODB = os.getenv("USE_MONGODB", "true").lower() == "true"

@st.cache_data(ttl=30)
def load_inverters():
    if MONGODB_URI and USE_MONGODB:
        try:
            with MongoClient(MONGODB_URI, serverSelectionTimeoutMS=4000) as client:
                client.admin.command("ping")
                records = list(client[DB_NAME].inverters.find({}, {"_id": 0}))
                if records:
                    return records, "MongoDB Atlas", True
        except Exception as exc:
            return SAMPLE_INVERTERS, f"Demo mode (MongoDB unavailable: {type(exc).__name__})", False
    return SAMPLE_INVERTERS, "Demo telemetry", False

@st.cache_data(ttl=30)
def load_telemetry():
    if MONGODB_URI and USE_MONGODB:
        try:
            with MongoClient(MONGODB_URI, serverSelectionTimeoutMS=4000) as client:
                records = list(client[DB_NAME].telemetry.find({}, {"_id": 0}).sort("timestamp", 1).limit(5000))
                if records:
                    return records
        except Exception:
            pass
    return demo_telemetry(hours=24)

docs, data_source, mongo_connected = load_inverters()
telemetry = load_telemetry()
rows = []
for item in docs:
    status, weather, firmware = item.get("status", {}), item.get("weather", {}), item.get("firmware", {})
    rows.append({
        "Inverter": item.get("inverter_id", "Unknown"),
        "Manufacturer": item.get("manufacturer", "Unknown"),
        "Site": item.get("site", "Unassigned"),
        "State": status.get("state", "unknown"),
        "Power (kW)": float(status.get("power_kw", 0) or 0),
        "Temperature (°C)": float(status.get("temperature_c", 0) or 0),
        "Firmware": firmware.get("version", "—"),
        "Weather": weather.get("condition", "—"),
        "Irradiance (W/m²)": weather.get("irradiance_w_m2", 0),
        "Errors": len(item.get("error_logs", [])),
    })
df = pd.DataFrame(rows)

with st.sidebar:
    st.markdown('<div class="brand">☀ SOLARA / CONTROL ROOM</div>', unsafe_allow_html=True)
    st.markdown("### Fleet controls")
    st.caption(f"Source: {data_source}")
    site_options = ["All sites"] + sorted(df["Site"].dropna().unique().tolist())
    selected_site = st.selectbox("Solar site", site_options)
    state_options = ["All states", "online", "warning", "offline"]
    selected_state = st.selectbox("Inverter state", state_options)
    st.divider()
    st.caption("Demonstration values are simulated, not live plant readings.")
    if st.button("↻ Refresh telemetry", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

view = df.copy()
if selected_site != "All sites":
    view = view[view["Site"] == selected_site]
if selected_state != "All states":
    view = view[view["State"] == selected_state]

st.markdown('<div class="brand">RENEWABLE ENERGY / FLEET INTELLIGENCE</div>', unsafe_allow_html=True)
st.title("Solar operations overview")
st.markdown('<div class="hero"><h3 style="margin:0">See the whole farm. Understand every inverter.</h3><p class="muted">Unified operational visibility across multi-vendor solar assets, firmware and site conditions.</p></div>', unsafe_allow_html=True)

count = len(view)
online = int((view["State"] == "online").sum()) if count else 0
availability = online / count * 100 if count else 0
power = view["Power (kW)"].sum() if count else 0
attention = int(view["State"].isin(["warning", "offline"]).sum()) if count else 0
average_temp = view["Temperature (°C)"].mean() if count else 0

m1,m2,m3,m4,m5 = st.columns(5)
m1.metric("CURRENT OUTPUT", f"{power:,.1f} kW")
m2.metric("SNAPSHOT AVAILABILITY", f"{availability:.1f}%")
m3.metric("ONLINE UNITS", f"{online}/{count}")
m4.metric("AVG. TEMPERATURE", f"{average_temp:.1f} °C")
m5.metric("NEEDS ATTENTION", attention)

left, right = st.columns([1.35, 1])
with left:
    st.subheader("24-hour generation profile")
    telemetry_df = pd.DataFrame(telemetry)
    if not telemetry_df.empty:
        telemetry_df["timestamp"] = pd.to_datetime(telemetry_df["timestamp"], utc=True, errors="coerce")
        selected_inverter = st.selectbox("Telemetry series", ["Whole fleet"] + view["Inverter"].tolist())
        if selected_inverter != "Whole fleet":
            telemetry_df = telemetry_df[telemetry_df["inverter_id"] == selected_inverter]
        profile = telemetry_df.groupby("timestamp", as_index=False)["power_kw"].sum()
        fig = px.area(profile, x="timestamp", y="power_kw", color_discrete_sequence=["#b9f36b"])
        fig.update_traces(line_width=2, fillcolor="rgba(185,243,107,.15)")
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font_color="#e1eee6", margin=dict(l=5,r=5,t=15,b=5),
                          xaxis_title="", yaxis_title="Power (kW)")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No telemetry history found yet. Seed sample telemetry or connect an IoT source.")
with right:
    st.subheader("Manufacturer comparison")
    maker = view.groupby("Manufacturer", as_index=False).agg(
        units=("Inverter","count"),
        online=("State",lambda x:(x=="online").sum()),
        power=("Power (kW)","sum"))
    if not maker.empty:
        maker["Snapshot availability (%)"] = (maker["online"] / maker["units"] * 100).round(1)
        fig = px.bar(maker, x="Manufacturer", y="power", color="Manufacturer",
                     color_discrete_sequence=["#b9f36b","#61c8a4","#7e9ee8"],
                     hover_data=["units","Snapshot availability (%)"])
        fig.update_layout(showlegend=False,paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="rgba(0,0,0,0)",font_color="#e1eee6",
                          margin=dict(l=5,r=5,t=15,b=5),xaxis_title="",yaxis_title="Power (kW)")
        st.plotly_chart(fig,use_container_width=True)

st.subheader("Inverter fleet")
st.dataframe(view, use_container_width=True, hide_index=True)

st.subheader("Operational event watch")
event_rows = []
for item in docs:
    for event in item.get("error_logs", []):
        event_rows.append({
            "Inverter": item.get("inverter_id"),
            "Manufacturer": item.get("manufacturer"),
            "Site": item.get("site"),
            "Severity": event.get("severity", "warning"),
            "Code": event.get("code", "UNSPECIFIED"),
            "Event": event.get("message", "No description"),
        })
if event_rows:
    st.dataframe(pd.DataFrame(event_rows), use_container_width=True, hide_index=True)
else:
    st.success("No active events reported by the selected dataset.")

st.caption("SOLARA FIELD INTELLIGENCE  •  Prototype environment  •  Snapshot availability is not historical uptime.")
