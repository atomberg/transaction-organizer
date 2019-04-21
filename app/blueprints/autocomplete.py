from flask import Blueprint, request, jsonify
from models.transaction import guess_category


bp = Blueprint('autocomplete', __name__)


@bp.route('/guess/<string:what>', methods=['GET'])
def guess(what):
    if what == 'category':
        q = request.values.get('q')
        return jsonify(dict(category=guess_category(q)))
    else:
        return jsonify(dict())
