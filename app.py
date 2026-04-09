from pathlib import Path
import runpy


# Mantiene una sola portada real para evitar diferencias entre deploys
# que apunten a `app.py` o a `Inicio.py`.
runpy.run_path(str(Path(__file__).with_name("Inicio.py")), run_name="__main__")
