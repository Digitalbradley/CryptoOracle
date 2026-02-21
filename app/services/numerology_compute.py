"""Numerology and Gematria computation engine.

Pure algorithmic computations — no external APIs or DB access.
Handles date numerology, multiple gematria ciphers, and price significance.
"""

import math
from datetime import date

# ---------------------------------------------------------------------------
# Date Numerology
# ---------------------------------------------------------------------------

def date_digit_sum(d: date) -> int:
    """Raw digit sum of a date's digits (YYYYMMDD).

    Example: 2026-02-20 -> 2+0+2+6+0+2+2+0 = 14
    """
    digits = d.strftime("%Y%m%d")
    return sum(int(ch) for ch in digits)


def reduce_to_digit(n: int) -> int:
    """Reduce a number to a single digit (1-9), preserving master numbers 11, 22, 33."""
    while n > 9 and n not in (11, 22, 33):
        n = sum(int(d) for d in str(n))
    return n


def universal_day_number(d: date) -> int:
    """Reduce a date to its universal day number.

    Example: 2026-02-20 -> digit sum 14 -> 1+4 = 5
    Preserves master numbers: 11, 22, 33.
    """
    return reduce_to_digit(date_digit_sum(d))


def is_master_number_date(d: date) -> bool:
    """Check if date reduces to a master number (11, 22, or 33)."""
    raw = date_digit_sum(d)
    reduced = reduce_to_digit(raw)
    return reduced in (11, 22, 33)


def get_master_number_value(d: date) -> int | None:
    """Return the master number value (11, 22, 33) or None."""
    reduced = universal_day_number(d)
    return reduced if reduced in (11, 22, 33) else None


# ---------------------------------------------------------------------------
# Gematria Calculator
# ---------------------------------------------------------------------------

# Jewish/Hebrew gematria values for English letters (traditional mapping)
_JEWISH_VALUES = {
    'a': 1, 'b': 2, 'c': 3, 'd': 4, 'e': 5, 'f': 6, 'g': 7, 'h': 8,
    'i': 9, 'j': 600, 'k': 10, 'l': 20, 'm': 30, 'n': 40, 'o': 50,
    'p': 60, 'q': 70, 'r': 80, 's': 90, 't': 100, 'u': 200, 'v': 700,
    'w': 900, 'x': 300, 'y': 400, 'z': 500,
}


class GematriaCalculator:
    """Multiple cipher gematria calculator.

    Ciphers:
    - english_ordinal: A=1, B=2, ... Z=26
    - full_reduction: A=1, B=2, ... I=9, J=1, K=2, ... (reduced to 1-9)
    - reverse_ordinal: A=26, B=25, ... Z=1
    - reverse_reduction: reverse ordinal reduced to 1-9
    - jewish_gematria: traditional Hebrew-to-English mapping
    - english_gematria: A=6, B=12, ... (ordinal × 6)
    """

    def calculate(self, text: str, cipher: str = "english_ordinal") -> int:
        """Calculate gematria value for text using specified cipher."""
        ciphers = {
            "english_ordinal": self._english_ordinal,
            "full_reduction": self._full_reduction,
            "reverse_ordinal": self._reverse_ordinal,
            "reverse_reduction": self._reverse_reduction,
            "jewish_gematria": self._jewish_gematria,
            "english_gematria": self._english_gematria,
        }
        func = ciphers.get(cipher)
        if func is None:
            raise ValueError(f"Unknown cipher: {cipher}. Valid: {list(ciphers)}")
        return func(text)

    def calculate_all_ciphers(self, text: str) -> dict:
        """Calculate gematria value across all ciphers.

        Returns dict with cipher names as keys and int values.
        """
        return {
            "english_ordinal": self._english_ordinal(text),
            "full_reduction": self._full_reduction(text),
            "reverse_ordinal": self._reverse_ordinal(text),
            "reverse_reduction": self._reverse_reduction(text),
            "jewish_gematria": self._jewish_gematria(text),
            "english_gematria": self._english_gematria(text),
        }

    def reduce_to_digit(self, number: int) -> int:
        """Reduce a number to a single digit, preserving master numbers."""
        return reduce_to_digit(number)

    def analyze_price_level(self, price: float) -> dict:
        """Analyze a price level for numerological properties.

        Returns dict with digit_sum, reduced, is_master, is_prime, contains_47, etc.
        """
        price_str = str(int(round(price)))
        digit_sum = sum(int(d) for d in price_str if d.isdigit())
        reduced = reduce_to_digit(digit_sum)
        price_int = int(round(price))

        return {
            "price": price,
            "price_rounded": price_int,
            "digit_sum": digit_sum,
            "reduced": reduced,
            "is_master_number": reduced in (11, 22, 33),
            "is_prime": _is_prime(price_int),
            "contains_47": "47" in price_str,
            "significant_numbers_found": _find_significant_numbers_in(price_str),
        }

    # --- Cipher implementations ---

    def _english_ordinal(self, text: str) -> int:
        """A=1, B=2, ... Z=26"""
        return sum(ord(c.lower()) - 96 for c in text if c.isalpha())

    def _full_reduction(self, text: str) -> int:
        """Each letter reduced to 1-9: A=1...I=9, J=1...R=9, S=1...Z=8"""
        total = 0
        for c in text:
            if c.isalpha():
                val = ord(c.lower()) - 96  # 1-26
                total += reduce_to_digit(val)
        return total

    def _reverse_ordinal(self, text: str) -> int:
        """A=26, B=25, ... Z=1"""
        return sum(27 - (ord(c.lower()) - 96) for c in text if c.isalpha())

    def _reverse_reduction(self, text: str) -> int:
        """Reverse ordinal values reduced to 1-9"""
        total = 0
        for c in text:
            if c.isalpha():
                val = 27 - (ord(c.lower()) - 96)
                total += reduce_to_digit(val)
        return total

    def _jewish_gematria(self, text: str) -> int:
        """Traditional Jewish/Hebrew gematria mapping for English letters."""
        return sum(_JEWISH_VALUES.get(c.lower(), 0) for c in text if c.isalpha())

    def _english_gematria(self, text: str) -> int:
        """English Gematria: ordinal × 6 (A=6, B=12, ... Z=156)"""
        return sum((ord(c.lower()) - 96) * 6 for c in text if c.isalpha())


