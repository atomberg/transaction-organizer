from flask import Blueprint, request, jsonify
from models.transaction import guess_category


bp = Blueprint('autocomplete', __name__, url_prefix='/autocomplete')


@bp.route('/<string:what>', methods=['GET'])
def autocomplete(what):
    if what == 'category':
        q = request.values.get('q')
        return jsonify(dict(category=guess_category(q)))
    else:
        return jsonify(dict())
