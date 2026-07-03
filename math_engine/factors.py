"""Fama-French 3-factor data: Ken French's Data Library, with parsing.

The three factors (Mkt-RF, SMB, HML) plus the risk-free rate used to build
them come from Ken French's publicly hosted data library at Dartmouth --
free, no API key, updated monthly. There's no JSON API for it; the file is
a CSV bundled in a zip, with descriptive text above the header and an
annual-data block appended below the monthly one in the same file. We fetch
the zip, then parse only the monthly block.

If the fetch or parse fails, callers should fall back to the historical-mean
return estimator rather than failing the whole analysis -- same pattern as
risk_free.py's Treasury fallback.
"""
from __future__ import annotations

import io
import re
import zipfile

import pandas as pd
import requests

FF3_ZIP_URL = (
    "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
    "F-F_Research_Data_Factors_CSV.zip"
)

REQUEST_TIMEOUT_SECONDS = 15

# Ken French's monthly rows are "YYYYMM,val,val,val,val"; the annual block
# further down the same file uses a bare four-digit year instead, which is
# how we know the monthly block has ended.
_MONTHLY_DATE_RE = re.compile(r"^\d{6}$")

FACTOR_COLUMNS = ["Mkt-RF", "SMB", "HML"]


class FactorDataError(ValueError):
    """Raised when Fama-French factor data can't be fetched or parsed."""


def _parse_ff3_csv(text: str) -> pd.DataFrame:
    lines = text.splitlines()
    header_idx = next((i for i, line in enumerate(lines) if "Mkt-RF" in line), None)
    if header_idx is None:
        raise FactorDataError("Unrecognized Fama-French CSV format: no header row found.")

    rows = []
    for line in lines[header_idx + 1 :]:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 5 or not _MONTHLY_DATE_RE.match(parts[0]):
            if rows:
                break  # monthly block ended (blank line or annual section)
            continue  # still in the header/description area
        date, mkt_rf, smb, hml, rf = parts[:5]
        try:
            rows.append(
                {
                    "date": date,
                    "Mkt-RF": float(mkt_rf) / 100.0,
                    "SMB": float(smb) / 100.0,
                    "HML": float(hml) / 100.0,
                    "RF": float(rf) / 100.0,
                }
            )
        except ValueError:
            break

    if not rows:
        raise FactorDataError("No monthly Fama-French factor rows parsed.")

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"], format="%Y%m")
    return df.set_index("date").sort_index()


def fetch_fama_french_factors() -> pd.DataFrame:
    """Return monthly Mkt-RF, SMB, HML, RF as decimals, indexed by month start."""
    try:
        resp = requests.get(FF3_ZIP_URL, timeout=REQUEST_TIMEOUT_SECONDS)
        resp.raise_for_status()
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            csv_name = next(n for n in zf.namelist() if n.lower().endswith(".csv"))
            text = zf.read(csv_name).decode("utf-8", errors="replace")
        return _parse_ff3_csv(text)
    except (requests.RequestException, zipfile.BadZipFile, StopIteration) as exc:
        raise FactorDataError(f"Could not fetch Fama-French factor data: {exc}") from exc
