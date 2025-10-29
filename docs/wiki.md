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
