"""Macro Liquidity signal computation engine (Layer 7).

Implements 5 sub-signals per brief Section 3.2:
  1. Oil signal        (0.15 weight)
  2. Dollar signal     (0.20 weight)
  3. Treasury signal   (0.20 weight)
  4. Liquidity signal  (0.25 weight)
  5. Carry trade signal(0.20 weight)

Composite: macro_score = Σ(weight × sub_signal), clamped [-1, +1].
Carry stress: continuous 0-1 score.
Regime: risk_on, risk_off, tightening, easing, neutral, carry_unwind.
"""

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select, func, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.macro_liquidity import (
    CarryTradeData,
    LiquidityData,
    MacroLiquiditySignal,
    MacroPrices,
    OilData,
    RateData,
)

logger = logging.getLogger(__name__)

# Internal sub-signal weights (brief Section 3.3)
SUB_WEIGHTS = {
    "oil": 0.15,
    "dollar": 0.20,
    "treasury": 0.20,
    "liquidity": 0.25,
    "carry_trade": 0.20,
}


def _f(val) -> float | None:
    """Convert Decimal/None to float."""
    if val is None:
        return None
    return float(val)


# ---------- Sub-signal 1: Oil ----------


def compute_oil_score(db: Session) -> tuple[float, dict]:
    """Oil signal: WTI momentum + inventory pressure.

    Returns (score, detail_dict).
    Score range: -1.0 to +1.0.
    """
    # Get latest and 30-day-ago WTI
    latest = db.execute(
        select(OilData)
        .where(OilData.wti_price.isnot(None))
        .order_by(OilData.timestamp.desc())
        .limit(1)
    ).scalar_one_or_none()

    if not latest or latest.wti_price is None:
        return 0.0, {"reason": "no_data"}

    wti = float(latest.wti_price)
    ts_30d = latest.timestamp - timedelta(days=30)

    prior = db.execute(
        select(OilData)
        .where(OilData.wti_price.isnot(None), OilData.timestamp <= ts_30d)
        .order_by(OilData.timestamp.desc())
        .limit(1)
    ).scalar_one_or_none()

    score = 0.0
    detail = {"wti": wti}

    if prior and prior.wti_price:
        pct_30d = (wti - float(prior.wti_price)) / float(prior.wti_price) * 100
        detail["pct_30d"] = round(pct_30d, 2)

        # Brief Section 3.2: Oil rising >15% in 30d → -0.5 to -0.8
        if pct_30d > 15:
            score = -0.5 - min(0.3, (pct_30d - 15) / 30)
        elif pct_30d > 5:
            score = -0.2 - (pct_30d - 5) / 50
        # Oil crashing >20% → -0.3 short-term
        elif pct_30d < -20:
            score = -0.3
        elif pct_30d < -10:
            score = -0.1
        # Stable → +0.1 to +0.2
        elif abs(pct_30d) < 5:
            score = 0.15
        else:
            score = 0.0

    # Inventory pressure: large builds = bearish for oil = good for crypto
    inv_row = db.execute(
        select(OilData)
        .where(OilData.inventory_change.isnot(None))
        .order_by(OilData.timestamp.desc())
        .limit(1)
    ).scalar_one_or_none()

    if inv_row and inv_row.inventory_change is not None:
        inv_change = float(inv_row.inventory_change)
        detail["inventory_change"] = inv_change
        # Large inventory build → slightly positive (lower oil pressure)
        if inv_change > 5000:
            score += 0.1
        elif inv_change < -5000:
            score -= 0.1

    score = max(-1.0, min(1.0, round(score, 4)))
    detail["score"] = score
    return score, detail


# ---------- Sub-signal 2: Dollar / DXY ----------


