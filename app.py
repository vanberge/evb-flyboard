import asyncio
import math
import os
import random
import time
from typing import Any, Dict, List, Optional, Tuple

import httpx
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="FlyBoard — 49418 & KGRR Live LED Dot-Matrix Flight Tracker",
    description="Real-time ADS-B / FlightRadar24 overhead FlyBoard with route enrichment, tail photos, and KGRR METAR weather.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Preset Locations
LOCATIONS = {
    "49418": {
        "id": "49418",
        "name": "Grandville, MI (ZIP 49418)",
        "short_name": "49418 HOME",
        "lat": 42.8836,
        "lon": -85.7606,
        "elevation_ft": 605,
    },
    "KGRR": {
        "id": "KGRR",
        "name": "Gerald R. Ford Intl Airport (KGRR)",
        "short_name": "KGRR TOWER",
        "lat": 42.8808,
        "lon": -85.5228,
        "elevation_ft": 794,
    },
}

# Coordinates of major US & International airports for instant route progress calculation
AIRPORT_COORDS: Dict[str, Dict[str, Any]] = {
    "GRR": {"lat": 42.8808, "lon": -85.5228, "city": "Grand Rapids"},
    "DTW": {"lat": 42.2124, "lon": -83.3534, "city": "Detroit"},
    "ORD": {"lat": 41.9742, "lon": -87.9073, "city": "Chicago O'Hare"},
    "MDW": {"lat": 41.7868, "lon": -87.7522, "city": "Chicago Midway"},
    "MSP": {"lat": 44.8848, "lon": -93.2223, "city": "Minneapolis"},
    "ATL": {"lat": 33.6407, "lon": -84.4277, "city": "Atlanta"},
    "CLT": {"lat": 35.2140, "lon": -80.9431, "city": "Charlotte"},
    "DFW": {"lat": 32.8998, "lon": -97.0403, "city": "Dallas/Fort Worth"},
    "DEN": {"lat": 39.8561, "lon": -104.6737, "city": "Denver"},
    "LGA": {"lat": 40.7769, "lon": -73.8740, "city": "New York LaGuardia"},
    "JFK": {"lat": 40.6413, "lon": -73.7781, "city": "New York JFK"},
    "EWR": {"lat": 40.6895, "lon": -74.1745, "city": "Newark"},
    "BOS": {"lat": 42.3656, "lon": -71.0096, "city": "Boston"},
    "PHL": {"lat": 39.8744, "lon": -75.2424, "city": "Philadelphia"},
    "DCA": {"lat": 38.8512, "lon": -77.0402, "city": "Washington Reagan"},
    "IAD": {"lat": 38.9531, "lon": -77.4565, "city": "Washington Dulles"},
    "BWI": {"lat": 39.1754, "lon": -76.6684, "city": "Baltimore"},
    "MCO": {"lat": 28.4312, "lon": -81.3081, "city": "Orlando"},
    "MIA": {"lat": 25.7959, "lon": -80.2870, "city": "Miami"},
    "FLL": {"lat": 26.0742, "lon": -80.1506, "city": "Fort Lauderdale"},
    "TPA": {"lat": 27.9755, "lon": -82.5332, "city": "Tampa"},
    "RSW": {"lat": 26.5362, "lon": -81.7552, "city": "Fort Myers"},
    "SRQ": {"lat": 27.3954, "lon": -82.5544, "city": "Sarasota"},
    "PIE": {"lat": 27.9102, "lon": -82.6874, "city": "St. Pete-Clearwater"},
    "SFB": {"lat": 28.7776, "lon": -81.2375, "city": "Orlando Sanford"},
    "PGD": {"lat": 26.9202, "lon": -81.9905, "city": "Punta Gorda"},
    "VPS": {"lat": 30.4832, "lon": -86.5254, "city": "Destin-Fort Walton"},
    "BNA": {"lat": 36.1263, "lon": -86.6774, "city": "Nashville"},
    "IAH": {"lat": 29.9902, "lon": -95.3368, "city": "Houston Intercontinental"},
    "HOU": {"lat": 29.6454, "lon": -95.2789, "city": "Houston Hobby"},
    "AUS": {"lat": 30.1975, "lon": -97.6664, "city": "Austin"},
    "LAS": {"lat": 36.0840, "lon": -115.1537, "city": "Las Vegas"},
    "PHX": {"lat": 33.4373, "lon": -112.0078, "city": "Phoenix"},
    "AZA": {"lat": 33.3078, "lon": -111.6556, "city": "Phoenix-Mesa"},
    "LAX": {"lat": 33.9416, "lon": -118.4085, "city": "Los Angeles"},
    "SFO": {"lat": 37.6213, "lon": -122.3790, "city": "San Francisco"},
    "SEA": {"lat": 47.4502, "lon": -122.3088, "city": "Seattle"},
    "PDX": {"lat": 45.5898, "lon": -122.5951, "city": "Portland"},
    "SLC": {"lat": 40.7899, "lon": -111.9791, "city": "Salt Lake City"},
    "SAN": {"lat": 32.7338, "lon": -117.1933, "city": "San Diego"},
    "STL": {"lat": 38.7487, "lon": -90.3700, "city": "St. Louis"},
    "MCI": {"lat": 39.2976, "lon": -94.7139, "city": "Kansas City"},
    "CVG": {"lat": 39.0488, "lon": -84.6678, "city": "Cincinnati"},
    "CLE": {"lat": 41.4117, "lon": -81.8498, "city": "Cleveland"},
    "IND": {"lat": 39.7173, "lon": -86.2944, "city": "Indianapolis"},
    "MKE": {"lat": 42.9472, "lon": -87.8966, "city": "Milwaukee"},
    "LAN": {"lat": 42.7787, "lon": -84.5874, "city": "Lansing"},
    "AZO": {"lat": 42.2350, "lon": -85.5521, "city": "Kalamazoo"},
    "MKG": {"lat": 43.1695, "lon": -86.2382, "city": "Muskegon"},
    "TVC": {"lat": 44.7414, "lon": -85.5822, "city": "Traverse City"},
    "FNT": {"lat": 42.9654, "lon": -83.7436, "city": "Flint"},
    "PVD": {"lat": 41.7240, "lon": -71.4282, "city": "Providence"},
    "YYZ": {"lat": 43.6777, "lon": -79.6248, "city": "Toronto"},
    "YUL": {"lat": 45.4706, "lon": -73.7408, "city": "Montreal"},
    "YVR": {"lat": 49.1967, "lon": -123.1815, "city": "Vancouver"},
    "LHR": {"lat": 51.4700, "lon": -0.4543, "city": "London Heathrow"},
    "CDG": {"lat": 49.0097, "lon": 2.5479, "city": "Paris"},
    "AMS": {"lat": 52.3105, "lon": 4.7683, "city": "Amsterdam"},
    "FRA": {"lat": 50.0379, "lon": 8.5622, "city": "Frankfurt"},
    "MAD": {"lat": 40.4983, "lon": -3.5676, "city": "Madrid"},
    "DUB": {"lat": 53.4264, "lon": -6.2499, "city": "Dublin"},
    "ICN": {"lat": 37.4602, "lon": 126.4407, "city": "Seoul Incheon"},
    "HND": {"lat": 35.5494, "lon": 139.7798, "city": "Tokyo Haneda"},
    "NRT": {"lat": 35.7720, "lon": 140.3929, "city": "Tokyo Narita"},
}

