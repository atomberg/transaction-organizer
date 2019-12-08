from flask import Blueprint, request, render_template, flash
from models.parse_reports import parse_report

bp = Blueprint('reports', __name__, url_prefix='/reports')


@bp.add_app_template_filter
def currency_format(value):
    return f'{value:.2f}'


@bp.route('/', methods=['GET'])
def upload():
    """Prompt the user to upload reports."""
    return render_template(
        'report_upload.html.j2'
    )


@bp.route('/', methods=['POST'])
def parse():
    """Parse the reports and display the results."""
    if not request.files.get('transactions') or not request.files.get('items'):
        flash('Please upload both reports required!')
        return upload()

    report = parse_report(request.files['transactions'], request.files['items'])
    return render_template(
        'report_parse.html.j2',
        report=report
    )
