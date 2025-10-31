import os
import subprocess
import sys
import venv
import signal
from pathlib import Path


VENV_DIR = Path("venv")
REQUIREMENTS_FILE = Path("requirements.txt")
DOCKER_COMPOSE_FILE = Path("docker-compose.yaml")
APP_MODULE = "app.main:main"
PYTHON = VENV_DIR / "bin" / "python" if os.name != "nt" else VENV_DIR / "Scripts" / "python.exe"
running_processes = []


def run(cmd, cwd=None, check=True, background=False):
    print(f">> {' '.join(cmd)}")
    if background:
        proc = subprocess.Popen(cmd, cwd=cwd)
        running_processes.append(proc)
        return proc
    else:
        result = subprocess.run(cmd, cwd=cwd, check=check)
        return result.returncode


def ensure_venv():
    if not VENV_DIR.exists():
        print("Creating virtual environment")
        venv.EnvBuilder(with_pip=True).create(VENV_DIR)
    else:
        print("Virtual environment already exists")


def install_requirements():
    if REQUIREMENTS_FILE.exists():
        print("Installing requirements")
        run([str(PYTHON), "-m", "pip", "install", "--upgrade", "pip"])
        run([str(PYTHON), "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)])
    else:
        print("No requirements.txt found")


def run_tests():
    print("Running tests")
    try:
        run([str(PYTHON), "-m", "pytest", "--maxfail=1", "--disable-warnings", "-q"])
        print("Tests passed")
        return True
    except subprocess.CalledProcessError:
        print("Tests failed. Aborting")
        return False


def start_docker():
    if DOCKER_COMPOSE_FILE.exists():
        print("Starting Docker services...")
        run(["docker", "compose", "up", "-d"])
    else:
        print("No docker-compose.yml found")


def stop_docker():
    if DOCKER_COMPOSE_FILE.exists():
        print("Stopping Docker services...")
        try:
            subprocess.run(["docker", "compose", "down"], check=False)
        except Exception as e:
            print(f"Could not stop Docker: {e}")


def run_app():
    print("Starting FastAPI app")
    app_process = subprocess.Popen(
        [str(PYTHON), "-m", "uvicorn", APP_MODULE, "--reload"],
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    running_processes.append(app_process)
    app_process.wait()


def handle_exit(sig, frame):
    print("\nShutting down...")
    for p in running_processes:
        try:
            p.terminate()
        except Exception:
            pass
    stop_docker()
    sys.exit(0)


def main():
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    ensure_venv()
    install_requirements()

    if not run_tests():
        sys.exit(1)

    start_docker()
    run_app()


if __name__ == "__main__":
    main()
