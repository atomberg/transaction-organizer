def test_autocomplete_supplier(client):
    response = client.get("/autocomplete/supplier")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_autocomplete_category(client):
    response = client.get("/autocomplete/category")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_autocomplete_category_guess(client):
    response = client.get("/autocomplete/category/guess")
    assert response.status_code == 200
    assert response.json() == {'category': ''}