AIRLINE_INFO: Dict[str, Dict[str, str]] = {
    "DAL": {"name": "Delta Air Lines", "callsign": "DELTA", "iata": "DL", "color": "#E01933", "accent": "#003366"},
    "UAL": {"name": "United Airlines", "callsign": "UNITED", "iata": "UA", "color": "#005DAA", "accent": "#48A9FF"},
    "AAL": {"name": "American Airlines", "callsign": "AMERICAN", "iata": "AA", "color": "#0078D2", "accent": "#C8102E"},
    "SWA": {"name": "Southwest Airlines", "callsign": "SOUTHWEST", "iata": "WN", "color": "#FFBF27", "accent": "#304CB2"},
    "AAY": {"name": "Allegiant Air", "callsign": "ALLEGIANT", "iata": "G4", "color": "#FF8200", "accent": "#005596"},
    "FFT": {"name": "Frontier Airlines", "callsign": "FRONTIER FLIGHT", "iata": "F9", "color": "#008556", "accent": "#44D62C"},
    "SKW": {"name": "SkyWest Airlines", "callsign": "SKYWEST", "iata": "OO", "color": "#004990", "accent": "#66B2FF"},
    "RPA": {"name": "Republic Airways", "callsign": "BRICKYARD", "iata": "YX", "color": "#003B71", "accent": "#5CA3FF"},
    "ENY": {"name": "Envoy Air", "callsign": "ENVOY", "iata": "MQ", "color": "#0078D2", "accent": "#E31837"},
    "EDV": {"name": "Endeavor Air", "callsign": "ENDEAVOR", "iata": "9E", "color": "#E01933", "accent": "#003366"},
    "JIA": {"name": "PSA Airlines", "callsign": "BLUE STREAK", "iata": "OH", "color": "#0078D2", "accent": "#C8102E"},
    "GJS": {"name": "GoJet Airlines", "callsign": "LINDBERGH", "iata": "G7", "color": "#005DAA", "accent": "#48A9FF"},
    "FDX": {"name": "FedEx Express", "callsign": "FEDEX", "iata": "FX", "color": "#FF6600", "accent": "#4D148C"},
    "UPS": {"name": "UPS Airlines", "callsign": "UPS", "iata": "5X", "color": "#FFB500", "accent": "#351C15"},
    "ASA": {"name": "Alaska Airlines", "callsign": "ALASKA", "iata": "AS", "color": "#0074C8", "accent": "#44D62C"},
    "JBU": {"name": "JetBlue Airways", "callsign": "JETBLUE", "iata": "B6", "color": "#003876", "accent": "#00A1DE"},
    "NKS": {"name": "Spirit Airlines", "callsign": "SPIRIT WINGS", "iata": "NK", "color": "#FFEC00", "accent": "#FFFFFF"},
    "ACA": {"name": "Air Canada", "callsign": "AIR CANADA", "iata": "AC", "color": "#F01428", "accent": "#FFFFFF"},
    "DLH": {"name": "Lufthansa", "callsign": "LUFTHANSA", "iata": "LH", "color": "#FFB800", "accent": "#05164D"},
    "BAW": {"name": "British Airways", "callsign": "SPEEDBIRD", "iata": "BA", "color": "#2E5C9A", "accent": "#EB2226"},
    "AFR": {"name": "Air France", "callsign": "AIRFRANS", "iata": "AF", "color": "#002157", "accent": "#FF0000"},
    "KLM": {"name": "KLM Royal Dutch", "callsign": "KLM", "iata": "KL", "color": "#00A1DE", "accent": "#FFFFFF"},
    "EJA": {"name": "NetJets", "callsign": "EXECJET", "iata": "1I", "color": "#38BDF8", "accent": "#94A3B8"},
    "LXJ": {"name": "Flexjet", "callsign": "FLEXJET", "iata": "FX", "color": "#F59E0B", "accent": "#D97706"},
}

AIRCRAFT_NAMES: Dict[str, str] = {
    "B737": "Boeing 737-700",
    "B738": "Boeing 737-800",
    "B739": "Boeing 737-900ER",
    "B38M": "Boeing 737 MAX 8",
    "B39M": "Boeing 737 MAX 9",
    "B712": "Boeing 717-200",
    "B752": "Boeing 757-200",
    "B753": "Boeing 757-300",
    "B763": "Boeing 767-300ER",
    "B772": "Boeing 777-200ER",
    "B77W": "Boeing 777-300ER",
    "B788": "Boeing 787-8 Dreamliner",
    "B789": "Boeing 787-9 Dreamliner",
    "B78X": "Boeing 787-10 Dreamliner",
    "B744": "Boeing 747-400",
    "B748": "Boeing 747-8 Intercontinental",
    "A319": "Airbus A319-100",
    "A320": "Airbus A320-200",
    "A20N": "Airbus A320neo",
    "A321": "Airbus A321-200",
    "A21N": "Airbus A321neo",
    "A332": "Airbus A330-200",
    "A333": "Airbus A330-300",
    "A339": "Airbus A330-900neo",
    "A359": "Airbus A350-900",
    "A35K": "Airbus A350-1000",
    "A388": "Airbus A380-800",
    "BCS1": "Airbus A220-100",
    "BCS3": "Airbus A220-300",
    "E170": "Embraer E170",
    "E75L": "Embraer E175LR",
    "E75S": "Embraer E175",
    "E190": "Embraer E190",
    "CRJ2": "Bombardier CRJ-200",
    "CRJ7": "Bombardier CRJ-700",
    "CRJ9": "Bombardier CRJ-900",
    "C172": "Cessna 172 Skyhawk",
    "C182": "Cessna 182 Skylane",
    "C208": "Cessna 208 Caravan",
    "PC12": "Pilatus PC-12",
    "SR22": "Cirrus SR22",
    "P28A": "Piper PA-28 Cherokee",
    "BE23": "Beechcraft B23 Musketeer",
    "BE20": "Beechcraft King Air 200",
    "CL30": "Bombardier Challenger 300",
    "CL35": "Bombardier Challenger 350",
    "C56X": "Cessna Citation Excel",
    "C68A": "Cessna Citation Latitude",
    "GLF6": "Gulfstream G650",
    "EC35": "Airbus H135 Medevac Helicopter",
    "K35R": "Boeing KC-135R Stratotanker",
}

# In-memory caches & provider circuit-breaker state
CACHE_TTL_SECONDS = 5.0
ENRICHMENT_CACHE: Dict[str, Dict[str, Any]] = {}
WEATHER_CACHE: Dict[str, Dict[str, Any]] = {}
FLIGHT_FEED_CACHE: Dict[str, Dict[str, Any]] = {}
RESOLVED_LOCATIONS_CACHE: Dict[str, Dict[str, Any]] = dict(LOCATIONS)
RESOLVED_AIRPORTS_CACHE: Dict[str, Dict[str, Any]] = {
    "KGRR": {
        "icao": "KGRR",
        "iata": "GRR",
        "name": "Gerald R. Ford Intl (Grand Rapids, MI)",
        "city": "Grand Rapids",
        "lat": 42.8808,
        "lon": -85.5228,
        "elevation_ft": 794,
    }
}
FLIGHT_FETCH_LOCK = asyncio.Lock()

PROVIDER_HEALTH: Dict[str, Dict[str, Any]] = {
    "fr24": {
        "name": "FlightRadar24 Zone Feed",
        "failures": 0,
        "cooldown_until": 0.0,
        "last_status": "READY",
        "last_error": None,
        "success_count": 0,
    },
    "adsb_fi": {
        "name": "adsb.fi OpenData Feed",
        "failures": 0,
        "cooldown_until": 0.0,
        "last_status": "READY",
        "last_error": None,
        "success_count": 0,
    },
    "adsbdb": {
        "name": "ADSBDB Route & Airframe API",
        "failures": 0,
        "cooldown_until": 0.0,
        "last_status": "READY",
        "last_error": None,
        "success_count": 0,
    },
}


def is_provider_available(provider_key: str) -> bool:
    """Return True if the provider is not currently in an exponential backoff cooldown window."""
    state = PROVIDER_HEALTH.get(provider_key)
    if not state:
        return True
    return time.time() >= state["cooldown_until"]


def record_provider_success(provider_key: str) -> None:
    """Reset consecutive failure count and clear any backoff cooldown."""
    state = PROVIDER_HEALTH.get(provider_key)
    if state:
        state["failures"] = 0
        state["cooldown_until"] = 0.0
        state["last_status"] = "HEALTHY"
        state["last_error"] = None
        state["success_count"] = state.get("success_count", 0) + 1


def record_provider_failure(
    provider_key: str,
    reason: str,
    base_delay: float = 5.0,
    max_delay: float = 300.0,
) -> float:
    """Apply exponential backoff (base * 2^(failures-1) + jitter) to a failing or rate-limited provider."""
    state = PROVIDER_HEALTH.get(provider_key)
    if not state:
        return 0.0
    state["failures"] = state.get("failures", 0) + 1
    failures = state["failures"]
    backoff_sec = min(max_delay, base_delay * (2 ** (failures - 1))) + random.uniform(0.25, 1.5)
    state["cooldown_until"] = time.time() + backoff_sec
    state["last_status"] = f"BACKOFF ({int(round(backoff_sec))}s, attempt #{failures})"
    state["last_error"] = reason
    return backoff_sec


def get_ipv4_client() -> httpx.AsyncClient:
    """Create an AsyncClient bound to IPv4 so dual-stack timeouts never occur."""
    transport = httpx.AsyncHTTPTransport(local_address="0.0.0.0")
    return httpx.AsyncClient(
        transport=transport,
        timeout=5.0,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36"
        },
    )


