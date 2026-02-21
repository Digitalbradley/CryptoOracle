"""Celestial/ephemeris computation engine using the ephem library.

Computes lunar phases, planetary retrogrades, aspects, eclipses,
and ingresses. Outputs celestial_score in range -1.0 to +1.0.
"""

import math
from datetime import date, datetime, timedelta, timezone

import ephem

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PLANETS = {
    "sun": ephem.Sun,
    "moon": ephem.Moon,
    "mercury": ephem.Mercury,
    "venus": ephem.Venus,
    "mars": ephem.Mars,
    "jupiter": ephem.Jupiter,
    "saturn": ephem.Saturn,
}

# Planets that can be retrograde (not Sun/Moon)
RETROGRADE_PLANETS = ["mercury", "venus", "mars", "jupiter", "saturn"]

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

ASPECT_DEFINITIONS = [
    {"name": "conjunction", "angle": 0, "orb": 8},
    {"name": "sextile", "angle": 60, "orb": 6},
    {"name": "square", "angle": 90, "orb": 8},
    {"name": "trine", "angle": 120, "orb": 8},
    {"name": "opposition", "angle": 180, "orb": 8},
]

LUNAR_PHASE_NAMES = [
    "new_moon",          # 0° - 45°
    "waxing_crescent",   # 45° - 90°
    "first_quarter",     # 90° - 135°
    "waxing_gibbous",    # 135° - 180°
    "full_moon",         # 180° - 225°
    "waning_gibbous",    # 225° - 270°
    "last_quarter",      # 270° - 315°
    "waning_crescent",   # 315° - 360°
]


def _to_ephem_date(d: date | datetime) -> ephem.Date:
    """Convert a Python date/datetime to ephem.Date."""
    if isinstance(d, datetime):
        return ephem.Date(d)
    return ephem.Date(datetime(d.year, d.month, d.day, 0, 0, 0))


def _deg(radians: float) -> float:
    """Convert radians to degrees."""
    return math.degrees(radians)


def _angular_distance(lon1: float, lon2: float) -> float:
    """Compute the minimum angular distance between two longitudes (0-360°)."""
    diff = abs(lon1 - lon2) % 360
    return min(diff, 360 - diff)


def _zodiac_sign(longitude_deg: float) -> str:
    """Get zodiac sign from ecliptic longitude in degrees."""
    idx = int(longitude_deg / 30) % 12
    return ZODIAC_SIGNS[idx]


# ---------------------------------------------------------------------------
# Lunar Phase
# ---------------------------------------------------------------------------

def compute_lunar_phase(d: date) -> dict:
    """Compute lunar phase information for a given date.

    Returns dict with: phase_angle, phase_name, illumination,
    days_to_next_new_moon, days_to_next_full_moon
    """
    ed = _to_ephem_date(d)
    moon = ephem.Moon(ed)

    # Phase angle: compute from sun-moon elongation
    sun = ephem.Sun(ed)
    moon_lon = _deg(float(ephem.Ecliptic(moon).lon))
    sun_lon = _deg(float(ephem.Ecliptic(sun).lon))
    phase_angle = (moon_lon - sun_lon) % 360

    # Phase name from angle
    phase_idx = int(phase_angle / 45) % 8
    phase_name = LUNAR_PHASE_NAMES[phase_idx]

    # Illumination (0.0 to 1.0)
    illumination = moon.phase / 100.0

    # Days to next new moon and full moon
    next_new = ephem.next_new_moon(ed)
    next_full = ephem.next_full_moon(ed)
    days_to_new = float(next_new - ed)
    days_to_full = float(next_full - ed)

    return {
        "phase_angle": round(phase_angle, 4),
        "phase_name": phase_name,
        "illumination": round(illumination, 4),
        "days_to_next_new_moon": round(days_to_new, 2),
        "days_to_next_full_moon": round(days_to_full, 2),
    }


# ---------------------------------------------------------------------------
# Eclipses
# ---------------------------------------------------------------------------

