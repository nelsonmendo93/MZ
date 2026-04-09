from pathlib import Path
import runpy


# Reutiliza la portada principal para mantener una sola home consistente
# aunque el deploy use `Inicio.py` o `app.py`.
runpy.run_path(str(Path(__file__).with_name("app.py")), run_name="__main__")
