# SeedFactory (ValueWise™ Seed Factory)

A deterministic, offline lab that turns four Ensemble knowledge files into a Seed, builds and runs it in a simulated sandbox, validates it, and reports on it. No LLM and no network at runtime.

## Set up and run

### Windows

From the repository folder, one command sets up everything, assuming nothing is installed:

```
powershell -ExecutionPolicy Bypass -File .\run.ps1 setup
```

It installs, for your user and without admin rights, only what is missing: Python 3.12 or newer, Node.js 22.18 or newer, the backend's virtual environment (`backend\.venv`), the Python packages and the frontend packages. It is safe to run again; finished steps are skipped. The set-up needs the network once; the app never does.

Then:

```
powershell -ExecutionPolicy Bypass -File .\run.ps1          # start the app
powershell -ExecutionPolicy Bypass -File .\run.ps1 test     # run both test suites
```

Open the address it prints, `http://127.0.0.1:5273/`. `Ctrl+C` stops it.

### macOS and Linux

Install Python 3.12 or newer and Node.js 22.18 or newer, then:

```
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements-dev.txt
cd frontend && npm ci && cd ..
python3 run.py            # start the app
python3 run.py test       # run both test suites
```

## More

- `docs/operator-guide.md`: set-up in full, starting and stopping, the demo, rehearsing, troubleshooting.
- `docs/README.md`: the documents and which one wins when they disagree.
- `docs/CLAUDE.md`: the standing rules and the developer commands.
