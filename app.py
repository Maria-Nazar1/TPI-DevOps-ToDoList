import os
import time
import psycopg2
from flask import Flask, render_template, request, redirect, url_for

# --- Configuración de la Aplicación ---
app = Flask(__name__)

# Variables de entorno (DEFAULTS alineados con docker-compose)
DB_HOST = os.environ.get('DB_HOST', 'localhost')   # en docker: 'db'
DB_NAME = os.environ.get('DB_NAME', 'todolistdb') # <-- 'todolistdb'
DB_USER = os.environ.get('DB_USER', 'admin')      # <-- coincide con compose
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'admin123')

# --- Funciones de Conexión a Base de Datos ---
def get_db_connection():
    """Establece la conexión a PostgreSQL usando las variables de entorno."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        return None

def wait_for_db(retries=30, delay=2):
    """Espera activamente a que la base de datos responda."""
    attempt = 0
    while attempt < retries:
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                connect_timeout=3
            )
            conn.close()
            print("Base de datos disponible.")
            return True
        except Exception as e:
            attempt += 1
            print(f"[{attempt}/{retries}] Esperando a PostgreSQL... ({e})")
            time.sleep(delay)
    print("Timeout esperando a la base de datos.")
    return False

def init_db():
    """Crea la tabla 'tasks' si no existe."""
    conn = get_db_connection()
    if conn is not None:
        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    description TEXT NOT NULL,
                    completed BOOLEAN DEFAULT FALSE
                );
            """)
            conn.commit()
            cur.close()
            print("Tabla 'tasks' creada o verificada correctamente.")
        except Exception as e:
            print(f"Error al inicializar la base de datos: {e}")
        finally:
            conn.close()
    else:
        print("No se pudo inicializar la DB porque la conexión es None.")

# --- Sólo esperar e inicializar la DB si NO estamos en modo testing ---
if os.environ.get("FLASK_ENV", "").lower() != "testing":
    if wait_for_db():
        with app.app_context():
            init_db()
    else:
        print("Continuando sin inicializar la base de datos (falló la espera).")
else:
    print("Modo TESTING: se omite wait_for_db e init_db.")

# --- Rutas de la Aplicación (CRUD) ---
@app.route('/')
def index():
    conn = get_db_connection()
    tasks = []
    if conn is not None:
        try:
            cur = conn.cursor()
            cur.execute("SELECT id, description, completed FROM tasks ORDER BY id DESC;")
            tasks = cur.fetchall()
            cur.close()
        except Exception as e:
            print(f"Error al recuperar tareas: {e}")
        finally:
            conn.close()
    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['POST'])
def add_task():
    task_description = request.form.get('description')
    if task_description:
        conn = get_db_connection()
        if conn is not None:
            try:
                cur = conn.cursor()
                cur.execute("INSERT INTO tasks (description) VALUES (%s);", (task_description,))
                conn.commit()
                cur.close()
            except Exception as e:
                print(f"Error al añadir tarea: {e}")
            finally:
                conn.close()
    return redirect(url_for('index'))

# Ahora aceptamos POST (coincide con el form en index.html)
@app.route('/complete/<int:task_id>', methods=['POST'])
def complete_task(task_id):
    conn = get_db_connection()
    if conn is not None:
        try:
            cur = conn.cursor()
            cur.execute("SELECT completed FROM tasks WHERE id = %s;", (task_id,))
            row = cur.fetchone()
            if row is not None:
                current_status = row[0]
                new_status = not current_status
                cur.execute("UPDATE tasks SET completed = %s WHERE id = %s;", (new_status, task_id))
                conn.commit()
            cur.close()
        except Exception as e:
            print(f"Error al completar tarea: {e}")
        finally:
            conn.close()
    return redirect(url_for('index'))

# Ahora aceptamos POST (coincide con el form en index.html)
@app.route('/delete/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    conn = get_db_connection()
    if conn is not None:
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM tasks WHERE id = %s;", (task_id,))
            conn.commit()
            cur.close()
        except Exception as e:
            print(f"Error al eliminar tarea: {e}")
        finally:
            conn.close()
    return redirect(url_for('index'))

# --- Ejecución del Servidor ---
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
