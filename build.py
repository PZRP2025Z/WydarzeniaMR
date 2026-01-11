import os
import subprocess
import sys
import venv
import signal
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


def run_tests():
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

        ensure_venv()

        if not run_tests():
            raise Exception("Tests failed")

        start_docker()

        print("✅ All services started. Backend is running in Docker.")
        print("Frontend URL: http://localhost:5173")
        print("Backend URL: http://localhost:8000")
        input("Press Enter to shut down everything...")

    except Exception as e:
        input(f"Error occurred: {str(e)}")
        sys.exit(1)
    finally:
        stop_docker()


if __name__ == "__main__":
    main()