def compute_dollar_score(db: Session) -> tuple[float, dict]:
    """Dollar signal: DXY level + momentum.

    Returns (score, detail_dict).
    """
    latest = db.execute(
        select(MacroPrices)
        .where(MacroPrices.dxy_index.isnot(None))
        .order_by(MacroPrices.timestamp.desc())
        .limit(1)
    ).scalar_one_or_none()

    if not latest or latest.dxy_index is None:
        return 0.0, {"reason": "no_data"}

    dxy = float(latest.dxy_index)
    detail = {"dxy": dxy}

    # Brief Section 3.2: DXY levels
    # Note: DTWEXBGS (trade-weighted) has different scale than classic DXY
    # Classic DXY ~100-115 range; DTWEXBGS ~110-130 range
    # We normalize: treat >125 as strong (like DXY>108), <115 as weak (like DXY<100)

    # Level-based score
    if dxy > 130:
        score = -0.7
    elif dxy > 125:
        score = -0.4 - (dxy - 125) * 0.06
    elif dxy > 120:
        score = -0.2
    elif dxy < 110:
        score = 0.5
    elif dxy < 115:
        score = 0.3
    else:
        score = 0.0

    # Momentum: check 20-day change
    ts_20d = latest.timestamp - timedelta(days=20)
    prior = db.execute(
        select(MacroPrices)
        .where(MacroPrices.dxy_index.isnot(None), MacroPrices.timestamp <= ts_20d)
        .order_by(MacroPrices.timestamp.desc())
        .limit(1)
    ).scalar_one_or_none()

    if prior and prior.dxy_index:
        pct = (dxy - float(prior.dxy_index)) / float(prior.dxy_index) * 100
        detail["pct_20d"] = round(pct, 2)
        # Rising dollar = bearish for crypto
        if pct > 2:
            score -= 0.2
        elif pct > 1:
            score -= 0.1
        elif pct < -2:
            score += 0.2
        elif pct < -1:
            score += 0.1

    score = max(-1.0, min(1.0, round(score, 4)))
    detail["score"] = score
    return score, detail


# ---------- Sub-signal 3: Treasury Yields ----------


def compute_treasury_score(db: Session) -> tuple[float, dict]:
    """Treasury yield signal: 10Y level/momentum, curve shape, real yields.

    Returns (score, detail_dict).
    """
    latest = db.execute(
        select(RateData)
        .where(RateData.dgs10.isnot(None))
        .order_by(RateData.timestamp.desc())
        .limit(1)
    ).scalar_one_or_none()

    if not latest:
        return 0.0, {"reason": "no_data"}

    score = 0.0
    detail = {}

    dgs10 = _f(latest.dgs10)
    dgs2 = _f(latest.dgs2)
    curve = _f(latest.yield_curve_2s10s)
    dfii10 = _f(latest.dfii10)

    if dgs10 is not None:
        detail["dgs10"] = dgs10

        # 10Y momentum
        ts_20d = latest.timestamp - timedelta(days=20)
        prior = db.execute(
            select(RateData)
            .where(RateData.dgs10.isnot(None), RateData.timestamp <= ts_20d)
            .order_by(RateData.timestamp.desc())
            .limit(1)
        ).scalar_one_or_none()

        if prior and prior.dgs10:
            change = dgs10 - float(prior.dgs10)
            detail["dgs10_change_20d"] = round(change, 4)
            # Brief: 10Y rising rapidly → -0.3 to -0.6
            if change > 0.5:
                score -= 0.6
            elif change > 0.3:
                score -= 0.4
            elif change > 0.1:
                score -= 0.2
            # Falling → +0.2 to +0.4
            elif change < -0.3:
                score += 0.4
            elif change < -0.1:
                score += 0.2

    # Yield curve
    if curve is not None:
        detail["yield_curve_2s10s"] = curve
        # Brief: inverting further → -0.2; steepening from inversion → +0.3
        if curve < -0.5:
            score -= 0.2
        elif curve < 0:
            score -= 0.1
        elif curve > 0.5:
            score += 0.3
        elif curve > 0:
            score += 0.1

    # Real yields (TIPS)
    if dfii10 is not None:
        detail["real_yield_10y"] = dfii10
        # Brief: real yields >2.5% → -0.5
        if dfii10 > 2.5:
            score -= 0.3
        elif dfii10 > 2.0:
            score -= 0.15
        elif dfii10 < 0.5:
            score += 0.2
        elif dfii10 < 1.0:
            score += 0.1

    score = max(-1.0, min(1.0, round(score, 4)))
    detail["score"] = score
    return score, detail


# ---------- Sub-signal 4: Global M2 Liquidity ----------


