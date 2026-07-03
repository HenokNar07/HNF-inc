import pandas as pd
import pytest

from math_engine.factors import FactorDataError, _parse_ff3_csv

# A trimmed synthetic file matching Ken French's real layout: description
# text, a header row, monthly rows in percent, then an annual block that
# should be ignored.
SAMPLE_FF3_CSV = """\
This file was provided by Kenneth French.

,Mkt-RF,SMB,HML,RF
192607,   2.96,  -2.30,  -2.87,   0.22
192608,   2.64,  -1.40,   4.19,   0.25
192609,   0.36,  -1.32,   0.01,   0.23

Annual Factors: January-December
1926,   -1.03,  -6.28,  -3.34,   3.16
1927,   29.28,  -2.75,   4.28,   3.12
"""


def test_parse_ff3_csv_extracts_monthly_rows_only():
    df = _parse_ff3_csv(SAMPLE_FF3_CSV)
    assert list(df.columns) == ["Mkt-RF", "SMB", "HML", "RF"]
    assert len(df) == 3
    assert df.index[0] == pd.Timestamp("1926-07-01")
    assert df.loc["1926-07-01", "Mkt-RF"] == pytest.approx(0.0296)
    assert df.loc["1926-08-01", "RF"] == pytest.approx(0.0025)


def test_parse_ff3_csv_stops_before_annual_block():
    df = _parse_ff3_csv(SAMPLE_FF3_CSV)
    # The annual block's "1926" and "1927" rows must not leak in as months.
    assert pd.Timestamp("1926-01-01") not in df.index


def test_parse_ff3_csv_no_header_raises():
    with pytest.raises(FactorDataError):
        _parse_ff3_csv("just,some,random,csv\n1,2,3,4\n")


def test_parse_ff3_csv_empty_monthly_block_raises():
    with pytest.raises(FactorDataError):
        _parse_ff3_csv(",Mkt-RF,SMB,HML,RF\n\nAnnual Factors\n1926,1,2,3\n")
