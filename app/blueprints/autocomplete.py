from flask import Blueprint, request, jsonify
from models.transaction import guess_category, get_categories, get_suppliers


bp = Blueprint('autocomplete', __name__, url_prefix='/autocomplete')


@bp.route('/supplier', methods=['GET'])
def supplier():
    q = request.values.get('q')
    items = [s for s in get_suppliers() if q in s]
    return jsonify(items)


@bp.route('/category', methods=['GET'])
def category():
    q = request.values.get('q')
    items = [s for s in get_categories() if q in s]
    return jsonify(items)


@bp.route('/category/guess', methods=['GET'])
def category_guess():
    q = request.values.get('q')
    return jsonify(dict(category=guess_category(q)))