# ---------------------------------------------------------------------------
# Price Significance Analysis
# ---------------------------------------------------------------------------

_DEFAULT_WATCHED_NUMBERS = [47, 11, 22, 33, 7, 9, 13]


def analyze_price_for_significance(
    price: float,
    watched_numbers: list[int] | None = None,
) -> dict:
    """Check if a price level contains or relates to significant numbers.

    Checks:
    - Does the price string contain any watched numbers?
    - Does the digit sum reduce to a watched number?
    - Is the price at a round number reducing to a key digit?
    """
    if watched_numbers is None:
        watched_numbers = _DEFAULT_WATCHED_NUMBERS

    price_str = str(int(round(price)))
    digit_sum = sum(int(d) for d in price_str if d.isdigit())
    reduced = reduce_to_digit(digit_sum)

    contained = [n for n in watched_numbers if str(n) in price_str]
    reduces_to_watched = reduced in watched_numbers

    return {
        "price": price,
        "digit_sum": digit_sum,
        "reduced_digit": reduced,
        "contains_numbers": contained,
        "reduces_to_watched": reduces_to_watched,
        "is_significant": bool(contained) or reduces_to_watched,
        "significance_level": len(contained) + (1 if reduces_to_watched else 0),
    }


# ---------------------------------------------------------------------------
# Numerology Score
# ---------------------------------------------------------------------------

def compute_numerology_score(
    universal_number: int,
    is_master: bool,
    cycle_alignments: list[dict] | None = None,
) -> float:
    """Compute numerology_score normalized to [-1.0, +1.0].

    Rules:
    - Master number date (11, 22, 33): +0.2
    - 47-day cycle alignment: -0.4
    - Multiple cycle confluence: amplified per overlap
    """
    score = 0.0

    # Master number bonus
    if is_master:
        score += 0.2

    # Cycle alignments
    if cycle_alignments:
        for alignment in cycle_alignments:
            cycle_name = alignment.get("name", "")
            if "47" in cycle_name:
                score -= 0.4  # 47-day crash cycle is bearish
            else:
                score -= 0.1  # other cycles: mild bearish signal

    return round(max(-1.0, min(1.0, score)), 4)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_prime(n: int) -> bool:
    """Check if a positive integer is prime."""
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def _find_significant_numbers_in(price_str: str) -> list[int]:
    """Find which watched numbers appear in the price string."""
    return [n for n in _DEFAULT_WATCHED_NUMBERS if str(n) in price_str]
