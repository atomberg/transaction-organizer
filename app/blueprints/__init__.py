from .donor_family import bp as donor_family_bp
from .persons import bp as persons_bp
from .reports import bp as reports_bp
from .transactions import bp as transactions_bp

__all__ = [persons_bp, transactions_bp, reports_bp, donor_family_bp]