def haversine_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return great-circle distance in nautical miles."""
    r_nm = 3440.065
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r_nm * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))


def bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Return compass bearing from point 1 to point 2 in degrees (0-360)."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlambda = math.radians(lon2 - lon1)
    y = math.sin(dlambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(dlambda)
    brng = math.degrees(math.atan2(y, x))
    return (brng + 360) % 360


def deg_to_cardinal(deg: float) -> str:
    dirs = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    ix = round(deg / (360.0 / len(dirs)))
    return dirs[ix % len(dirs)]


def elevation_angle_deg(dist_nm: float, alt_ft: int, observer_elev_ft: int = 605) -> float:
    """Calculate how many degrees above the horizon the plane is from the observer."""
    if dist_nm <= 0.05:
        return 89.0
    delta_alt_ft = max(0, alt_ft - observer_elev_ft)
    dist_ft = dist_nm * 6076.12
    angle = math.degrees(math.atan2(delta_alt_ft, dist_ft))
    return round(max(1.0, min(89.0, angle)), 1)


async def resolve_airport(airport_query: str) -> Dict[str, Any]:
    """
    Resolve any 3-letter IATA or 4-letter ICAO airport code to coordinates and metadata.
    Uses in-memory cache + AIRPORT_COORDS first, falling back to NOAA AviationWeather.gov StationInfo API.
    """
    raw_code = (airport_query or "KGRR").strip().upper()
    if not raw_code:
        raw_code = "KGRR"

    if raw_code in RESOLVED_AIRPORTS_CACHE:
        return RESOLVED_AIRPORTS_CACHE[raw_code]

    # Check if 3-letter US IATA or 4-letter K-prefixed ICAO is in our built-in AIRPORT_COORDS
    iata_candidate = raw_code[1:] if len(raw_code) == 4 and raw_code.startswith("K") else raw_code
    icao_candidate = f"K{raw_code}" if len(raw_code) == 3 and raw_code.isalpha() else raw_code

    if iata_candidate in AIRPORT_COORDS:
        ap = AIRPORT_COORDS[iata_candidate]
        entry = {
            "icao": icao_candidate if len(icao_candidate) == 4 else f"K{iata_candidate}",
            "iata": iata_candidate,
            "name": f"{ap['city']} Airport ({icao_candidate})",
            "city": ap["city"],
            "lat": float(ap["lat"]),
            "lon": float(ap["lon"]),
            "elevation_ft": 750,
        }
        RESOLVED_AIRPORTS_CACHE[raw_code] = entry
        RESOLVED_AIRPORTS_CACHE[entry["icao"]] = entry
        return entry

    # Query official NOAA AviationWeather.gov public station database (no key, public domain)
    async with get_ipv4_client() as client:
        for lookup_id in (icao_candidate, raw_code):
            try:
                resp = await client.get(
                    f"https://aviationweather.gov/api/data/stationinfo?ids={lookup_id}&format=json",
                    timeout=3.5,
                )
                if resp.status_code == 200:
                    arr = resp.json()
                    if isinstance(arr, list) and len(arr) > 0:
                        st = arr[0]
                        icao_val = str(st.get("icaoId") or lookup_id).upper()
                        iata_val = str(st.get("iataId") or (icao_val[1:] if icao_val.startswith("K") and len(icao_val) == 4 else icao_val[:3])).upper()
                        site_name = str(st.get("site") or icao_val)
                        state_prov = str(st.get("state") or "")
                        lat_val = float(st.get("lat") or 42.8808)
                        lon_val = float(st.get("lon") or -85.5228)
                        elev_m = float(st.get("elev") or 240.0)
                        entry = {
                            "icao": icao_val,
                            "iata": iata_val,
                            "name": f"{site_name}{', ' + state_prov if state_prov else ''} ({icao_val})",
                            "city": site_name,
                            "lat": lat_val,
                            "lon": lon_val,
                            "elevation_ft": int(round(elev_m * 3.28084)),
                        }
                        RESOLVED_AIRPORTS_CACHE[raw_code] = entry
                        RESOLVED_AIRPORTS_CACHE[icao_val] = entry
                        AIRPORT_COORDS[iata_val] = {"lat": lat_val, "lon": lon_val, "city": site_name}
                        return entry
            except Exception:
                pass

    return RESOLVED_AIRPORTS_CACHE["KGRR"]


async def resolve_observer_location(location_query: str, airport_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Resolve any 5-digit US ZIP code (via Zippopotam.us) or Airport code to observer coordinates.
    Results are cached permanently in RESOLVED_LOCATIONS_CACHE so each ZIP is only looked up once.
    """
    loc_key = (location_query or "49418").strip().upper()
    if not loc_key:
        loc_key = "49418"

    if loc_key in RESOLVED_LOCATIONS_CACHE:
        return RESOLVED_LOCATIONS_CACHE[loc_key]

    # 1. If 5-digit US ZIP code -> resolve via open Zippopotam.us API
    if loc_key.isdigit() and len(loc_key) == 5:
        async with get_ipv4_client() as client:
            try:
                resp = await client.get(f"https://api.zippopotam.us/us/{loc_key}", timeout=3.5)
                if resp.status_code == 200:
                    payload = resp.json()
                    places = payload.get("places") or []
                    if places:
                        pl = places[0]
                        city = str(pl.get("place name") or loc_key)
                        state = str(pl.get("state abbreviation") or "")
                        lat_val = float(pl.get("latitude"))
                        lon_val = float(pl.get("longitude"))
                        entry = {
                            "id": loc_key,
                            "name": f"{city}, {state} (ZIP {loc_key})" if state else f"ZIP {loc_key}",
                            "short_name": f"{loc_key} {city[:6].upper()}",
                            "lat": lat_val,
                            "lon": lon_val,
                            "elevation_ft": airport_info.get("elevation_ft", 650),
                        }
                        RESOLVED_LOCATIONS_CACHE[loc_key] = entry
                        return entry
            except Exception:
                pass

    # 2. Otherwise treat location_query as an airport ICAO/IATA code
    ap = await resolve_airport(loc_key)
    if ap:
        entry = {
            "id": ap["icao"],
            "name": ap["name"],
            "short_name": f"{ap['icao']} TOWER",
            "lat": ap["lat"],
            "lon": ap["lon"],
            "elevation_ft": ap["elevation_ft"],
        }
        RESOLVED_LOCATIONS_CACHE[loc_key] = entry
        return entry

    return LOCATIONS["49418"]


def classify_silhouette(type_code: str, category_hint: str = "") -> str:
    t = (type_code or "").upper()
    if t in ("B744", "B748", "A388"):
        return "jumbo"
    if t in ("B772", "B77W", "B788", "B789", "B78X", "B763", "A332", "A333", "A339", "A359", "A35K"):
        return "widebody"
    if t in ("CRJ2", "CRJ7", "CRJ9", "E170", "E75L", "E75S", "E190", "CL30", "CL35", "C56X", "C68A", "GLF6"):
        return "regional"
    if t in ("EC35", "R44", "B06", "S76", "H60", "A139"):
        return "heli"
    if t in ("K35R", "C17", "C130", "F16", "A10", "T38"):
        return "military"
    if t in ("C172", "C182", "C208", "PC12", "SR22", "P28A", "BE23", "BE20"):
        return "prop"
    return "jet"


GA_TYPES = {
    "C150", "C152", "C172", "C177", "C182", "C206", "C208", "C210", "C310", "C340", "C402", "C414", "C421",
    "C25A", "C25B", "C25C", "C510", "C525", "C550", "C560", "C56X", "C680", "C68A", "C700", "C750",
    "P28A", "P28R", "P28T", "PA32", "PA34", "PA44", "PA46", "M20P", "M20T", "SR20", "SR22", "SF50",
    "BE23", "BE33", "BE35", "BE36", "BE55", "BE58", "BE9L", "BE20", "BE30", "BE40", "PRM1",
    "PC12", "PC24", "TBM7", "TBM8", "TBM9", "EA50", "E50P", "E55P", "LJ35", "LJ45", "LJ60", "LJ75",
    "CL30", "CL35", "CL60", "BD70", "GL5T", "GLEX", "GLF4", "GLF5", "GLF6", "GA5C", "GA6C",
    "FA7X", "FA8X", "F900", "F2TH", "H25B", "HA4T", "HDJT", "DA40", "DA42", "DA62", "RV7", "RV8", "RV10",
}


def classify_operator_group(
    airline_icao: str,
    flight_num: str,
    callsign: str,
    reg: str,
    type_code: str,
    orig_iata: str,
    dest_iata: str,
) -> str:
    """Classify an aircraft into an airline or aviation category for filtering."""
    al = (airline_icao or "").upper()
    fn = (flight_num or "").upper()
    cs = (callsign or "").upper()
    rg = (reg or "").upper()
    tc = (type_code or "").upper()

    # 1. Military / Government / Medevac
    if al in ("RCH", "CNV", "CFC", "PAT", "IAM", "RRR", "GAF", "AIO") or tc in ("K35R", "C17", "C130", "F16", "A10", "H60", "EC35"):
        return "MIL_GOV"

    # 2. Delta Air Lines (+ Delta Connection)
    if al in ("DAL", "EDV") or fn.startswith("DL") or cs.startswith("DAL"):
        return "DAL"

    # 3. American Airlines (+ American Eagle)
    if al in ("AAL", "ENY", "JIA", "PDT") or fn.startswith("AA") or cs.startswith("AAL"):
        return "AAL"

    # 4. United Airlines (+ United Express)
    if al in ("UAL", "GJS", "UCA", "ASH") or fn.startswith("UA") or cs.startswith("UAL"):
        return "UAL"

    # 5. Southwest Airlines
    if al == "SWA" or fn.startswith("WN") or cs.startswith("SWA"):
        return "SWA"

    # 6. Allegiant Air (Major KGRR Focus Carrier)
    if al == "AAY" or fn.startswith("G4") or cs.startswith("AAY"):
        return "AAY"

    # 7. Cargo / Freight (FedEx, UPS, Atlas, Kalitta, etc.)
    if al in ("FDX", "UPS", "GTI", "CKS", "ABX", "ATN", "polar") or fn.startswith(("FX", "5X")):
        return "CARGO"

    # 8. Personal / Private / General Aviation / Corporate Jets
    is_tail_callsign = bool(rg and (cs == rg or fn == rg or (cs.startswith("N") and cs[1:2].isdigit())))
    is_bizjet_fractional = al in ("EJA", "LXJ", "XOJ", "TWY", "VJA", "PGT")
    has_no_Gate_route = (not orig_iata or orig_iata == "---") and (not dest_iata or dest_iata == "---")
    if is_tail_callsign or is_bizjet_fractional or tc in GA_TYPES or (has_no_Gate_route and al in ("", "GA")):
        return "GA_PRIVATE"

    return "OTHER_COMM"


