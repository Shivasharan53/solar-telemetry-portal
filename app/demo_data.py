from datetime import datetime, timedelta, timezone
import math

SAMPLE_INVERTERS = [
    {"inverter_id":"INV-001","manufacturer":"SolarEdge","site":"North Ridge","capacity_kw":120,"status":{"state":"online","power_kw":82.5,"temperature_c":41.2,"voltage_v":415.2},"firmware":{"version":"2.4.1","panel_model":"SE-550","channel":"stable"},"weather":{"condition":"Clear","irradiance_w_m2":820,"ambient_temperature_c":31.0},"vendor_metadata":{"mppt_channels":6,"grid_profile":"IN-2025"},"error_logs":[]},
    {"inverter_id":"INV-002","manufacturer":"SMA","site":"Lakeview","capacity_kw":100,"status":{"state":"online","power_kw":74.2,"temperature_c":39.8,"voltage_v":412.8},"firmware":{"version":"3.1.0","panel_model":"STP-500","channel":"stable"},"weather":{"condition":"Partly cloudy","irradiance_w_m2":610,"ambient_temperature_c":29.0},"vendor_metadata":{"string_inputs":12,"thermal_mode":"adaptive"},"error_logs":[]},
    {"inverter_id":"INV-003","manufacturer":"Growatt","site":"East Valley","capacity_kw":100,"status":{"state":"warning","power_kw":28.4,"temperature_c":56.1,"voltage_v":407.1},"firmware":{"version":"1.8.2","panel_model":"GW-450","channel":"stable"},"weather":{"condition":"Hazy","irradiance_w_m2":690,"ambient_temperature_c":33.0},"vendor_metadata":{"dc_bus_v":760,"diagnostic_code":"TEMP-02"},"error_logs":[{"code":"TEMP-02","message":"High inverter temperature","severity":"warning","recorded_at":"2026-11-18T10:20:00+00:00"}]},
    {"inverter_id":"INV-004","manufacturer":"SolarEdge","site":"North Ridge","capacity_kw":120,"status":{"state":"online","power_kw":91.7,"temperature_c":44.6,"voltage_v":416.4},"firmware":{"version":"2.4.1","panel_model":"SE-550","channel":"stable"},"weather":{"condition":"Clear","irradiance_w_m2":845,"ambient_temperature_c":31.0},"vendor_metadata":{"mppt_channels":6,"grid_profile":"IN-2025"},"error_logs":[]},
    {"inverter_id":"INV-005","manufacturer":"SMA","site":"Lakeview","capacity_kw":100,"status":{"state":"offline","power_kw":0.0,"temperature_c":32.8,"voltage_v":0.0},"firmware":{"version":"3.0.8","panel_model":"STP-500","channel":"stable"},"weather":{"condition":"Cloudy","irradiance_w_m2":280,"ambient_temperature_c":27.0},"vendor_metadata":{"string_inputs":12,"thermal_mode":"adaptive"},"error_logs":[{"code":"COMMS-01","message":"Telemetry heartbeat missing","severity":"critical","recorded_at":"2026-11-18T10:12:00+00:00"}]},
    {"inverter_id":"INV-006","manufacturer":"Growatt","site":"East Valley","capacity_kw":100,"status":{"state":"online","power_kw":68.9,"temperature_c":46.3,"voltage_v":411.5},"firmware":{"version":"1.8.2","panel_model":"GW-450","channel":"stable"},"weather":{"condition":"Clear","irradiance_w_m2":790,"ambient_temperature_c":32.0},"vendor_metadata":{"dc_bus_v":775,"diagnostic_code":"OK"},"error_logs":[]},
    {"inverter_id":"INV-007","manufacturer":"SolarEdge","site":"North Ridge","capacity_kw":120,"status":{"state":"online","power_kw":88.1,"temperature_c":42.4,"voltage_v":414.6},"firmware":{"version":"2.5.0","panel_model":"SE-550","channel":"stable"},"weather":{"condition":"Clear","irradiance_w_m2":860,"ambient_temperature_c":31.0},"vendor_metadata":{"mppt_channels":6,"grid_profile":"IN-2025"},"error_logs":[]},
    {"inverter_id":"INV-008","manufacturer":"SMA","site":"Lakeview","capacity_kw":100,"status":{"state":"warning","power_kw":43.2,"temperature_c":59.2,"voltage_v":409.2},"firmware":{"version":"3.1.0","panel_model":"STP-500","channel":"stable"},"weather":{"condition":"Partly cloudy","irradiance_w_m2":540,"ambient_temperature_c":29.0},"vendor_metadata":{"string_inputs":12,"thermal_mode":"adaptive"},"error_logs":[{"code":"TEMP-03","message":"Thermal threshold approaching","severity":"warning","recorded_at":"2026-11-18T10:18:00+00:00"}]},
    {"inverter_id":"INV-009","manufacturer":"Growatt","site":"East Valley","capacity_kw":100,"status":{"state":"online","power_kw":76.4,"temperature_c":43.7,"voltage_v":413.0},"firmware":{"version":"1.9.0","panel_model":"GW-450","channel":"stable"},"weather":{"condition":"Clear","irradiance_w_m2":810,"ambient_temperature_c":32.0},"vendor_metadata":{"dc_bus_v":790,"diagnostic_code":"OK"},"error_logs":[]}
]

def demo_telemetry(inverter_id=None, hours=24):
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    selected = [x for x in SAMPLE_INVERTERS if inverter_id is None or x["inverter_id"] == inverter_id]
    output = []
    for item in selected:
        base = item["status"]["power_kw"]
        for offset in range(hours - 1, -1, -1):
            stamp = now - timedelta(hours=offset)
            daylight = max(0.0, math.sin(math.pi * ((stamp.hour - 6) % 24) / 12))
            output.append({
                "inverter_id": item["inverter_id"],
                "timestamp": stamp,
                "power_kw": round(base * daylight * (0.94 + 0.06 * math.sin(offset)), 2),
                "temperature_c": round(item["status"]["temperature_c"] - 3 + 4 * daylight, 1),
                "voltage_v": item["status"]["voltage_v"],
                "irradiance_w_m2": int(item["weather"]["irradiance_w_m2"] * daylight)
            })
    return output
