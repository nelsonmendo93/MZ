"""
SUBIR_DATOS.py — Marca Zonal
Sube automáticamente todos los archivos de la carpeta /data a GitHub
usando la API de GitHub. No requiere git ni Anaconda prompt.

USO: Doble clic en SUBIR_DATOS.bat  (o ejecutar: python SUBIR_DATOS.py)
"""

import os
import base64
import json
import urllib.request
import urllib.error
import getpass

# ─── CONFIGURACIÓN ────────────────────────────────────────────────────────────
GITHUB_USER  = "nelsonmendo93"
GITHUB_REPO  = "MZ"
GITHUB_BRANCH = "main"
DATA_FOLDER  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
TOKEN_FILE   = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".github_token")
# ──────────────────────────────────────────────────────────────────────────────


def load_token() -> str:
    """Carga el token guardado, o pide uno nuevo."""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            token = f.read().strip()
        if token:
            print("✅  Token de GitHub cargado.")
            return token
    print("\n🔑  No se encontró token guardado.")
    print("    Necesitás un Personal Access Token de GitHub con permisos 'repo'.")
    print("    Podés crearlo en: https://github.com/settings/tokens")
    print()
    token = getpass.getpass("    Pegá tu token aquí (no se mostrará): ").strip()
    if not token:
        print("❌  Token vacío. Abortando.")
        input("\nPresioná Enter para cerrar...")
        exit(1)
    save = input("    ¿Guardar el token para la próxima vez? (s/n): ").strip().lower()
    if save == "s":
        with open(TOKEN_FILE, "w") as f:
            f.write(token)
        print("    💾  Token guardado en .github_token (no lo compartas).")
    return token


def github_api(method: str, endpoint: str, token: str, data: dict = None):
    """Hace una llamada a la API de GitHub."""
    url = f"https://api.github.com{endpoint}"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "MarcaZonal-Uploader/1.0",
    }
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        raise RuntimeError(f"HTTP {e.code}: {err_body}")


def get_file_sha(path_in_repo: str, token: str) -> str | None:
    """Obtiene el SHA del archivo en el repo (necesario para actualizarlo)."""
    try:
        result = github_api(
            "GET",
            f"/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{path_in_repo}?ref={GITHUB_BRANCH}",
            token,
        )
        return result.get("sha")
    except RuntimeError:
        return None  # El archivo no existe aún → será creado


def upload_file(local_path: str, token: str) -> str:
    """Sube o actualiza un archivo en el repo. Devuelve 'creado' o 'actualizado'."""
    filename = os.path.basename(local_path)
    repo_path = f"data/{filename}"

    with open(local_path, "rb") as f:
        content_b64 = base64.b64encode(f.read()).decode("utf-8")

    sha = get_file_sha(repo_path, token)

    payload = {
        "message": f"update: {filename} — Apertura 2026",
        "content": content_b64,
        "branch": GITHUB_BRANCH,
    }
    if sha:
        payload["sha"] = sha

    github_api(
        "PUT",
        f"/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{repo_path}",
        token,
        payload,
    )
    return "actualizado" if sha else "creado"


def main():
    print("=" * 60)
    print("  MARCA ZONAL — Subida de datos a GitHub")
    print("=" * 60)

    # Verificar carpeta data
    if not os.path.isdir(DATA_FOLDER):
        print(f"❌  No se encontró la carpeta 'data' en:\n    {DATA_FOLDER}")
        input("\nPresioná Enter para cerrar...")
        exit(1)

    # Listar archivos xlsx
    archivos = sorted([
        f for f in os.listdir(DATA_FOLDER)
        if f.endswith((".xlsx", ".xls", ".csv"))
    ])

    if not archivos:
        print("❌  No se encontraron archivos .xlsx en la carpeta 'data'.")
        input("\nPresioná Enter para cerrar...")
        exit(1)

    print(f"\n📂  Carpeta: {DATA_FOLDER}")
    print(f"📊  Archivos encontrados: {len(archivos)}\n")
    for a in archivos:
        size = os.path.getsize(os.path.join(DATA_FOLDER, a))
        print(f"     • {a}  ({size/1024:.1f} KB)")

    print()
    confirmar = input("¿Subir estos archivos a GitHub? (s/n): ").strip().lower()
    if confirmar != "s":
        print("Cancelado.")
        input("\nPresioná Enter para cerrar...")
        exit(0)

    token = load_token()
    print()

    errores = []
    for i, nombre in enumerate(archivos, 1):
        local_path = os.path.join(DATA_FOLDER, nombre)
        print(f"  [{i}/{len(archivos)}] {nombre} ... ", end="", flush=True)
        try:
            estado = upload_file(local_path, token)
            print(f"✅ {estado}")
        except Exception as e:
            print(f"❌ ERROR: {e}")
            errores.append(nombre)

    print()
    if errores:
        print(f"⚠️  {len(errores)} archivo(s) fallaron:")
        for e in errores:
            print(f"     • {e}")
    else:
        print("🎉  ¡Todo subido correctamente!")
        print("    Streamlit Cloud actualizará la app en 1-2 minutos.")

    print()
    input("Presioná Enter para cerrar...")


if __name__ == "__main__":
    main()