def compute_liquidity_score(db: Session) -> tuple[float, dict]:
    """Global M2 / Fed liquidity signal.

    Uses ~90-day lag for BTC correlation per brief Section 3.2.
    Returns (score, detail_dict).
    """
    M2_LAG_DAYS = 90  # Configurable, brief says 10-12 weeks

    # Latest liquidity data
    latest = db.execute(
        select(LiquidityData)
        .where(LiquidityData.m2_supply.isnot(None))
        .order_by(LiquidityData.timestamp.desc())
        .limit(1)
    ).scalar_one_or_none()

    if not latest or latest.m2_supply is None:
        return 0.0, {"reason": "no_data"}

    m2_now = float(latest.m2_supply)
    detail = {"m2_supply": m2_now}

    # YoY change for M2
    ts_1y = latest.timestamp - timedelta(days=365)
    prior_1y = db.execute(
        select(LiquidityData)
        .where(LiquidityData.m2_supply.isnot(None), LiquidityData.timestamp <= ts_1y)
        .order_by(LiquidityData.timestamp.desc())
        .limit(1)
    ).scalar_one_or_none()

    score = 0.0
    m2_yoy = None
    if prior_1y and prior_1y.m2_supply:
        m2_yoy = (m2_now - float(prior_1y.m2_supply)) / float(prior_1y.m2_supply) * 100
        detail["m2_yoy_pct"] = round(m2_yoy, 2)

        # Brief: M2 expanding YoY + accelerating → +0.4 to +0.8
        if m2_yoy > 5:
            score = 0.8
        elif m2_yoy > 2:
            score = 0.4 + (m2_yoy - 2) / 7.5
        elif m2_yoy > 0:
            score = 0.2
        # Contracting → -0.4 to -0.8
        elif m2_yoy < -3:
            score = -0.8
        elif m2_yoy < -1:
            score = -0.4 - (abs(m2_yoy) - 1) / 5
        elif m2_yoy < 0:
            score = -0.2

    # Net liquidity component
    net_liq = _f(latest.net_liquidity)
    if net_liq is not None:
        detail["net_liquidity"] = net_liq

        # Check net liquidity trend (vs 3 months ago)
        ts_3m = latest.timestamp - timedelta(days=90)
        prior_3m = db.execute(
            select(LiquidityData)
            .where(LiquidityData.net_liquidity.isnot(None), LiquidityData.timestamp <= ts_3m)
            .order_by(LiquidityData.timestamp.desc())
            .limit(1)
        ).scalar_one_or_none()

        if prior_3m and prior_3m.net_liquidity:
            net_change = float(latest.net_liquidity) - float(prior_3m.net_liquidity)
            # Expanding → bullish, contracting → bearish
            if net_change > 0:
                score += 0.15
            else:
                score -= 0.15

    score = max(-1.0, min(1.0, round(score, 4)))
    detail["score"] = score
    return score, detail


# ---------- Sub-signal 5: Carry Trade Stress ----------


