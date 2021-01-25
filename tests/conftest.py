# import os
# import tempfile

import pytest

from app import create_app


@pytest.fixture(scope='module')
def test_client():
    backend = create_app()
    backend.secret_key = 'test key'
    # db_fd, backend.config['DATABASE'] = tempfile.mkstemp()
    backend.config['TESTING'] = True

    with backend.test_client() as client:
        yield client

    # os.close(db_fd)
    # os.unlink(backend.config['DATABASE'])
