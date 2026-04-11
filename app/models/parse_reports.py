"""Report parsing utilities for external spreadsheet exports."""

import pandas as pd


def parse_report(transactions_fileobj, items_fileobj):
    cash_purchases = pd.read_excel(
        transactions_fileobj, sheet_name='Cash Purchases', usecols=['ID/Note', 'Total'], engine='openpyxl'
    )
    cash_purchases['ID/Note'] = cash_purchases['ID/Note'].map(lambda s: f'#{s}')
    cash_purchases_ids = set(cash_purchases['ID/Note'].tolist())

    card_purchases = pd.read_excel(
        transactions_fileobj, sheet_name='Card Purchases', usecols=['ID/Note', 'Total'], engine='openpyxl'
    )
    card_purchases_ids = set(card_purchases['ID/Note'].tolist())

    both = cash_purchases_ids.intersection(card_purchases_ids)
    if both:
        cash_purchases_ids = cash_purchases_ids.difference(both)
        card_purchases_ids = card_purchases_ids.difference(both)

    items = pd.read_excel(items_fileobj, sheet_name='Item Details', engine='openpyxl')
    item_transaction_ids = set(items['Transaction ID'].tolist())
    items['Type'] = items['Transaction ID']
    items['Type'] = items['Type'].map(lambda t: 'Cash' if t in cash_purchases_ids else t)
    items['Type'] = items['Type'].map(lambda t: 'Card' if t in card_purchases_ids else t)

    report = items.groupby(by=['Name/SKU', 'Type'])['Grand Total'].sum()
    report = report.to_dict()

    cash_without_items = cash_purchases_ids.difference(item_transaction_ids)
    card_without_items = card_purchases_ids.difference(item_transaction_ids)

    if cash_without_items:
        report[('other', 'Cash')] = float(
            cash_purchases[cash_purchases['ID/Note'].isin(cash_without_items)]['Total'].sum()
        )
    if card_without_items:
        report[('other', 'Card')] = float(
            card_purchases[card_purchases['ID/Note'].isin(card_without_items)]['Total'].sum()
        )

    return report