def compute_atc_comms(
    lat: float,
    lon: float,
    alt_ft: int,
    orig_iata: str,
    dest_iata: str,
    squawk: str,
    dist_airport_nm: float,
    operator_group: str,
    airport_icao: str = "KGRR",
    airport_iata: str = "GRR",
) -> Dict[str, str]:
    """
    Infer the active VHF/UHF Airband frequency, ATC facility/sector, next handoff frequency,
    and clickable LiveATC / RadioReference URLs based on 3D airspace geometry around the target airport.
    """
    ap_icao = (airport_icao or "KGRR").upper()
    ap_iata = (airport_iata or "GRR").upper()
    is_kgrr = ap_icao == "KGRR"
    liveatc_ap_url = f"https://www.liveatc.net/search/?icao={ap_icao}"

    # 1. Emergency Squawk 7700 -> VHF Guard 121.500 MHz
    if squawk == "7700":
        return {
            "frequency_mhz": "121.500",
            "uhf_mhz": "243.000",
            "agency": f"VHF EMERGENCY GUARD / {ap_icao} TWR",
            "sector_short": "121.5 GUARD",
            "handoff": "135.650 MHz (KGRR Tower)" if is_kgrr else f"{ap_icao} Tower / Emergency",
            "liveatc_url": liveatc_ap_url,
            "liveatc_label": f"Listen: {ap_icao} Tower / Emergency",
            "radioref_url": "https://www.radioreference.com/db/aid/2249",
        }

    # 2. Airport Tower Inner Core / Final Approach (< 3,900 ft & within 14 NM of target airport)
    if (dest_iata == ap_iata or orig_iata == ap_iata or dist_airport_nm <= 7.0) and alt_ft <= 3900 and dist_airport_nm <= 14.0:
        if is_kgrr:
            handoff = "121.800 MHz (KGRR Ground)" if dest_iata == "GRR" else "128.400 MHz (Great Lakes Dep)"
            return {
                "frequency_mhz": "135.650",
                "uhf_mhz": "339.800",
                "agency": "KGRR TOWER (LOCAL CONTROL)",
                "sector_short": "135.65 TWR",
                "handoff": handoff,
                "liveatc_url": liveatc_ap_url,
                "liveatc_label": "Listen: KGRR Tower (135.65)",
                "radioref_url": "https://www.radioreference.com/db/aid/2249",
            }
        return {
            "frequency_mhz": f"{ap_icao} TWR",
            "uhf_mhz": "257.800",
            "agency": f"{ap_icao} TOWER (LOCAL CONTROL)",
            "sector_short": f"{ap_icao} TOWER",
            "handoff": f"{ap_icao} Ground" if dest_iata == ap_iata else f"{ap_icao} Departure",
            "liveatc_url": liveatc_ap_url,
            "liveatc_label": f"Listen: {ap_icao} Tower",
            "radioref_url": "https://www.radioreference.com/db/aid/2249",
        }

    # 3. Terminal Radar Approach Control (TRACON) — Terminal Airspace (< 11,500 ft or Airport Arrival/Departure)
    if alt_ft <= 11500 and (dist_airport_nm <= 32.0 or dest_iata == ap_iata or orig_iata == ap_iata):
        if is_kgrr:
            # KGRR Runway 08R/26L centerline is ~42.8808N. South sector (covering 49418 Grandville) = 128.400, North = 124.600
            if lat <= 42.9000:
                freq = "128.400"
                sector_name = "GREAT LAKES APPR/DEP (SOUTH)"
                short = "128.40 APP-S"
            else:
                freq = "124.600"
                sector_name = "GREAT LAKES APPR/DEP (NORTH)"
                short = "124.60 APP-N"

            handoff = "135.650 MHz (KGRR Tower)" if dest_iata == "GRR" else "133.200 MHz (Chicago Ctr Low)"
            return {
                "frequency_mhz": freq,
                "uhf_mhz": "339.800",
                "agency": sector_name,
                "sector_short": short,
                "handoff": handoff,
                "liveatc_url": liveatc_ap_url,
                "liveatc_label": f"Listen: KGRR Approach ({freq})",
                "radioref_url": "https://www.radioreference.com/db/aid/2249",
            }
        return {
            "frequency_mhz": f"{ap_icao} APP",
            "uhf_mhz": "307.000",
            "agency": f"{ap_icao} TRACON APPR / DEP",
            "sector_short": f"{ap_icao} APPR",
            "handoff": f"{ap_icao} Tower" if dest_iata == ap_iata else "ARTCC Center Low",
            "liveatc_url": liveatc_ap_url,
            "liveatc_label": f"Listen: {ap_icao} Approach",
            "radioref_url": "https://www.radioreference.com/db/aid/2249",
        }

    # 4. Low VFR General Aviation outside TRACON core (< 3,800 ft)
    if alt_ft <= 3800 and operator_group == "GA_PRIVATE":
        return {
            "frequency_mhz": "122.800",
            "uhf_mhz": "128.400" if is_kgrr else "122.700",
            "agency": "LOCAL UNICOM/CTAF • GRR FF 128.4" if is_kgrr else f"LOCAL UNICOM/CTAF ({ap_icao} AREA)",
            "sector_short": "122.80 CTAF",
            "handoff": "128.400 MHz (Great Lakes Appr)" if is_kgrr else f"{ap_icao} Approach Flight Following",
            "liveatc_url": liveatc_ap_url,
            "liveatc_label": f"Listen: {ap_icao} Approach / CTAF",
            "radioref_url": "https://www.radioreference.com/db/aid/2249",
        }

    # 5. Enroute Low Sector (11,500 ft – 23,500 ft)
    if alt_ft <= 23500:
        if is_kgrr:
            if lat >= 43.05 and lon <= -85.95:
                return {
                    "frequency_mhz": "132.275",
                    "uhf_mhz": "254.350",
                    "agency": "CHICAGO CENTER (ZAU MUSKEGON LOW)",
                    "sector_short": "132.27 ZAU-L",
                    "handoff": "126.125 MHz (ZAU High) / 124.600 (GRR)",
                    "liveatc_url": "https://www.liveatc.net/search/?icao=ZAU",
                    "liveatc_label": "Listen: Chicago Center (ZAU)",
                    "radioref_url": "https://www.radioreference.com/db/aid/2236",
                }
            return {
                "frequency_mhz": "133.200",
                "uhf_mhz": "343.675",
                "agency": "CHICAGO CENTER (ZAU SEC 26 • GRR RCAG)",
                "sector_short": "133.20 ZAU-L",
                "handoff": "128.400 MHz (Great Lakes Appr)",
                "liveatc_url": "https://www.liveatc.net/search/?icao=ZAU",
                "liveatc_label": "Listen: Chicago Center (ZAU Low)",
                "radioref_url": "https://www.radioreference.com/db/aid/2236",
            }
        return {
            "frequency_mhz": "133.200",
            "uhf_mhz": "343.675",
            "agency": f"ARTCC ENROUTE LOW ({ap_icao} SECTOR)",
            "sector_short": "ARTCC LOW",
            "handoff": f"{ap_icao} TRACON Approach",
            "liveatc_url": liveatc_ap_url,
            "liveatc_label": f"Listen: {ap_icao} / Center Feeds",
            "radioref_url": "https://www.radioreference.com/db/aid/2236",
        }

    # 6. Enroute High Sector (23,500 ft – 33,500 ft)
    if alt_ft <= 33500:
        if is_kgrr:
            return {
                "frequency_mhz": "126.125",
                "uhf_mhz": "319.100",
                "agency": "CHICAGO CENTER (ZAU SEC 25 • PMM HIGH)",
                "sector_short": "126.12 ZAU-H",
                "handoff": "133.200 MHz (ZAU KUBBS Low)",
                "liveatc_url": "https://www.liveatc.net/search/?icao=ZAU",
                "liveatc_label": "Listen: Chicago Center (ZAU High)",
                "radioref_url": "https://www.radioreference.com/db/aid/2236",
            }
        return {
            "frequency_mhz": "126.125",
            "uhf_mhz": "319.100",
            "agency": f"ARTCC ENROUTE HIGH ({ap_icao} CORRIDOR)",
            "sector_short": "ARTCC HIGH",
            "handoff": "ARTCC Low Sector",
            "liveatc_url": liveatc_ap_url,
            "liveatc_label": f"Listen: {ap_icao} / Center Feeds",
            "radioref_url": "https://www.radioreference.com/db/aid/2236",
        }

    # 7. Enroute Ultra-High Sector (FL340+)
    return {
        "frequency_mhz": "128.650",
        "uhf_mhz": "351.825",
        "agency": "CHICAGO CENTER (ZAU ULTRA-HIGH)" if is_kgrr else f"ARTCC ULTRA-HIGH (FL340+ {ap_icao})",
        "sector_short": "128.65 ZAU-U" if is_kgrr else "ARTCC ULTRA",
        "handoff": "126.125 MHz (ZAU Pullman High)" if is_kgrr else "ARTCC High Sector",
        "liveatc_url": "https://www.liveatc.net/search/?icao=ZAU" if is_kgrr else liveatc_ap_url,
        "liveatc_label": "Listen: Chicago Center (ZAU)" if is_kgrr else f"Listen: {ap_icao} LiveATC",
        "radioref_url": "https://www.radioreference.com/db/aid/2236",
    }


