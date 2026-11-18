import os
import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

st.set_page_config(
    page_title="SOLARA | Solar Intelligence",
    page_icon="☀️",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: Manrope, sans-serif;
}
.stApp {
    background: #071511;
    color: #e9f4ee;
}
section[data-testid="stSidebar"] {
    background: #0d211a;
}
div[data-testid="stMetric"] {
    background: #10271e;
    border: 1px solid #244637;
    padding: 18px;
    border-radius: 14px;
}
h1, h2, h3 {
    color: #e9f4ee;
}
</style>
""", unsafe_allow_html=True)

st.title("☀️ SOLARA")
st.caption("FIELD INTELLIGENCE / MULTI-INVERTER TELEMETRY")

# Read credentials from environment variables
uri = os.getenv("MONGODB_URI", "").strip()
db_name = os.getenv("DATABASE_NAME", "solar_farm_db")

st.sidebar.markdown("### CONTROL ROOM")
st.sidebar.caption("Solar generation monitoring")

demo = st.sidebar.toggle(
    "Demo preview",
    value=not bool(uri)
)

sample = [
    {
        "inverter_id": "INV-001",
        "manufacturer": "SolarEdge",
        "site": "Farm North",
        "status": {
            "state": "online",
            "power_kw": 82.5,
            "temperature_c": 41.2
        },
        "firmware": {"version": "v2.4.1"},
        "weather": {
            "condition": "sunny",
            "irradiance_w_m2": 820
        },
        "error_logs": []
    },
    {
        "inverter_id": "INV-002",
        "manufacturer": "SMA",
        "site": "Farm South",
        "status": {
            "state": "online",
            "power_kw": 74.2,
            "temperature_c": 39.8
        },
        "firmware": {"version": "v3.1.0"},
        "weather": {
            "condition": "cloudy",
            "irradiance_w_m2": 610
        },
        "error_logs": []
    },
    {
        "inverter_id": "INV-003",
        "manufacturer": "Growatt",
        "site": "Farm East",
        "status": {
            "state": "warning",
            "power_kw": 28.4,
            "temperature_c": 56.1
        },
        "firmware": {"version": "v1.8.2"},
        "weather": {
            "condition": "partly cloudy",
            "irradiance_w_m2": 690
        },
        "error_logs": [
            {
                "code": "TEMP-02",
                "message": "High inverter temperature"
            }
        ]
    }
]

docs = sample

if uri and not demo:
    try:
        client = MongoClient(
            uri,
            serverSelectionTimeoutMS=5000
        )
        client.admin.command("ping")
        docs = list(
            client[db_name]["inverters"].find(
                {},
                {"_id": 0}
            )
        )
        client.close()

    except Exception as e:
        st.error(f"MongoDB connection failed: {e}")
        st.stop()

elif not demo:
    st.warning("Add MONGODB_URI to Render environment variables.")
    st.stop()

if not docs:
    st.warning("No inverter records found.")
    st.stop()

df = pd.DataFrame([
    {
        "Inverter": d.get("inverter_id", "-"),
        "Manufacturer": d.get("manufacturer", "-"),
        "Site": d.get("site", "-"),
        "State": d.get("status", {}).get("state", "unknown"),
        "Power (kW)": d.get("status", {}).get("power_kw", 0),
        "Temperature (°C)": d.get("status", {}).get("temperature_c", 0),
        "Firmware": d.get("firmware", {}).get("version", "-"),
        "Weather": d.get("weather", {}).get("condition", "-"),
        "Irradiance": d.get("weather", {}).get("irradiance_w_m2", 0),
        "Errors": len(d.get("error_logs", []))
    }
    for d in docs
])

total_power = df["Power (kW)"].sum()
online = int((df["State"] == "online").sum())
uptime = online / len(df) * 100
alerts = int((df["State"] != "online").sum())

c1, c2, c3, c4 = st.columns(4)

c1.metric("LIVE GENERATION", f"{total_power:,.1f} kW")
c2.metric("FLEET UPTIME", f"{uptime:.1f}%")
c3.metric("ACTIVE INVERTERS", f"{online}/{len(df)}")
c4.metric("ATTENTION NEEDED", alerts)

left, right = st.columns([1.2, 1])

with left:
    st.subheader("Generation by manufacturer")

    chart = px.bar(
        df,
        x="Manufacturer",
        y="Power (kW)",
        color="Manufacturer",
        text_auto=".1f",
        template="plotly_dark"
    )

    chart.update_layout(
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    st.plotly_chart(chart, use_container_width=True)

with right:
    st.subheader("Fleet condition")

    states = (
        df["State"]
        .value_counts()
        .rename_axis("State")
        .reset_index(name="Units")
    )

    chart2 = px.pie(
        states,
        names="State",
        values="Units",
        hole=0.62,
        template="plotly_dark"
    )

    chart2.update_layout(
        paper_bgcolor="rgba(0,0,0,0)"
    )

    st.plotly_chart(chart2, use_container_width=True)

st.subheader("Inverter telemetry")

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True
)

st.subheader("Fault watch")

faults = [
    (
        d.get("inverter_id"),
        err.get("code"),
        err.get("message")
    )
    for d in docs
    for err in d.get("error_logs", [])
]

if faults:
    st.dataframe(
        pd.DataFrame(
            faults,
            columns=["Inverter", "Fault code", "Description"]
        ),
        use_container_width=True,
        hide_index=True
    )
else:
    st.success("No inverter faults reported.")

st.caption(
    "SOLARA FIELD INTELLIGENCE • Demonstration telemetry unless MongoDB is connected"
)
