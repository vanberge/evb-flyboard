# FlyBoard (`evb-flyboard`)

A real-time **192×64 RGB LED Dot-Matrix Overhead Flight & VHF/UHF Airband Tracker** designed for a widescreen monitor, desktop dashboard, or **Raspberry Pi + LED/LCD Kiosk**, and engineered to run within the **Google Cloud Run Free Tier (`~$0.00/mo`)**.

Built for **Grandville, MI (`49418`)** & **Gerald R. Ford International Airport (`KGRR`)**, with live support for **any 5-digit US ZIP code or global Airport ICAO/IATA code**.

---

## Key Features

- **192×64 Virtual HUB75 RGB LED Dot-Matrix Display:**
  - Authentic `5×7` bitmap typography, custom `16×16` pixel-art airline tail logos (Delta, United, American, Southwest, Allegiant, FedEx, USAF/Military, Private/GA), and `16×7` aircraft silhouettes (`jet`, `jumbo`, `regional`, `prop`, `heli`, `military`).
  - Live route progress bar, altitude/vertical speed arrows, sky-spotter look-up bearing/elevation angle, active VHF frequency readout, and scrolling bottom METAR + traffic ticker.
  - Multiple hardware LED shaders: **RGB Full Color**, **Retro Amber Airport**, **VFD Studio Cyan**, and **Tactical Night Green**.
- **Editable ZIP Code & Airport Geofence:**
  - Switch between quick presets (`49418`, `KGRR`) or type **any 5-digit US ZIP code** (resolved via `api.zippopotam.us`) and **any 3/4-letter Airport code** (resolved via NOAA `aviationweather.gov`) on the fly.
- **Airline & Operator Category Filtering:**
  - Filter overhead traffic by **Delta (`DAL`)**, **American (`AAL`)**, **United (`UAL`)**, **Southwest (`SWA`)**, **Allegiant (`AAY`)**, **Personal / Private / GA**, **Cargo (`FedEx`/`UPS`)**, **Military / Gov / Medevac**, or **Other Commercial**, complete with live sky counts.
- **VHF / UHF Airband Frequency Tracker & LiveATC Scanner Tuner:**
  - Computes each aircraft's active **VHF (`118–136.975 MHz` AM)** and **military UHF (`225–399.975 MHz` AM)** frequency, controlling ATC agency/sector (e.g., *KGRR Tower `135.650`*, *Great Lakes Approach South `128.400` / North `124.600`*, *Chicago Center `ZAU` Sector 26 Low `133.200`*, *Pullman High `126.125`*, *Ultra-High `128.650`*), and next expected frequency handoff.
  - One-click **🎧 LiveATC** and **📻 RadioReference** links in both the Spotter Card and the Overhead Traffic Queue table.
- **5-Second Server-Side Caching & Exponential Backoff Failover:**
  - Coalesces concurrent requests into a single 5-second cached snapshot (`FLIGHT_FEED_CACHE`) with automatic failover between **FlightRadar24** and **adsb.fi OpenData** (`opendata.adsb.fi`), plus 30-minute airframe/photo caching via **ADSBDB** and **HexDB**.
- **Widescreen Fullscreen Kiosk Mode:**
  - Collapsible ultra-compact top bar (`< 5%` viewport height) that automatically tucks into a floating corner pill when entering fullscreen mode.

---

## Quick Start (Local Development)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

uvicorn app:app --host 0.0.0.0 --port 8080
```

Open **`http://localhost:8080`** in your browser.

---

## Deploy to Google Cloud Run (Free Tier)

### Option A: Deploy Directly from GitHub in Cloud Run Console
1. Open the **[Google Cloud Run Console](https://console.cloud.google.com/run)** → **Create Service**.
2. Select **Continuously deploy from a repository (source or function)** → connect `vanberge/evb-flyboard` (`main` branch, `Dockerfile`).
3. Set **Region** to `us-central1`, **Authentication** to *Allow unauthenticated invocations*, **CPU allocation** to *CPU is only allocated during request processing*, **Minimum instances** = `0`, and **Maximum instances** = `1`.

### Option B: Deploy via Google Cloud CLI / Cloud Shell
```bash
git clone https://github.com/vanberge/evb-flyboard.git
cd evb-flyboard
bash deploy-cloudrun.sh
```

Or run `gcloud` directly:
```bash
gcloud run deploy evb-flyboard \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --min-instances 0 \
  --max-instances 1 \
  --cpu 1 \
  --memory 256Mi \
  --cpu-throttling \
  --port 8080
```

---

## Raspberry Pi Fullscreen Kiosk Launch

```bash
chromium-browser --kiosk --app=https://YOUR-CLOUD-RUN-URL.run.app \
  --start-fullscreen --noerrdialogs --disable-infobars --check-for-update-interval=31536000
```
