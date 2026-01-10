import os
import subprocess
import sys
import venv
import signal
import time
from pathlib import Path
import dotenv

dotenv.load_dotenv()

VENV_DIR = Path("venv")
DOCKER_COMPOSE_FILE = Path("docker-compose.yaml")
PROJECT_ROOT = Path(__file__).resolve().parent
running_processes = []


def run(cmd, cwd=None, check=True, background=False, env=None):
    print(f">> {' '.join(cmd)}")
    if background:
        proc = subprocess.Popen(cmd, cwd=cwd, env=env)
        running_processes.append(proc)
        return proc
    else:
        result = subprocess.run(cmd, cwd=cwd, check=check, env=env)
        return result.returncode


def ensure_venv():
    if not VENV_DIR.exists():
        print("Creating virtual environment")
        venv.EnvBuilder(with_pip=True).create(VENV_DIR)
    else:
        print("Virtual environment already exists")


def install_requirements():
    """Instaluje pakiety lokalnie do testów, ale nie uruchamia backendu."""
    print("Installing requirements in venv for local tests")
    PYTHON = VENV_DIR / "bin" / "python" if os.name != "nt" else VENV_DIR / "Scripts" / "python.exe"
    run([str(PYTHON), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"])
    run([str(PYTHON), "-m", "pip", "install", "-e", "."])
    run([str(PYTHON), "-m", "pip", "install", "-e", ".[test,dev]"])

    # Install frontend dependencies
    frontend_dir = PROJECT_ROOT / "app" / "frontend"
    if frontend_dir.exists():
        print("Installing frontend dependencies (npm)")
        run(["npm", "install"], cwd=frontend_dir)


def run_tests():
    """Uruchamia lokalnie testy w venv (opcjonalne)."""
    print("Running tests")
    PYTHON = VENV_DIR / "bin" / "python" if os.name != "nt" else VENV_DIR / "Scripts" / "python.exe"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)

    result = subprocess.run(
        [str(PYTHON), "-m", "pytest", "--maxfail=1", "--disable-warnings", "-q"],
        cwd=PROJECT_ROOT,
        env=env,
        check=False,
    )
    if result.returncode == 0:
        print("Tests passed")
        return True
    else:
        print("Tests failed. Aborting")
        return False


def start_docker():
    if DOCKER_COMPOSE_FILE.exists():
        print("Starting Docker services (frontend, backend, worker)...")
        run(["docker", "compose", "up", "-d", "--build"])
    else:
        print("No docker-compose.yml found")


def stop_docker():
    if DOCKER_COMPOSE_FILE.exists():
        print("Stopping Docker services...")
        try:
            subprocess.run(["docker", "compose", "down", "-v"], check=False)
        except Exception as e:
            print(f"Could not stop Docker: {e}")


def wait_for_postgres(timeout=60):
    """Czeka aż baza danych w kontenerze będzie gotowa."""
    print("Waiting for PostgreSQL")
    import psycopg2
    DB_USERNAME = os.getenv("DB_USERNAME")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = int(os.getenv("DB_PORT", 5432))
    DB_NAME = os.getenv("DB_NAME")
    start = time.time()
    while time.time() - start < timeout:
        try:
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                user=DB_USERNAME,
                password=DB_PASSWORD,
                dbname=DB_NAME,
            )
            conn.close()
            print("✅ PostgreSQL is ready!")
            return True
        except psycopg2.OperationalError:
            time.sleep(1)
    print("PostgreSQL did not become ready in time.")
    return False


def handle_exit(sig, frame):
    print("\nShutting down...")
    for p in running_processes:
        try:
            p.terminate()
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            p.kill()
        except Exception as e:
            print(f"Error stopping process: {e}")
    stop_docker()
    sys.exit(0)


def main():
    try:
        signal.signal(signal.SIGINT, handle_exit)
        signal.signal(signal.SIGTERM, handle_exit)

        # Wirtualne środowisko i instalacja dla testów (nie uruchamiamy backendu lokalnie)
        ensure_venv()
        install_requirements()

        # Opcjonalne testy
        # if not run_tests():
        #     raise Exception("Tests failed")

        # Start wszystkich kontenerów
        start_docker()

        # Czekamy aż baza danych w kontenerze będzie gotowa
        if not wait_for_postgres():
            raise Exception("Postgres failed to initialize")

        print("✅ All services started. Backend is running in Docker.")
        print("Frontend URL: http://localhost:5173")
        print("Backend URL: http://localhost:8000")
        print("Dramatiq worker is running in Docker as well.")
        input("Press Enter to shut down everything...")

    except Exception as e:
        input(f"Error occurred: {str(e)}")
        sys.exit(1)
    finally:
        stop_docker()


if __name__ == "__main__":
    main()
