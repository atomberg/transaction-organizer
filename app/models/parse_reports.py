import pandas as pd


def parse_report(transactions_fileobj, items_fileobj):
    cash_purchases = pd.read_excel(
        transactions_fileobj, sheet_name='Cash Purchases', usecols=['ID/Note'], engine='openpyxl'
    )
    cash_purchases['ID/Note'] = cash_purchases['ID/Note'].map(lambda s: f'#{s}')
    cash_purchases = set(cash_purchases['ID/Note'].tolist())

    card_purchases = set(
        pd.read_excel(
            transactions_fileobj, sheet_name='Card Purchases', usecols=['ID/Note'], engine='openpyxl'
        )['ID/Note'].tolist()
    )

    both = cash_purchases.intersection(card_purchases)
    if both:
        cash_purchases = cash_purchases.difference(both)
        card_purchases = card_purchases.difference(both)

    items = pd.read_excel(items_fileobj, sheet_name='Item Details', engine='openpyxl')
    items['Type'] = items['Transaction ID']
    items['Type'] = items['Type'].map(lambda t: 'Cash' if t in cash_purchases else t)
    items['Type'] = items['Type'].map(lambda t: 'Card' if t in card_purchases else t)

    report = items.groupby(by=['Name/SKU', 'Type'])['Grand Total'].sum()
    return report.to_dict()
