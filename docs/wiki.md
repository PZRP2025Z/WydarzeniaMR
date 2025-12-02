# Starting the backend side
Backend is based on uvicorn, a popular solution for FastAPI server, to start the app in root folder run `python -m uvicorn app.main:app --reload` then you can access the site on address `http://127.0.0.1:8000/docs`

# Database
We are using `PostgreSQL` currently via pgAdmin4 on localhost (install PosgreSQL locally to access it). This will need to be updated with docker-compose.
Keep in mind that .env db properties may vary until we get docket-compose setup

# Logger
We are using a `logging` library to handle file ond stdstream logging.
WARNING: Instead of using: logging.info("") firstly create an instance of a logger with `logger = logging.getLogger(__name__)` then `logger.info("")` since operating on a root logger is a bad practice (example at main.py).

# Linter & Autoformater
Out linter and autoformatter is `Ruff`, best way to use it is to download vscode extension Ruff: `charliermarsh.ruff`
To configure it, first install it from vscode extension tool, then using ctrl+shift+P -> User Settings (JSON), then add the following config:
```json
    "[python]":{
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.formatOnSave": true
    }
```
Ruff will format everything on save from now on.

# JWT & Cookies
Project uses two types of JWT tokens: short access token and a long refresh token. Both are saved in secure cookies, but the short one expires quickly, so it's safer to send around. When short one expires it can get refreshed thanks to safe stored long refresh token, which is deleted after a user logs out. This approach solves auto login.