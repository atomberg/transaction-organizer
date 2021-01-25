def test_upload(test_client):
    """Test the response of the upload page."""
    response = test_client.get('/reports', follow_redirects=True)
    assert response.status_code == 200


def test_parse(test_client, shared_datadir):
    """Test the response of the parse page."""
    response = test_client.post(
        '/reports',
        data={
            'transactions': (shared_datadir / 'transactions.xlsx').open('rb'),
            'items': (shared_datadir / 'items.xlsx').open('rb'),
        },
        follow_redirects=True,
        content_type='multipart/form-data',
    )
    assert response.status_code == 200
    assert b'table id="transactions_table"' in response.data
    assert b'<td>Item 2</td>\n        <td>Cash</td>\n        <td>30.00</td>' in response.data
    assert b'<td>Item 4</td>\n        <td>Card</td>\n        <td>16.00</td>' in response.data


def test_parse_with_missing_file(test_client, shared_datadir):
    """Test the response of the parse page when one file is missing."""
    response = test_client.post(
        '/reports',
        data={'transactions': (shared_datadir / 'transactions.xlsx').open('rb')},
        follow_redirects=True,
        content_type='multipart/form-data',
    )
    assert response.status_code == 200
    assert b'div class="alert alert-danger col-lg-12"' in response.data
    assert b'Please upload both reports required!' in response.data
