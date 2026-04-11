"""Routes for uploading and parsing external transaction reports."""

import io
import json

import pandas as pd
from flask import Blueprint, flash, render_template, request, send_file

from app.models.parse_reports import parse_report

bp = Blueprint('reports', __name__, url_prefix='/reports')


@bp.add_app_template_filter
def currency_format(value):
    return f'{value:.2f}'


@bp.route('/', methods=['GET'])
def upload():
    """Prompt the user to upload reports."""
    return render_template('report_upload.html.j2')


@bp.route('/', methods=['POST'])
def parse():
    """Parse the reports and display the results."""
    if not request.files.get('transactions') or not request.files.get('items'):
        flash('Please upload both reports required!')
        return upload()

    transactions_file = io.BytesIO(request.files['transactions'].read())
    items_file = io.BytesIO(request.files['items'].read())
    report = parse_report(transactions_file, items_file)
    report_rows_by_sku = {}
    for (item, typ), amount in report.items():
        if item not in report_rows_by_sku:
            report_rows_by_sku[item] = {'sku': item, 'card': 0.0, 'cash': 0.0, 'other': 0.0}

        amount = float(amount)
        typ = str(typ).lower()
        if typ == 'card':
            report_rows_by_sku[item]['card'] += amount
        elif typ == 'cash':
            report_rows_by_sku[item]['cash'] += amount
        else:
            report_rows_by_sku[item]['other'] += amount

    report_rows = sorted(
        [
            {
                'sku': row['sku'],
                'card': row['card'],
                'cash': row['cash'],
                'total': row['card'] + row['cash'] + row['other'],
            }
            for row in report_rows_by_sku.values()
        ],
        key=lambda r: str(r['sku']).lower(),
    )
    report_sums = {
        'card': sum(row['card'] for row in report_rows),
        'cash': sum(row['cash'] for row in report_rows),
        'total': sum(row['total'] for row in report_rows),
    }
    return render_template('report_parse.html.j2', report_rows=report_rows, report_sums=report_sums)


@bp.route('/export', methods=['POST'])
def export():
    """Export parsed report rows to an xlsx file."""
    report_rows_raw = request.form.get('report_rows')
    if not report_rows_raw:
        flash('No parsed report found to export. Please upload reports first.')
        return upload()

    try:
        report_rows = json.loads(report_rows_raw)
    except json.JSONDecodeError:
        flash('Could not parse the exported report data. Please parse reports again.')
        return upload()

    if not isinstance(report_rows, list):
        flash('Invalid report data provided for export.')
        return upload()

    normalized_rows = []
    for row in report_rows:
        if not isinstance(row, dict):
            continue
        normalized_rows.append(
            {
                'SKU': row.get('sku', ''),
                'Card': row.get('card', 0.0),
                'Cash': row.get('cash', 0.0),
                'Total': row.get('total', 0.0),
            }
        )

    if not normalized_rows:
        flash('No parsed rows are available to export.')
        return upload()

    report_df = pd.DataFrame(normalized_rows)
    report_df['Card'] = pd.to_numeric(report_df['Card'], errors='coerce').fillna(0.0)
    report_df['Cash'] = pd.to_numeric(report_df['Cash'], errors='coerce').fillna(0.0)
    report_df['Total'] = pd.to_numeric(report_df['Total'], errors='coerce').fillna(0.0)

    workbook = io.BytesIO()
    with pd.ExcelWriter(workbook, engine='openpyxl') as writer:
        report_df.to_excel(writer, sheet_name='Parsed Report', index=False)
    workbook.seek(0)

    return send_file(
        workbook,
        as_attachment=True,
        download_name='parsed_report.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    )
