"""Unit tests for report parsing edge cases."""

import io
from zipfile import BadZipFile

import pandas as pd
import pytest

from app.models.parse_reports import parse_report


def make_workbook(sheets):
    workbook = io.BytesIO()
    with pd.ExcelWriter(workbook, engine='openpyxl') as writer:
        for sheet_name, dataframe in sheets.items():
            dataframe.to_excel(writer, sheet_name=sheet_name, index=False)
    workbook.seek(0)
    return workbook


def test_parse_report_handles_duplicate_ids_across_cash_and_card():
    transactions = make_workbook(
        {
            'Cash Purchases': pd.DataFrame({'ID/Note': [101]}),
            'Card Purchases': pd.DataFrame({'ID/Note': ['#101']}),
        }
    )
    items = make_workbook(
        {
            'Item Details': pd.DataFrame(
                {
                    'Name/SKU': ['Membership'],
                    'Transaction ID': ['#101'],
                    'Grand Total': [25.0],
                }
            )
        }
    )

    report = parse_report(transactions, items)
    assert report[('Membership', '#101')] == 25.0


def test_parse_report_raises_on_missing_required_sheet():
    transactions = make_workbook(
        {
            'Cash Purchases': pd.DataFrame({'ID/Note': [101]}),
        }
    )
    items = make_workbook(
        {
            'Item Details': pd.DataFrame(
                {
                    'Name/SKU': ['Membership'],
                    'Transaction ID': ['#101'],
                    'Grand Total': [25.0],
                }
            )
        }
    )

    with pytest.raises(ValueError):
        parse_report(transactions, items)


def test_parse_report_raises_on_malformed_input_file():
    with pytest.raises(BadZipFile):
        parse_report(io.BytesIO(b'not an xlsx file'), io.BytesIO(b'also not xlsx'))
