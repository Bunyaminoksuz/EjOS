from fastapi import FastAPI
import psutil
import subprocess
import re

app = FastAPI()

def temps_from_psutil():
    try:
        temps = psutil.sensors_temperatures()
        if not temps:
            return None
        cpu = None
        sys = None

        # yaygın anahtarlar
        if "coretemp" in temps and temps["coretemp"]:
            cpu = temps["coretemp"][0].current
        elif "k10temp" in temps and temps["k10temp"]:
            cpu = temps["k10temp"][0].current
        elif "cpu_thermal" in temps and temps["cpu_thermal"]:
            cpu = temps["cpu_thermal"][0].current

        if "acpitz" in temps and temps["acpitz"]:
            sys = temps["acpitz"][0].current

        if cpu is None and sys is not None:
            cpu = sys
        if sys is None and cpu is not None:
            sys = cpu

        if cpu is None and sys is None:
            return None
        return {"cpu": cpu or 0, "sys": sys or 0}
    except Exception:
        return None

def temps_from_sensors_cmd():
    # sensors çıktısından ilk anlamlı sıcaklığı çekmeye çalışır
    try:
        r = subprocess.run(["sensors"], capture_output=True, text=True, timeout=2)
        out = r.stdout or ""
        # ör: "+45.0°C" veya "+45.0 C"
        m = re.findall(r"([+-]?\d+(?:\.\d+)?)\s*°?C", out)
        if not m:
            return None
        # en baştaki değeri CPU kabul edip sys'e de aynı veriyoruz (istersen daha sonra refine ederiz)
        t = float(m[0])
        return {"cpu": t, "sys": t}
    except Exception:
        return None

def get_temps():
    t = temps_from_psutil()
    if t is not None:
        return t
    t = temps_from_sensors_cmd()
    if t is not None:
        return t
    return {"cpu": 0, "sys": 0}

@app.get("/stats")
def stats():
    cpu_usage = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory()
    ram_used_gb = round(ram.used / (1024 ** 3), 1)
    ram_total_gb = round(ram.total / (1024 ** 3), 1)
    temps = get_temps()
    return {
        "cpu": cpu_usage,
        "ram_percent": ram.percent,
        "ram_text": f"{ram_used_gb} GB / {ram_total_gb} GB",
        "temp_cpu": temps["cpu"],
        "temp_sys": temps["sys"],
    }
