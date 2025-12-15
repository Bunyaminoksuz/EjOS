### Setup yaptıktan Sonra Mutlaka chmod +x setup_lenovo_stats.sh yapınız!!!!
#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="$HOME/ejos-stats"
VENV_DIR="$BASE_DIR/venv"
APP_FILE="$BASE_DIR/lenovo_stats_server.py"

echo "[1/5] apt paketleri kuruluyor..."
sudo apt-get update
sudo apt-get install -y python3-venv python3-full lm-sensors

echo "[2/5] klasör hazırlanıyor: $BASE_DIR"
mkdir -p "$BASE_DIR"

echo "[3/5] venv oluşturuluyor..."
python3 -m venv "$VENV_DIR"

echo "[4/5] python paketleri kuruluyor (venv içine)..."
"$VENV_DIR/bin/python" -m pip install --upgrade pip
"$VENV_DIR/bin/pip" install fastapi uvicorn psutil

echo "[5/5] lenovo_stats_server.py yazılıyor..."
cat > "$APP_FILE" <<'PY'
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
        return {"cpu": float(cpu or 0), "sys": float(sys or 0)}
    except Exception:
        return None

def temps_from_sensors_cmd():
    try:
        r = subprocess.run(["sensors"], capture_output=True, text=True, timeout=2)
        out = r.stdout or ""
        # örnek: "+45.0°C" veya "+45.0 C"
        m = re.findall(r"([+-]?\d+(?:\.\d+)?)\s*°?C", out)
        if not m:
            return None
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
    return {"cpu": 0.0, "sys": 0.0}

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
PY

chmod +x "$APP_FILE"

echo
echo "KURULUM TAMAM."
echo "Çalıştırmak için:"
echo "  cd $BASE_DIR"
echo "  $VENV_DIR/bin/uvicorn lenovo_stats_server:app --host 0.0.0.0 --port 9000"
echo
echo "Test:"
echo "  curl -s http://127.0.0.1:9000/stats"
