"""MIC / OpenFIGI exchCode → Yahoo Finance suffix."""

OPENFIGI_EXCH_TO_SUFFIX: dict[str, str] = {
    "AS": ".AS",
    "PA": ".PA",
    "DE": ".DE",
    "L": ".L",
    "LN": ".L",
    "SW": ".SW",
    "BR": ".BR",
    "MI": ".MI",
    "HE": ".HE",
    "CO": ".CO",
    "ST": ".ST",
    "WA": ".WA",
}

MIC_TO_YAHOO_SUFFIX: dict[str, str] = {
    "XAMS": ".AS",
    "XPAR": ".PA",
    "XETR": ".DE",
    "XLON": ".L",
    "XSWX": ".SW",
    "XBRU": ".BR",
    "XMIL": ".MI",
    "XHEL": ".HE",
    "XCSE": ".CO",
    "XSTO": ".ST",
    "XWAR": ".WA",
}


YAHOO_SUFFIX_TO_MIC: dict[str, str] = {v.upper(): k for k, v in MIC_TO_YAHOO_SUFFIX.items()}


def yahoo_suffix_from_mic(mic: str) -> str | None:
    return MIC_TO_YAHOO_SUFFIX.get((mic or "").upper().strip())


def mic_from_yahoo_suffix(suffix: str) -> str | None:
    return YAHOO_SUFFIX_TO_MIC.get((suffix or "").upper().strip())


def yahoo_suffix_from_openfigi_exch(exch_code: str) -> str | None:
    return OPENFIGI_EXCH_TO_SUFFIX.get((exch_code or "").upper().strip())


def build_yahoo_ticker(*, ticker: str, exch_code: str = "", mic: str = "") -> str:
    base = (ticker or "").strip()
    if not base:
        return ""
    if "." in base:
        return base.upper()
    suffix = yahoo_suffix_from_openfigi_exch(exch_code) or yahoo_suffix_from_mic(mic)
    if suffix:
        return f"{base.upper()}{suffix}"
    return base.upper()
