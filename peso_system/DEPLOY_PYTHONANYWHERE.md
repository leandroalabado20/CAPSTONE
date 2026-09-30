# Deploying PESO System to PythonAnywhere

Account username: `luispaolo`  ->  https://luispaolo.pythonanywhere.com/

If your username differs, replace `luispaolo` everywhere below.
Get your real paths any time with `cd ~/peso_system && pwd` and `echo $VIRTUAL_ENV` (after `workon peso`).

## Part 1: Upload the zip
1. Log in -> **Files** tab (you start in `/home/luispaolo/`).
2. **Upload a file** -> `peso_system_deploy.zip`.
3. **Consoles** tab -> **Bash**, then:
   ```bash
   cd ~
   unzip -o peso_system_deploy.zip
   ls peso_system
   ```
   Expect: `app.py peso.db requirements.txt ml templates static uploads`.

## Part 2: Python environment
4. See available Python versions: `ls /usr/bin/python3*`
5. Create the virtualenv (needs Python 3.11+; local dev uses 3.13):
   ```bash
   mkvirtualenv peso --python=python3.13
   ```
6. Install packages. **Use `--no-cache-dir`**, the free plan has a 512 MB quota and pip's cache causes `OSError: [Errno 122] Disk quota exceeded`:
   ```bash
   pip cache purge
   rm -rf ~/.cache/pip
   cd ~/peso_system
   pip install --no-cache-dir -r requirements.txt
   ```
   (pip prints one "Successfully installed flask-... ..." line listing everything.)
7. Verify:
   ```bash
   python -c "import flask, pandas, numpy, sklearn, openpyxl, joblib; print('imports OK', sklearn.__version__)"
   python -c "import joblib; joblib.load('ml/recommendation_pipeline.pkl'); print('model OK')"
   du -sh ~
   rm ~/peso_system_deploy.zip
   ```
   Expect `imports OK 1.9.0` and `model OK`.

## Part 3: Create the web app
8. **Web** tab -> **Add a new web app** -> Next -> **Manual configuration** (not Flask) -> same Python version as step 5.

## Part 4: Configure (Web tab)
9. **Source code:** `/home/luispaolo/peso_system`
10. **Working directory:** `/home/luispaolo/peso_system`
11. **Virtualenv:** `/home/luispaolo/.virtualenvs/peso`
12. Generate a secret key in the Bash console:
    ```bash
    python -c "import secrets; print(secrets.token_hex(32))"
    ```
13. Click the **WSGI configuration file** link, delete everything, paste (use your key), **Save**:
    ```python
    import os, sys

    path = '/home/luispaolo/peso_system'
    if path not in sys.path:
        sys.path.insert(0, path)

    os.environ['FLASK_SECRET_KEY'] = 'PASTE_KEY_HERE'
    os.environ['PESO_HTTPS'] = '1'

    from app import app as application
    ```
14. Optional, Static files: URL `/static/` -> `/home/luispaolo/peso_system/static`
15. Click the green **Reload** button.

## Part 5: Test
16. Open https://luispaolo.pythonanywhere.com/ (use `https://`; `PESO_HTTPS=1` makes session cookies secure-only).
17. Try: home, login, recommendations, Excel upload, referral slip.
18. Errors: Web tab -> **Error log**.

## Part 6: Before sharing the link
- Log in as `admin` and change the default password (`admin123`).
- `peso.db` contains 52 applicants and 7 accounts. Ask for a cleaned copy if you don't want testers to see them.

## Part 7: Maintenance
- Free apps expire after 3 months: Web tab -> **Run until 3 months from today**.
- Update code: upload changed files (Files tab), then **Reload**.
  When unzipping a new zip, skip the DB so online data isn't overwritten:
  `unzip -o peso_system_deploy.zip -x 'peso_system/peso.db'`
- Back up online data: download `/home/luispaolo/peso_system/peso.db`.
- The online `peso.db` is separate from your local one.
- Local development is unchanged: `python app.py` -> http://localhost:5000

## Troubleshooting
| Symptom | Fix |
|---|---|
| "This directory does not exist" | Wrong username in the path. Run `pwd` in `~/peso_system`. |
| Disk quota exceeded | `pip cache purge`, `rm -rf ~/.cache/pip`, `pip install --no-cache-dir ...` |
| `ModuleNotFoundError` | Wrong virtualenv path, or install unfinished. Redo step 6. |
| sklearn pickle/version error | Versions differ from the pickle's. Keep the pins in `requirements.txt`. |
| Logged out immediately after login | Opened via `http://`. Use `https://`. |
| `attempt to write a readonly database` | `chmod 664 ~/peso_system/peso.db; chmod 775 ~/peso_system`, then Reload. |
| Excel upload fails | Make sure `~/peso_system/uploads/` exists. |
