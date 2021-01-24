import io

from flask import Blueprint, flash, render_template, request

from models.parse_reports import parse_report

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
    return render_template('report_parse.html.j2', report=report)