def compute_carry_trade_score(db: Session) -> tuple[float, float, dict]:
    """Carry trade stress signal.

    Returns (score, carry_stress, detail_dict).
    score: -1.0 to +1.0 (for composite)
    carry_stress: 0.0 to 1.0 (continuous stress level)
    """
    latest = db.execute(
        select(CarryTradeData)
        .where(CarryTradeData.usdjpy.isnot(None))
        .order_by(CarryTradeData.timestamp.desc())
        .limit(1)
    ).scalar_one_or_none()

    if not latest or latest.usdjpy is None:
        return 0.0, 0.0, {"reason": "no_data"}

    usdjpy = float(latest.usdjpy)
    detail = {"usdjpy": usdjpy}

    # --- Forex stress component ---
    forex_stress = 0.0
    sma_20 = _f(latest.usdjpy_sma_20)
    atr_14 = _f(latest.usdjpy_atr_14)

    if sma_20 and atr_14 and atr_14 > 0:
        # Yen strengthening vs SMA-20, normalized by ATR-14
        deviation = (sma_20 - usdjpy) / atr_14
        forex_stress = max(0.0, min(1.0, deviation / 3.0))
        detail["forex_stress"] = round(forex_stress, 4)

    # Weekly change check
    ts_7d = latest.timestamp - timedelta(days=7)
    prior_7d = db.execute(
        select(CarryTradeData)
        .where(CarryTradeData.usdjpy.isnot(None), CarryTradeData.timestamp <= ts_7d)
        .order_by(CarryTradeData.timestamp.desc())
        .limit(1)
    ).scalar_one_or_none()

    weekly_pct = 0.0
    if prior_7d and prior_7d.usdjpy:
        weekly_pct = (usdjpy - float(prior_7d.usdjpy)) / float(prior_7d.usdjpy) * 100
        detail["usdjpy_weekly_pct"] = round(weekly_pct, 2)

    # --- VIX stress component ---
    vix_stress = 0.0
    vix_row = db.execute(
        select(MacroPrices)
        .where(MacroPrices.vix.isnot(None))
        .order_by(MacroPrices.timestamp.desc())
        .limit(1)
    ).scalar_one_or_none()

    if vix_row and vix_row.vix:
        vix = float(vix_row.vix)
        detail["vix"] = vix
        # VIX > 30 → high stress
        if vix > 35:
            vix_stress = 1.0
        elif vix > 30:
            vix_stress = 0.7
        elif vix > 25:
            vix_stress = 0.4
        elif vix > 20:
            vix_stress = 0.15
        detail["vix_stress"] = round(vix_stress, 4)

    # --- Positioning stress component ---
    positioning_stress = 0.0
    zscore = _f(latest.jpy_positioning_zscore)
    if zscore is not None:
        detail["jpy_zscore"] = zscore
        # Extreme net short yen → crowded trade risk
        if zscore < -2.0:
            positioning_stress = 0.8
        elif zscore < -1.5:
            positioning_stress = 0.5
        elif zscore < -1.0:
            positioning_stress = 0.3
        detail["positioning_stress"] = round(positioning_stress, 4)

    # --- Continuous carry stress (0-1) ---
    # Brief: stress = 0.40 * forex + 0.30 * vix + 0.30 * positioning
    carry_stress = (
        0.40 * forex_stress + 0.30 * vix_stress + 0.30 * positioning_stress
    )
    carry_stress = max(0.0, min(1.0, round(carry_stress, 4)))
    detail["carry_stress"] = carry_stress

    # --- Score for composite (-1 to +1) ---
    score = 0.0

    # Brief Section 3.2 thresholds
    # USD/JPY dropping >5%/wk → -0.8
    if weekly_pct < -5:
        score = -0.8
    # USD/JPY dropping >2%/wk → -0.4
    elif weekly_pct < -2:
        score = -0.4
    # VIX>30 + yen weakening → -0.9
    elif vix_stress > 0.5 and forex_stress > 0.3:
        score = -0.9
    # Stable + wide differential → +0.2
    elif carry_stress < 0.2:
        score = 0.2
    elif carry_stress < 0.4:
        score = 0.0
    elif carry_stress < 0.6:
        score = -0.2
    elif carry_stress < 0.8:
        score = -0.5
    else:
        score = -0.8

    # CFTC extreme adds -0.2 (brief)
    if positioning_stress > 0.5:
        score -= 0.2

    score = max(-1.0, min(1.0, round(score, 4)))
    detail["score"] = score
    return score, carry_stress, detail


# ---------- Regime classification ----------


def classify_regime(
    liquidity_score: float,
    treasury_score: float,
    carry_stress: float,
    dollar_score: float,
) -> tuple[str, float]:
    """Classify macro regime.

    Returns (regime_name, confidence).
    Regimes: risk_on, risk_off, tightening, easing, neutral, carry_unwind.
    """
    # Carry unwind takes priority
    if carry_stress > 0.7:
        return "carry_unwind", min(1.0, carry_stress)

    # Tightening: rates rising, dollar strong, liquidity contracting
    tightening_signals = sum([
        treasury_score < -0.3,
        dollar_score < -0.3,
        liquidity_score < -0.3,
    ])
    if tightening_signals >= 2:
        confidence = min(1.0, abs(treasury_score + dollar_score + liquidity_score) / 3)
        return "tightening", round(confidence, 4)

    # Easing: rates falling, liquidity expanding
    easing_signals = sum([
        treasury_score > 0.3,
        liquidity_score > 0.3,
        dollar_score > 0.2,
    ])
    if easing_signals >= 2:
        confidence = min(1.0, (treasury_score + liquidity_score + dollar_score) / 3)
        return "easing", round(confidence, 4)

    # Risk off: high VIX / carry stress + bearish scores
    if carry_stress > 0.4 and (treasury_score < 0 or dollar_score < 0):
        return "risk_off", round(carry_stress, 4)

    # Risk on: everything positive
    if liquidity_score > 0.2 and treasury_score > 0 and dollar_score > 0:
        avg = (liquidity_score + treasury_score + dollar_score) / 3
        return "risk_on", round(min(1.0, avg), 4)

    return "neutral", 0.5