def check_eclipses(d: date) -> dict:
    """Check if there is a lunar or solar eclipse near this date.

    Returns dict with: is_lunar_eclipse, is_solar_eclipse
    """
    ed = _to_ephem_date(d)
    threshold = 1.0  # within 1 day

    is_lunar = False
    is_solar = False

    try:
        next_lunar = ephem.next_lunar_eclipse(ed)
        if abs(float(next_lunar - ed)) <= threshold:
            is_lunar = True
        prev_lunar = ephem.previous_lunar_eclipse(ed)
        if abs(float(ed - prev_lunar)) <= threshold:
            is_lunar = True
    except Exception:
        pass

    try:
        next_solar = ephem.next_solar_eclipse(ed)
        if abs(float(next_solar - ed)) <= threshold:
            is_solar = True
        prev_solar = ephem.previous_solar_eclipse(ed)
        if abs(float(ed - prev_solar)) <= threshold:
            is_solar = True
    except Exception:
        pass

    return {
        "is_lunar_eclipse": is_lunar,
        "is_solar_eclipse": is_solar,
    }


# ---------------------------------------------------------------------------
# Planetary Positions
# ---------------------------------------------------------------------------

def get_planet_positions(d: date) -> dict[str, float]:
    """Get ecliptic longitude (0-360°) for each planet.

    Returns dict mapping planet name to longitude in degrees.
    """
    ed = _to_ephem_date(d)
    positions = {}
    for name, PlanetClass in PLANETS.items():
        body = PlanetClass(ed)
        lon_deg = _deg(float(ephem.Ecliptic(body).lon))
        positions[name] = round(lon_deg, 4)
    return positions


# ---------------------------------------------------------------------------
# Retrogrades
# ---------------------------------------------------------------------------

def check_retrogrades(d: date) -> dict:
    """Check which planets are retrograde on a given date.

    Retrograde is detected by comparing the planet's ecliptic longitude
    on consecutive days — if it decreases, the planet is retrograde.

    Returns dict with individual booleans and retrograde_count.
    """
    ed = _to_ephem_date(d)
    ed_next = ephem.Date(ed + 1)  # next day

    retrogrades = {}
    count = 0

    for name in RETROGRADE_PLANETS:
        PlanetClass = PLANETS[name]
        body_today = PlanetClass(ed)
        body_tomorrow = PlanetClass(ed_next)

        lon_today = _deg(float(ephem.Ecliptic(body_today).lon))
        lon_tomorrow = _deg(float(ephem.Ecliptic(body_tomorrow).lon))

        # Handle wrap-around at 360°/0°
        diff = lon_tomorrow - lon_today
        if diff > 180:
            diff -= 360
        elif diff < -180:
            diff += 360

        is_retro = diff < 0
        retrogrades[f"{name}_retrograde"] = is_retro
        if is_retro:
            count += 1

    retrogrades["retrograde_count"] = count
    return retrogrades


# ---------------------------------------------------------------------------
# Aspects
# ---------------------------------------------------------------------------

def compute_aspects(d: date) -> list[dict]:
    """Compute active aspects between planet pairs.

    Returns list of dicts with: planet1, planet2, aspect_name, exact_angle, orb_distance
    """
    positions = get_planet_positions(d)
    planet_names = list(positions.keys())
    aspects = []

    for i in range(len(planet_names)):
        for j in range(i + 1, len(planet_names)):
            p1 = planet_names[i]
            p2 = planet_names[j]
            dist = _angular_distance(positions[p1], positions[p2])

            for aspect_def in ASPECT_DEFINITIONS:
                orb_distance = abs(dist - aspect_def["angle"])
                if orb_distance <= aspect_def["orb"]:
                    aspects.append({
                        "planet1": p1,
                        "planet2": p2,
                        "aspect": aspect_def["name"],
                        "exact_angle": aspect_def["angle"],
                        "orb_distance": round(orb_distance, 2),
                    })
                    break  # only one aspect per pair

    return aspects


# ---------------------------------------------------------------------------
# Ingresses
# ---------------------------------------------------------------------------

def compute_ingresses(d: date) -> list[dict]:
    """Detect planets changing zodiac signs on this date.

    Returns list of dicts with: planet, from_sign, to_sign
    """
    positions_today = get_planet_positions(d)
    yesterday = d - timedelta(days=1) if isinstance(d, date) else d - timedelta(days=1)
    positions_yesterday = get_planet_positions(yesterday)

    ingresses = []
    for name in PLANETS:
        sign_today = _zodiac_sign(positions_today[name])
        sign_yesterday = _zodiac_sign(positions_yesterday[name])
        if sign_today != sign_yesterday:
            ingresses.append({
                "planet": name,
                "from_sign": sign_yesterday,
                "to_sign": sign_today,
            })

    return ingresses