async def enrich_aircraft(client: httpx.AsyncClient, icao_hex: str, callsign: str) -> Dict[str, Any]:
    cache_key = f"{icao_hex}:{callsign}"
    now = time.time()
    cached = ENRICHMENT_CACHE.get(cache_key)
    if cached and now - cached.get("_ts", 0) < 1800:
        return cached

    result: Dict[str, Any] = {"_ts": now}
    if is_provider_available("adsbdb") and icao_hex:
        try:
            url = f"https://api.adsbdb.com/v0/aircraft/{icao_hex}"
            if callsign:
                url += f"?callsign={callsign}"
            resp = await client.get(url, timeout=2.8)
            if resp.status_code == 200:
                record_provider_success("adsbdb")
                payload = resp.json().get("response", {})
                ac = payload.get("aircraft")
                if isinstance(ac, dict):
                    result["manufacturer"] = ac.get("manufacturer") or ""
                    result["model"] = ac.get("type") or ""
                    result["owner"] = ac.get("registered_owner") or ""
                    result["operator_code"] = ac.get("registered_owner_operator_flag_code") or ""
                    result["photo_url"] = ac.get("url_photo") or ac.get("url_photo_thumbnail") or ""
                    result["photo_thumb"] = ac.get("url_photo_thumbnail") or ac.get("url_photo") or ""

                route = payload.get("flightroute")
                if isinstance(route, dict):
                    airline = route.get("airline") or {}
                    if isinstance(airline, dict):
                        result["airline_name"] = airline.get("name") or ""
                        result["radio_callsign"] = airline.get("callsign") or ""
                    orig = route.get("origin") or {}
                    dest = route.get("destination") or {}
                    if isinstance(orig, dict) and orig.get("iata_code"):
                        result["adsbdb_origin_iata"] = orig.get("iata_code")
                        result["adsbdb_origin_city"] = orig.get("municipality") or orig.get("name") or ""
                        result["adsbdb_origin_lat"] = orig.get("latitude")
                        result["adsbdb_origin_lon"] = orig.get("longitude")
                    if isinstance(dest, dict) and dest.get("iata_code"):
                        result["adsbdb_dest_iata"] = dest.get("iata_code")
                        result["adsbdb_dest_city"] = dest.get("municipality") or dest.get("name") or ""
                        result["adsbdb_dest_lat"] = dest.get("latitude")
                        result["adsbdb_dest_lon"] = dest.get("longitude")
            elif resp.status_code in (429, 500, 502, 503, 504):
                record_provider_failure("adsbdb", f"HTTP {resp.status_code}", base_delay=10.0)
        except Exception as exc:
            record_provider_failure("adsbdb", type(exc).__name__, base_delay=10.0)

    # If no photo from adsbdb, try hexdb thumbnail endpoint
    if not result.get("photo_url") and icao_hex:
        try:
            r_img = await client.get(f"https://hexdb.io/hex-image-thumb?hex={icao_hex}", timeout=2.0)
            if r_img.status_code == 200 and r_img.text.strip().startswith("http"):
                result["photo_url"] = r_img.text.strip()
                result["photo_thumb"] = r_img.text.strip()
        except Exception:
            pass

    ENRICHMENT_CACHE[cache_key] = result
    return result


def build_showcase_flights(center_lat: float, center_lon: float, observer_elev: int, mode: str) -> List[Dict[str, Any]]:
    """Build hyper-realistic West Michigan / KGRR showcase flights when requested or if sky is quiet."""
    t = time.time()
    # Smoothly animate positions over time so the radar and distance numbers are alive!
    phase = (t % 120) / 120.0
    showcase_raw = [
        {
            "id": "sim-dl1492",
            "icao_hex": "A44369",
            "callsign": "DAL1492",
            "flight_number": "DL1492",
            "airline_icao": "DAL",
            "registration": "N374DA",
            "type_code": "B738",
            "origin_iata": "ATL",
            "dest_iata": "GRR",
            "lat": 42.8815 + math.sin(t / 30.0) * 0.004,
            "lon": -85.7450 + phase * 0.08,  # Flying East right over 49418 Grandville onto KGRR Runway 08R!
            "altitude_ft": 2450,
            "ground_speed_kts": 162,
            "track_deg": 88,
            "vertical_rate_fpm": -750,
            "squawk": "2415",
            "photo_url": "https://image.airport-data.com/aircraft/001676265.jpg",
        },
        {
            "id": "sim-ua1844",
            "icao_hex": "A3A0EB",
            "callsign": "UAL1844",
            "flight_number": "UA1844",
            "airline_icao": "UAL",
            "registration": "N33292",
            "type_code": "B738",
            "origin_iata": "GRR",
            "dest_iata": "DEN",
            "lat": 42.8950 + phase * 0.03,
            "lon": -85.6420 - phase * 0.12,
            "altitude_ft": 6800,
            "ground_speed_kts": 265,
            "track_deg": 274,
            "vertical_rate_fpm": 2150,
            "squawk": "3142",
            "photo_url": "",
        },
        {
            "id": "sim-g41102",
            "icao_hex": "A33219",
            "callsign": "AAY1102",
            "flight_number": "G41102",
            "airline_icao": "AAY",
            "registration": "N306NV",
            "type_code": "A320",
            "origin_iata": "PIE",
            "dest_iata": "GRR",
            "lat": 42.7620 + phase * 0.05,
            "lon": -85.6910 + phase * 0.04,
            "altitude_ft": 5200,
            "ground_speed_kts": 218,
            "track_deg": 32,
            "vertical_rate_fpm": -1100,
            "squawk": "4621",
            "photo_url": "",
        },
        {
            "id": "sim-lh430",
            "icao_hex": "3C4B26",
            "callsign": "DLH430",
            "flight_number": "LH430",
            "airline_icao": "DLH",
            "registration": "D-ABYF",
            "type_code": "B748",
            "origin_iata": "FRA",
            "dest_iata": "ORD",
            "lat": 42.9120,
            "lon": -85.7100 - phase * 0.09,
            "altitude_ft": 36000,
            "ground_speed_kts": 472,
            "track_deg": 258,
            "vertical_rate_fpm": 0,
            "squawk": "1402",
            "photo_url": "",
        },
        {
            "id": "sim-rch421",
            "icao_hex": "AE0488",
            "callsign": "RCH421",
            "flight_number": "RCH421",
            "airline_icao": "RCH",
            "registration": "62-3543",
            "type_code": "K35R",
            "origin_iata": "MTC",
            "dest_iata": "GRR",
            "lat": 42.9310 - phase * 0.02,
            "lon": -85.7850 + phase * 0.05,
            "altitude_ft": 11500,
            "ground_speed_kts": 315,
            "track_deg": 115,
            "vertical_rate_fpm": -450,
            "squawk": "7700" if mode == "emergency" else "4111",
            "photo_url": "",
        },
        {
            "id": "sim-aa1208",
            "icao_hex": "A1B821",
            "callsign": "AAL1208",
            "flight_number": "AA1208",
            "airline_icao": "AAL",
            "registration": "N818AL",
            "type_code": "B738",
            "origin_iata": "DFW",
            "dest_iata": "GRR",
            "lat": 42.8320 + phase * 0.04,
            "lon": -85.8120 + phase * 0.06,
            "altitude_ft": 4100,
            "ground_speed_kts": 195,
            "track_deg": 72,
            "vertical_rate_fpm": -850,
            "squawk": "2241",
            "photo_url": "",
        },
        {
            "id": "sim-n437ps",
            "icao_hex": "A53E11",
            "callsign": "N437PS",
            "flight_number": "N437PS",
            "airline_icao": "GA",
            "registration": "N437PS",
            "type_code": "SR22",
            "origin_iata": "GRR",
            "dest_iata": "TVC",
            "lat": 42.9180 + phase * 0.03,
            "lon": -85.7320 - phase * 0.02,
            "altitude_ft": 3400,
            "ground_speed_kts": 148,
            "track_deg": 352,
            "vertical_rate_fpm": 400,
            "squawk": "1200",
            "photo_url": "",
        },
    ]

    if mode == "emergency":
        # Put emergency flight first
        showcase_raw[0]["squawk"] = "7700"
        showcase_raw[0]["vertical_rate_fpm"] = -2400

    flights = []
    for item in showcase_raw:
        flights.append(format_flight_record(item, center_lat, center_lon, observer_elev, {}))
    flights.sort(key=lambda x: x["priority_score"], reverse=True)
    return flights