# ---------- Composite + Store ----------


def compute_macro_signal(db: Session) -> dict:
    """Compute all 5 sub-signals, composite, regime, and store.

    Returns full signal dict.
    """
    # Compute all sub-signals
    oil_score, oil_detail = compute_oil_score(db)
    dollar_score, dollar_detail = compute_dollar_score(db)
    treasury_score, treasury_detail = compute_treasury_score(db)
    liquidity_score, liquidity_detail = compute_liquidity_score(db)
    carry_score, carry_stress, carry_detail = compute_carry_trade_score(db)

    # Composite (brief Section 3.3)
    macro_score = (
        SUB_WEIGHTS["oil"] * oil_score
        + SUB_WEIGHTS["dollar"] * dollar_score
        + SUB_WEIGHTS["treasury"] * treasury_score
        + SUB_WEIGHTS["liquidity"] * liquidity_score
        + SUB_WEIGHTS["carry_trade"] * carry_score
    )
    macro_score = max(-1.0, min(1.0, round(macro_score, 4)))

    # Regime
    regime, regime_confidence = classify_regime(
        liquidity_score, treasury_score, carry_stress, dollar_score
    )

    # Snapshot data points for display
    dxy_val = dollar_detail.get("dxy")
    vix_val = carry_detail.get("vix")
    curve_val = treasury_detail.get("yield_curve_2s10s")
    wti_val = oil_detail.get("wti")
    usdjpy_val = carry_detail.get("usdjpy")
    m2_yoy = liquidity_detail.get("m2_yoy_pct")
    net_liq = liquidity_detail.get("net_liquidity")

    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)

    row = {
        "timestamp": now,
        "liquidity_score": Decimal(str(liquidity_score)),
        "treasury_score": Decimal(str(treasury_score)),
        "dollar_score": Decimal(str(dollar_score)),
        "oil_score": Decimal(str(oil_score)),
        "carry_trade_score": Decimal(str(carry_score)),
        "macro_score": Decimal(str(macro_score)),
        "regime": regime,
        "regime_confidence": Decimal(str(regime_confidence)),
        "net_liquidity": Decimal(str(net_liq)) if net_liq else None,
        "m2_yoy_pct": Decimal(str(m2_yoy)) if m2_yoy else None,
        "yield_curve_2s10s": Decimal(str(curve_val)) if curve_val else None,
        "dxy_value": Decimal(str(dxy_val)) if dxy_val else None,
        "vix_value": Decimal(str(vix_val)) if vix_val else None,
        "wti_price": Decimal(str(wti_val)) if wti_val else None,
        "usdjpy_value": Decimal(str(usdjpy_val)) if usdjpy_val else None,
        "carry_stress": Decimal(str(carry_stress)),
        "sub_signals": {
            "oil": oil_detail,
            "dollar": dollar_detail,
            "treasury": treasury_detail,
            "liquidity": liquidity_detail,
            "carry_trade": carry_detail,
        },
    }

    stmt = pg_insert(MacroLiquiditySignal).values([row])
    update_cols = {k: getattr(stmt.excluded, k) for k in row if k != "timestamp"}
    stmt = stmt.on_conflict_do_update(
        index_elements=["timestamp"],
        set_=update_cols,
    )
    db.execute(stmt)
    db.commit()

    logger.info(
        "Macro signal computed: score=%.4f regime=%s carry_stress=%.4f",
        macro_score,
        regime,
        carry_stress,
    )

    return {
        "timestamp": now.isoformat(),
        "oil_score": oil_score,
        "dollar_score": dollar_score,
        "treasury_score": treasury_score,
        "liquidity_score": liquidity_score,
        "carry_trade_score": carry_score,
        "macro_score": macro_score,
        "regime": regime,
        "regime_confidence": regime_confidence,
        "carry_stress": carry_stress,
        "dxy_value": dxy_val,
        "vix_value": vix_val,
        "yield_curve_2s10s": curve_val,
        "wti_price": wti_val,
        "usdjpy_value": usdjpy_val,
        "m2_yoy_pct": m2_yoy,
        "net_liquidity": net_liq,
        "sub_signals": {
            "oil": oil_detail,
            "dollar": dollar_detail,
            "treasury": treasury_detail,
            "liquidity": liquidity_detail,
            "carry_trade": carry_detail,
        },
    }