# ---------------------------------------------------------------------------
# Composite Celestial State
# ---------------------------------------------------------------------------

def compute_celestial_state(d: date) -> dict:
    """Compute the full celestial state for a given date.

    Returns a dict matching all celestial_state table columns.
    """
    lunar = compute_lunar_phase(d)
    eclipses = check_eclipses(d)
    positions = get_planet_positions(d)
    retrogrades = check_retrogrades(d)
    aspects = compute_aspects(d)
    ingresses = compute_ingresses(d)

    state = {
        "timestamp": datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=timezone.utc)
        if isinstance(d, date) and not isinstance(d, datetime)
        else d,
        # Lunar
        "lunar_phase_angle": lunar["phase_angle"],
        "lunar_phase_name": lunar["phase_name"],
        "lunar_illumination": lunar["illumination"],
        "days_to_next_new_moon": lunar["days_to_next_new_moon"],
        "days_to_next_full_moon": lunar["days_to_next_full_moon"],
        "is_lunar_eclipse": eclipses["is_lunar_eclipse"],
        "is_solar_eclipse": eclipses["is_solar_eclipse"],
        # Retrogrades
        "mercury_retrograde": retrogrades["mercury_retrograde"],
        "venus_retrograde": retrogrades["venus_retrograde"],
        "mars_retrograde": retrogrades["mars_retrograde"],
        "jupiter_retrograde": retrogrades["jupiter_retrograde"],
        "saturn_retrograde": retrogrades["saturn_retrograde"],
        "retrograde_count": retrogrades["retrograde_count"],
        # Positions
        "sun_longitude": positions["sun"],
        "moon_longitude": positions["moon"],
        "mercury_longitude": positions["mercury"],
        "venus_longitude": positions["venus"],
        "mars_longitude": positions["mars"],
        "jupiter_longitude": positions["jupiter"],
        "saturn_longitude": positions["saturn"],
        # Aspects & Ingresses
        "active_aspects": aspects,
        "ingresses": ingresses,
    }

    # Compute score
    state["celestial_score"] = compute_celestial_score(state)

    return state


# ---------------------------------------------------------------------------
# Celestial Score
# ---------------------------------------------------------------------------

def compute_celestial_score(state: dict) -> float:
    """Compute celestial_score from state, normalized to [-1.0, +1.0].

    Score rules (from PRD):
    - New moon: +0.2
    - Full moon: -0.2
    - Mercury retrograde: -0.3
    - 3+ retrogrades: -0.5
    - Eclipse within 3 days: -0.4
    - Saturn-Jupiter conjunction: ±0.4
    - Mars square Saturn: -0.3
    """
    score = 0.0

    # Lunar phase
    phase_name = state.get("lunar_phase_name", "")
    if phase_name == "new_moon":
        score += 0.2
    elif phase_name == "full_moon":
        score -= 0.2

    # Mercury retrograde
    if state.get("mercury_retrograde"):
        score -= 0.3

    # Multiple retrogrades
    retro_count = state.get("retrograde_count", 0)
    if retro_count >= 3:
        score -= 0.5

    # Eclipses
    if state.get("is_lunar_eclipse") or state.get("is_solar_eclipse"):
        score -= 0.4

    # Check aspects for specific patterns
    aspects = state.get("active_aspects", [])
    for asp in aspects:
        p1, p2 = asp.get("planet1", ""), asp.get("planet2", "")
        aspect_name = asp.get("aspect", "")
        pair = frozenset([p1, p2])

        # Saturn-Jupiter conjunction
        if pair == frozenset(["saturn", "jupiter"]) and aspect_name == "conjunction":
            score += 0.4  # major cycle shift (positive for new era)

        # Mars square Saturn
        if pair == frozenset(["mars", "saturn"]) and aspect_name == "square":
            score -= 0.3

    # Clamp to [-1.0, +1.0]
    return round(max(-1.0, min(1.0, score)), 4)