def format_flight_record(
    raw: Dict[str, Any],
    center_lat: float,
    center_lon: float,
    observer_elev: int,
    enriched: Dict[str, Any],
    home_airport: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    ap = home_airport or RESOLVED_AIRPORTS_CACHE["KGRR"]
    ap_icao = ap.get("icao", "KGRR").upper()
    ap_iata = ap.get("iata", "GRR").upper()
    ap_lat = float(ap.get("lat", 42.8808))
    ap_lon = float(ap.get("lon", -85.5228))

    lat = float(raw["lat"])
    lon = float(raw["lon"])
    alt_ft = int(raw.get("altitude_ft") or 0)
    gs_kts = int(raw.get("ground_speed_kts") or 0)
    track_deg = int(raw.get("track_deg") or 0)
    vrate_fpm = int(raw.get("vertical_rate_fpm") or 0)
    icao_hex = (raw.get("icao_hex") or "").upper()
    callsign = (raw.get("callsign") or "").strip().upper()
    flight_num = (raw.get("flight_number") or callsign or raw.get("registration") or "UNKN").strip().upper()
    airline_icao = (raw.get("airline_icao") or "").strip().upper()
    if not airline_icao and len(callsign) >= 3 and callsign[:3].isalpha():
        airline_icao = callsign[:3]

    orig_iata = (raw.get("origin_iata") or enriched.get("adsbdb_origin_iata") or "").upper()
    dest_iata = (raw.get("dest_iata") or enriched.get("adsbdb_dest_iata") or "").upper()
    type_code = (raw.get("type_code") or "").upper()
    reg = (raw.get("registration") or "").upper()
    squawk = str(raw.get("squawk") or "")

    dist_nm = haversine_nm(center_lat, center_lon, lat, lon)
    dist_mi = dist_nm * 1.15078
    brng = bearing_deg(center_lat, center_lon, lat, lon)
    cardinal = deg_to_cardinal(brng)
    elev_deg = elevation_angle_deg(dist_nm, alt_ft, observer_elev)

    # Distance to the active target airport (defaults to KGRR)
    dist_airport_nm = haversine_nm(ap_lat, ap_lon, lat, lon)

    # Airline metadata
    al_meta = AIRLINE_INFO.get(airline_icao, {})
    airline_name = (
        enriched.get("airline_name")
        or al_meta.get("name")
        or raw.get("ownOp")
        or enriched.get("owner")
        or ""
    )
    if not airline_name:
        if airline_icao == "RCH":
            airline_name = "US Air Force Mobility Command"
        elif reg.startswith("N"):
            airline_name = "Private / General Aviation"
        else:
            airline_name = "Commercial Carrier"

    radio_callsign = enriched.get("radio_callsign") or al_meta.get("callsign") or ""
    brand_color = al_meta.get("color") or ("#10B981" if airline_icao == "RCH" else "#F59E0B")
    accent_color = al_meta.get("accent") or "#38BDF8"

    # Aircraft full model name
    if enriched.get("manufacturer") and enriched.get("model"):
        aircraft_model = f"{enriched['manufacturer']} {enriched['model']}"
    elif raw.get("desc"):
        aircraft_model = str(raw["desc"])
    else:
        aircraft_model = AIRCRAFT_NAMES.get(type_code, type_code or "Fixed-Wing Aircraft")

    # Origin & Destination cities + Route Progress %
    orig_info = AIRPORT_COORDS.get(orig_iata, {})
    dest_info = AIRPORT_COORDS.get(dest_iata, {})
    orig_city = orig_info.get("city") or enriched.get("adsbdb_origin_city") or orig_iata or "Local"
    dest_city = dest_info.get("city") or enriched.get("adsbdb_dest_city") or dest_iata or "Enroute"

    orig_lat = orig_info.get("lat") or enriched.get("adsbdb_origin_lat")
    orig_lon = orig_info.get("lon") or enriched.get("adsbdb_origin_lon")
    dest_lat = dest_info.get("lat") or enriched.get("adsbdb_dest_lat")
    dest_lon = dest_info.get("lon") or enriched.get("adsbdb_dest_lon")

    progress_pct = 50
    total_route_nm = None
    remaining_nm = None
    if orig_lat is not None and dest_lat is not None:
        total_d = haversine_nm(float(orig_lat), float(orig_lon), float(dest_lat), float(dest_lon))
        rem_d = haversine_nm(lat, lon, float(dest_lat), float(dest_lon))
        total_route_nm = round(total_d, 1)
        remaining_nm = round(rem_d, 1)
        if total_d > 5:
            progress_pct = int(max(3, min(98, round(((total_d - rem_d) / total_d) * 100))))

    # Flight phase relative to target airport & observer
    if squawk in ("7700", "7600", "7500"):
        phase_badge = f"SQUAWK {squawk} ALERT"
        phase_type = "emergency"
    elif dest_iata == ap_iata and (alt_ft < 6500 or dist_airport_nm < 18):
        phase_badge = f"FINAL APPR {ap_icao}" if alt_ft < 3800 else f"ARRIVING {ap_icao}"
        phase_type = "arriving_kgrr"
    elif orig_iata == ap_iata and (alt_ft < 12000 or dist_airport_nm < 25):
        phase_badge = f"DEPARTING {ap_icao}"
        phase_type = "departing_kgrr"
    elif dest_iata == ap_iata:
        phase_badge = f"INBOUND {ap_icao}"
        phase_type = "arriving_kgrr"
    elif orig_iata == ap_iata:
        phase_badge = f"OUTBOUND {ap_icao}"
        phase_type = "departing_kgrr"
    elif dist_nm <= 6.0:
        phase_badge = "DIRECTLY OVERHEAD"
        phase_type = "overhead"
    elif vrate_fpm > 350:
        phase_badge = "CLIMBING"
        phase_type = "climbing"
    elif vrate_fpm < -350:
        phase_badge = "DESCENDING"
        phase_type = "descending"
    else:
        phase_badge = f"CRUISE FL{int(round(alt_ft / 100)):03d}" if alt_ft >= 18000 else "ENROUTE"
        phase_type = "cruise"

    # Priority score for sorting (prefer close overhead flights & target airport arrivals/departures)
    priority_score = 100.0 - dist_nm
    if dest_iata == ap_iata or orig_iata == ap_iata:
        priority_score += 22.0
    if orig_iata and dest_iata:
        priority_score += 10.0
    if squawk in ("7700", "7600"):
        priority_score += 500.0

    operator_group = classify_operator_group(
        airline_icao, flight_num, callsign, reg, type_code, orig_iata, dest_iata
    )
    atc_info = compute_atc_comms(
        lat,
        lon,
        alt_ft,
        orig_iata,
        dest_iata,
        squawk,
        dist_airport_nm,
        operator_group,
        airport_icao=ap_icao,
        airport_iata=ap_iata,
    )

    return {
        "id": raw.get("id") or icao_hex or callsign,
        "icao_hex": icao_hex,
        "callsign": callsign or reg or "N/A",
        "flight_number": flight_num,
        "airline_icao": airline_icao or ("GA" if reg.startswith("N") else "AIR"),
        "airline_name": airline_name,
        "operator_group": operator_group,
        "radio_callsign": radio_callsign,
        "atc": atc_info,
        "brand_color": brand_color,
        "accent_color": accent_color,
        "registration": reg or "UNKN",
        "type_code": type_code or "ACFT",
        "aircraft_model": aircraft_model,
        "silhouette": classify_silhouette(type_code),
        "origin_iata": orig_iata or "---",
        "dest_iata": dest_iata or "---",
        "origin_city": orig_city,
        "dest_city": dest_city,
        "progress_pct": progress_pct,
        "total_route_nm": total_route_nm,
        "remaining_nm": remaining_nm,
        "lat": round(lat, 4),
        "lon": round(lon, 4),
        "altitude_ft": alt_ft,
        "ground_speed_kts": gs_kts,
        "ground_speed_mph": int(round(gs_kts * 1.15078)),
        "track_deg": track_deg,
        "track_cardinal": deg_to_cardinal(track_deg),
        "vertical_rate_fpm": vrate_fpm,
        "squawk": squawk,
        "distance_nm": round(dist_nm, 1),
        "distance_mi": round(dist_mi, 1),
        "bearing_deg": int(round(brng)),
        "bearing_cardinal": cardinal,
        "elevation_deg": elev_deg,
        "phase_badge": phase_badge,
        "phase_type": phase_type,
        "photo_url": enriched.get("photo_url") or raw.get("photo_url") or "",
        "priority_score": round(priority_score, 2),
    }


def compute_operator_counts(flights: List[Dict[str, Any]]) -> Dict[str, int]:
    counts: Dict[str, int] = {
        "all": len(flights),
        "DAL": 0,
        "AAL": 0,
        "UAL": 0,
        "SWA": 0,
        "AAY": 0,
        "GA_PRIVATE": 0,
        "CARGO": 0,
        "MIL_GOV": 0,
        "OTHER_COMM": 0,
    }
    for f in flights:
        grp = f.get("operator_group", "OTHER_COMM")
        counts[grp] = counts.get(grp, 0) + 1
    return counts


async def fetch_from_fr24(
    client: httpx.AsyncClient, center_lat: float, center_lon: float, radius_nm: float
) -> List[Dict[str, Any]]:
    lat_delta = (radius_nm / 60.0) * 1.15
    lon_delta = (radius_nm / (60.0 * math.cos(math.radians(center_lat)))) * 1.15
    n_lat = round(center_lat + lat_delta, 3)
    s_lat = round(center_lat - lat_delta, 3)
    w_lon = round(center_lon - lon_delta, 3)
    e_lon = round(center_lon + lon_delta, 3)

    fr24_url = (
        f"https://data-cloud.flightradar24.com/zones/fcgi/feed.js"
        f"?bounds={n_lat},{s_lat},{w_lon},{e_lon}"
        f"&faa=1&satellite=1&mlat=1&flarm=1&adsb=1&gnd=0&air=1&vehicles=0&estimated=1&maxage=14400&gliders=0&stats=0"
    )
    resp = await client.get(fr24_url)
    if resp.status_code != 200:
        raise RuntimeError(f"FR24 HTTP {resp.status_code}")

    data = resp.json()
    candidates: List[Dict[str, Any]] = []
    for key, val in data.items():
        if not isinstance(val, list) or len(val) < 17:
            continue
        ac_lat = float(val[1])
        ac_lon = float(val[2])
        dist_nm = haversine_nm(center_lat, center_lon, ac_lat, ac_lon)
        if dist_nm > radius_nm:
            continue
        alt_ft = int(val[4] or 0)
        if alt_ft <= 100 and int(val[14] or 0) == 1:
            continue
        candidates.append(
            {
                "id": key,
                "icao_hex": str(val[0] or ""),
                "lat": ac_lat,
                "lon": ac_lon,
                "track_deg": int(val[3] or 0),
                "altitude_ft": alt_ft,
                "ground_speed_kts": int(val[5] or 0),
                "squawk": str(val[6] or ""),
                "type_code": str(val[8] or ""),
                "registration": str(val[9] or ""),
                "origin_iata": str(val[11] or ""),
                "dest_iata": str(val[12] or ""),
                "flight_number": str(val[13] or ""),
                "vertical_rate_fpm": int(val[15] or 0),
                "callsign": str(val[16] or ""),
                "airline_icao": str(val[18] if len(val) > 18 else ""),
                "_dist_nm": dist_nm,
            }
        )
    return candidates


async def fetch_from_adsb_fi(
    client: httpx.AsyncClient, center_lat: float, center_lon: float, radius_nm: float
) -> List[Dict[str, Any]]:
    dist_int = max(5, min(250, int(round(radius_nm))))
    url = f"https://opendata.adsb.fi/api/v2/lat/{center_lat:.4f}/lon/{center_lon:.4f}/dist/{dist_int}"
    resp = await client.get(url)
    if resp.status_code != 200:
        raise RuntimeError(f"adsb.fi HTTP {resp.status_code}")

    aircraft_list = resp.json().get("aircraft", [])
    candidates: List[Dict[str, Any]] = []
    for ac in aircraft_list:
        if not isinstance(ac, dict):
            continue
        if "lat" not in ac or "lon" not in ac:
            continue
        alt_raw = ac.get("alt_baro")
        if alt_raw == "ground":
            continue
        alt_ft = int(alt_raw) if isinstance(alt_raw, (int, float)) else 0
        ac_lat = float(ac["lat"])
        ac_lon = float(ac["lon"])
        dist_nm = haversine_nm(center_lat, center_lon, ac_lat, ac_lon)
        if dist_nm > radius_nm:
            continue
        hex_code = str(ac.get("hex") or "").upper()
        callsign = str(ac.get("flight") or "").strip().upper()
        reg = str(ac.get("r") or "").strip().upper()
        vrate = ac.get("baro_rate") if ac.get("baro_rate") is not None else ac.get("geom_rate")
        db_flags = int(ac.get("dbFlags") or 0)
        airline_icao = "RCH" if (db_flags & 1) else (callsign[:3] if len(callsign) >= 3 and callsign[:3].isalpha() else "")

        candidates.append(
            {
                "id": hex_code or callsign,
                "icao_hex": hex_code,
                "lat": ac_lat,
                "lon": ac_lon,
                "track_deg": int(round(float(ac.get("track") or 0))),
                "altitude_ft": alt_ft,
                "ground_speed_kts": int(round(float(ac.get("gs") or 0))),
                "squawk": str(ac.get("squawk") or ""),
                "type_code": str(ac.get("t") or ""),
                "registration": reg,
                "origin_iata": "",
                "dest_iata": "",
                "flight_number": callsign or reg,
                "vertical_rate_fpm": int(vrate or 0),
                "callsign": callsign,
                "airline_icao": airline_icao,
                "desc": str(ac.get("desc") or ""),
                "ownOp": str(ac.get("ownOp") or ""),
                "_dist_nm": dist_nm,
            }
        )
    return candidates


async def get_cached_or_live_flights(
    center_lat: float,
    center_lon: float,
    observer_elev: int,
    radius_nm: float,
    prefer_provider: str = "auto",
    home_airport: Optional[Dict[str, Any]] = None,
) -> Tuple[List[Dict[str, Any]], str, Dict[str, Any]]:
    """
    Return formatted flights for the requested airspace using a 5-second server-side cache,
    multi-provider failover (FR24 -> adsb.fi), and per-provider exponential backoff.
    """
    ap = home_airport or RESOLVED_AIRPORTS_CACHE["KGRR"]
    ap_icao = ap.get("icao", "KGRR").upper()
    ap_iata = ap.get("iata", "GRR").upper()
    cache_key = f"{round(center_lat, 3)}:{round(center_lon, 3)}:{round(radius_nm, 1)}:{prefer_provider}:{ap_icao}"
    now = time.time()

    cached_entry = FLIGHT_FEED_CACHE.get(cache_key)
    if cached_entry and (now - cached_entry["timestamp"]) < CACHE_TTL_SECONDS:
        age = round(now - cached_entry["timestamp"], 2)
        return (
            cached_entry["flights"],
            f"{cached_entry['source']} (CACHED {age}s)",
            {
                "cache_hit": True,
                "cache_age_sec": age,
                "cache_ttl_sec": CACHE_TTL_SECONDS,
                "providers": PROVIDER_HEALTH,
            },
        )

    async with FLIGHT_FETCH_LOCK:
        # Double-check cache after acquiring lock in case another concurrent request just refreshed it
        now = time.time()
        cached_entry = FLIGHT_FEED_CACHE.get(cache_key)
        if cached_entry and (now - cached_entry["timestamp"]) < CACHE_TTL_SECONDS:
            age = round(now - cached_entry["timestamp"], 2)
            return (
                cached_entry["flights"],
                f"{cached_entry['source']} (CACHED {age}s)",
                {
                    "cache_hit": True,
                    "cache_age_sec": age,
                    "cache_ttl_sec": CACHE_TTL_SECONDS,
                    "providers": PROVIDER_HEALTH,
                },
            )

        raw_candidates: List[Dict[str, Any]] = []
        source_name = ""

        async with get_ipv4_client() as client:
            # 1. Try Primary Provider (FR24) unless user forced adsb_fi or FR24 is in exponential backoff
            if prefer_provider != "adsb_fi" and is_provider_available("fr24"):
                try:
                    raw_candidates = await fetch_from_fr24(client, center_lat, center_lon, radius_nm)
                    record_provider_success("fr24")
                    source_name = "LIVE FR24 FEED"
                except Exception as exc:
                    backoff = record_provider_failure("fr24", str(exc), base_delay=5.0, max_delay=300.0)
                    source_name = f"FR24 BACKOFF ({int(backoff)}s)"

            # 2. Automatic Failover (or explicit selection) -> OpenData adsb.fi Community ADS-B
            if not raw_candidates and is_provider_available("adsb_fi"):
                try:
                    raw_candidates = await fetch_from_adsb_fi(client, center_lat, center_lon, radius_nm)
                    record_provider_success("adsb_fi")
                    if source_name.startswith("FR24 BACKOFF"):
                        source_name = f"FAILOVER: ADSB.FI ({source_name})"
                    else:
                        source_name = "LIVE ADSB.FI UNFILTERED FEED"
                except Exception as exc:
                    backoff = record_provider_failure("adsb_fi", str(exc), base_delay=5.0, max_delay=300.0)
                    source_name = f"ALL FEEDS BACKOFF ({int(backoff)}s)"

            # 3. If both live feeds failed/backed off, serve stale cache if available
            if not raw_candidates and cached_entry:
                stale_age = int(round(time.time() - cached_entry["timestamp"]))
                return (
                    cached_entry["flights"],
                    f"STALE CACHE ({stale_age}s ago • {source_name})",
                    {
                        "cache_hit": True,
                        "stale": True,
                        "cache_age_sec": stale_age,
                        "cache_ttl_sec": CACHE_TTL_SECONDS,
                        "providers": PROVIDER_HEALTH,
                    },
                )

            # Sort raw candidates by distance + target airport relevance so we enrich the top 10 in parallel
            raw_candidates.sort(
                key=lambda x: x["_dist_nm"] - (18.0 if x["dest_iata"] == ap_iata or x["origin_iata"] == ap_iata else 0.0)
            )

            top_slice = raw_candidates[:10]
            enrichment_tasks = [
                enrich_aircraft(client, item["icao_hex"], item["callsign"]) for item in top_slice
            ]
            enriched_results = await asyncio.gather(*enrichment_tasks, return_exceptions=True)

            enriched_map: Dict[str, Dict[str, Any]] = {}
            for item, res in zip(top_slice, enriched_results):
                if isinstance(res, dict):
                    enriched_map[item["id"]] = res

        flights = [
            format_flight_record(item, center_lat, center_lon, observer_elev, enriched_map.get(item["id"], {}), home_airport=ap)
            for item in raw_candidates
        ]

        FLIGHT_FEED_CACHE[cache_key] = {
            "timestamp": time.time(),
            "source": source_name or "LIVE ADS-B",
            "flights": flights,
        }

        return (
            flights,
            source_name or "LIVE ADS-B",
            {
                "cache_hit": False,
                "cache_age_sec": 0.0,
                "cache_ttl_sec": CACHE_TTL_SECONDS,
                "providers": PROVIDER_HEALTH,
            },
        )


@app.get("/api/health")
async def get_provider_health():
    """Inspect server-side cache entries and per-provider exponential backoff states."""
    now = time.time()
    return {
        "cache_ttl_seconds": CACHE_TTL_SECONDS,
        "cached_zones": [
            {"key": k, "age_sec": round(now - v["timestamp"], 2), "flight_count": len(v["flights"])}
            for k, v in FLIGHT_FEED_CACHE.items()
        ],
        "enrichment_cache_size": len(ENRICHMENT_CACHE),
        "resolved_locations_cached": list(RESOLVED_LOCATIONS_CACHE.keys()),
        "resolved_airports_cached": list(RESOLVED_AIRPORTS_CACHE.keys()),
        "providers": PROVIDER_HEALTH,
    }


@app.get("/api/flights")
async def get_flights(
    location: str = Query("49418", description="Any 5-digit US ZIP code (e.g. 49418, 60601) or Airport code (e.g. KGRR, KORD)"),
    airport: str = Query("KGRR", description="Reference Airport ICAO/IATA code (e.g. KGRR, KDTW, KORD)"),
    lat: Optional[float] = Query(None),
    lon: Optional[float] = Query(None),
    radius_nm: float = Query(45.0, ge=5.0, le=150.0),
    filter_mode: str = Query("all", description="all | kgrr | low | commercial"),
    airline_filter: str = Query("all", description="all | DAL | AAL | UAL | SWA | AAY | GA_PRIVATE | CARGO | MIL_GOV | OTHER_COMM"),
    sim_mode: str = Query("live", description="live | adsb_fi | approach_rush | emergency"),
):
    ap_info = await resolve_airport(airport)
    loc = await resolve_observer_location(location, ap_info)
    center_lat = lat if lat is not None else loc["lat"]
    center_lon = lon if lon is not None else loc["lon"]
    observer_elev = loc["elevation_ft"]
    ap_iata = ap_info["iata"]

    # If user explicitly toggled a demo simulation mode
    if sim_mode in ("approach_rush", "emergency"):
        sim_flights = build_showcase_flights(center_lat, center_lon, observer_elev, sim_mode)
        operator_counts = compute_operator_counts(sim_flights)
        if airline_filter and airline_filter != "all":
            sim_flights = [f for f in sim_flights if f["operator_group"] == airline_filter]
        return {
            "source": f"SIMULATION ({sim_mode.upper()})",
            "timestamp": int(time.time()),
            "observer": {
                "id": loc["id"],
                "name": loc["name"],
                "short_name": loc["short_name"],
                "lat": center_lat,
                "lon": center_lon,
                "radius_nm": radius_nm,
                "airport_icao": ap_info["icao"],
                "airport_iata": ap_info["iata"],
                "airport_name": ap_info["name"],
            },
            "cache": {"cache_hit": False, "cache_ttl_sec": CACHE_TTL_SECONDS, "providers": PROVIDER_HEALTH},
            "operator_counts": operator_counts,
            "count": len(sim_flights),
            "flights": sim_flights,
        }

    prefer_provider = "adsb_fi" if sim_mode == "adsb_fi" else "auto"
    base_flights, source_name, cache_meta = await get_cached_or_live_flights(
        center_lat, center_lon, observer_elev, radius_nm, prefer_provider=prefer_provider, home_airport=ap_info
    )
    flights = list(base_flights)

    # Apply optional traffic filter before counting operators so counts match the airspace mode
    if filter_mode == "kgrr":
        flights = [f for f in flights if f["origin_iata"] == ap_iata or f["dest_iata"] == ap_iata]
    elif filter_mode == "low":
        flights = [f for f in flights if f["altitude_ft"] <= 15000]
    elif filter_mode == "commercial":
        flights = [f for f in flights if f["origin_iata"] != "---" and f["dest_iata"] != "---"]

    operator_counts = compute_operator_counts(flights)

    # Apply airline / operator group filter
    if airline_filter and airline_filter != "all":
        flights = [f for f in flights if f["operator_group"] == airline_filter]

    flights.sort(key=lambda x: x["priority_score"], reverse=True)

    return {
        "source": source_name,
        "timestamp": int(time.time()),
        "observer": {
            "id": loc["id"],
            "name": loc["name"],
            "short_name": loc["short_name"],
            "lat": center_lat,
            "lon": center_lon,
            "radius_nm": radius_nm,
            "airport_icao": ap_info["icao"],
            "airport_iata": ap_info["iata"],
            "airport_name": ap_info["name"],
        },
        "cache": cache_meta,
        "operator_counts": operator_counts,
        "count": len(flights),
        "flights": flights,
    }


@app.get("/api/weather")
async def get_airport_weather(station: str = Query("KGRR", description="ICAO airport weather station (e.g. KGRR, KDTW, KORD)")):
    """Fetch and parse live NOAA METAR for any ICAO airport station."""
    ap_info = await resolve_airport(station)
    icao_station = ap_info["icao"]
    now = time.time()
    cached = WEATHER_CACHE.get(icao_station)
    if cached and now - cached["timestamp"] < 300:
        return cached["data"]

    raw_metar = f"{icao_station} 111953Z 26010KT 10SM SCT055 12/04 A2998"
    obs_time = ""
    async with get_ipv4_client() as client:
        try:
            r = await client.get(
                f"https://tgftp.nws.noaa.gov/data/observations/metar/stations/{icao_station}.TXT",
                timeout=3.5,
            )
            if r.status_code == 200:
                lines = [ln.strip() for ln in r.text.strip().splitlines() if ln.strip()]
                if len(lines) >= 2:
                    obs_time = lines[0]
                    raw_metar = lines[1]
                elif lines:
                    raw_metar = lines[0]
        except Exception:
            pass

    # Lightweight METAR parser for flight category, wind, temp, altimeter
    parts = raw_metar.split()
    wind_str = "CALM"
    vis_str = "10SM"
    temp_c = None
    dew_c = None
    altimeter = "29.92"
    clouds: List[str] = []
    ceiling_ft = 99999
    vis_sm = 10.0

    for token in parts:
        if token.endswith("KT") and (len(token) >= 7):
            wdir = token[:3]
            wspd = token[3:5]
            wgst = ""
            if "G" in token:
                g_idx = token.index("G")
                wgst = f" G{token[g_idx+1:token.index('KT')]}"
            wind_str = f"{wdir}° @ {int(wspd) if wspd.isdigit() else wspd}{wgst} KT"
        elif token.endswith("SM"):
            vis_str = token
            try:
                if "/" in token:
                    vis_sm = 1.0
                else:
                    vis_sm = float(token.replace("SM", "").replace("P", ""))
            except ValueError:
                vis_sm = 10.0
        elif "/" in token and len(token) in (5, 6, 7) and not token.endswith("SM"):
            t_parts = token.split("/")
            if len(t_parts) == 2:
                def parse_t(s: str) -> Optional[int]:
                    s_clean = s.replace("M", "-")
                    try:
                        return int(s_clean)
                    except ValueError:
                        return None
                t_val = parse_t(t_parts[0])
                d_val = parse_t(t_parts[1])
                if t_val is not None:
                    temp_c = t_val
                    dew_c = d_val
        elif token.startswith("A") and len(token) == 5 and token[1:].isdigit():
            altimeter = f"{token[1:3]}.{token[3:5]}"
        elif token[:3] in ("FEW", "SCT", "BKN", "OVC", "VV0") and len(token) >= 6:
            clouds.append(token)
            if token[:3] in ("BKN", "OVC", "VV0") and token[3:6].isdigit():
                layer_ft = int(token[3:6]) * 100
                ceiling_ft = min(ceiling_ft, layer_ft)

    # Determine FAA Flight Category
    if ceiling_ft < 500 or vis_sm < 1.0:
        flight_category = "LIFR"
    elif ceiling_ft < 1000 or vis_sm < 3.0:
        flight_category = "IFR"
    elif ceiling_ft <= 3000 or vis_sm <= 5.0:
        flight_category = "MVFR"
    else:
        flight_category = "VFR"

    temp_f = int(round(temp_c * 9 / 5 + 32)) if temp_c is not None else 50

    weather_payload = {
        "station": icao_station,
        "name": ap_info["name"],
        "obs_time": obs_time,
        "raw_metar": raw_metar,
        "flight_category": flight_category,
        "wind": wind_str,
        "visibility": vis_str,
        "clouds": " ".join(clouds) if clouds else "CLR",
        "temp_c": temp_c,
        "temp_f": temp_f,
        "dew_c": dew_c,
        "altimeter_inhg": altimeter,
    }
    WEATHER_CACHE[icao_station] = {"timestamp": now, "data": weather_payload}
    return weather_payload


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def index():
    return FileResponse("static/index.html")


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
