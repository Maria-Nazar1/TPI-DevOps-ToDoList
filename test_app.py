import pytest
from unittest.mock import patch, MagicMock
from app import app


# ------------------------------------------------------------
# FIXTURE: cliente de pruebas de Flask
# ------------------------------------------------------------
@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# ------------------------------------------------------------
# Helper para mockear la conexión a PostgreSQL
# ------------------------------------------------------------
def mock_connection(tasks=None):
    """
    Crea un mock de conexión con cursor falso.
    Permite simular SELECT, INSERT, UPDATE y DELETE.
    """
    conn = MagicMock()
    cursor = MagicMock()

    # Simular fetchall() para SELECT en '/'
    cursor.fetchall.return_value = tasks or []

    # Simular fetchone() para SELECT en /complete/<id>
    cursor.fetchone.return_value = (False,)  # tarea no completada

    conn.cursor.return_value = cursor
    return conn


# ------------------------------------------------------------
# TEST 1 — El index carga sin errores
# ------------------------------------------------------------
@patch('app.get_db_connection')
def test_index_loads(mock_db, client):
    fake_tasks = [
        (1, "Tarea de prueba", False),
        (2, "Tarea completada", True),
    ]

    mock_conn = mock_connection(tasks=fake_tasks)
    mock_db.return_value = mock_conn

    response = client.get('/')
    assert response.status_code == 200
    assert b"Tarea de prueba" in response.data
    assert b"Tarea completada" in response.data


# ------------------------------------------------------------
# TEST 2 — Añadir tarea (POST)
# ------------------------------------------------------------
@patch('app.get_db_connection')
def test_add_task(mock_db, client):
    mock_db.return_value = mock_connection()

    response = client.post('/add', data={'description': 'Nueva tarea'})
    # Debe redirigir al index
    assert response.status_code == 302
    assert response.location.endswith('/')


# ------------------------------------------------------------
# TEST 3 — Completar / revertir tarea
# ------------------------------------------------------------
@patch('app.get_db_connection')
def test_complete_task(mock_db, client):
    mock_conn = mock_connection()
    mock_db.return_value = mock_conn

    response = client.post('/complete/1')
    assert response.status_code == 302  # redirección


# ------------------------------------------------------------
# TEST 4 — Eliminar tarea
# ------------------------------------------------------------
@patch('app.get_db_connection')
def test_delete_task(mock_db, client):
    mock_conn = mock_connection()
    mock_db.return_value = mock_conn

    response = client.post('/delete/1')
    assert response.status_code == 302  # redirección


# ------------------------------------------------------------
# TEST 5 — El template se renderiza sin errores si no hay tareas
# ------------------------------------------------------------
@patch('app.get_db_connection')
def test_index_no_tasks(mock_db, client):
    mock_conn = mock_connection(tasks=[])
    mock_db.return_value = mock_conn

    response = client.get('/')
    assert response.status_code == 200
    assert b"No hay tareas" in response.data
