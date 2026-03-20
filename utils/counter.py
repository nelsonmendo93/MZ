"""
Contador de visitas compartido entre páginas.
Incrementa una sola vez por sesión usando st.session_state.
"""
import os
import json
import streamlit as st

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COUNTER_FILE = os.path.join(_ROOT, "data", "visit_counter.json")


def _load(path: str) -> int:
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f).get("visits", 0)
        except Exception:
            return 0
    return 0


def _save(path: str, count: int) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump({"visits": count}, f)


def count_visit() -> int:
    """
    Incrementa el contador si es la primera carga en esta sesión.
    Retorna el total actual de visitas.
    """
    if "visit_counted" not in st.session_state:
        st.session_state["visit_counted"] = True
        total = _load(COUNTER_FILE) + 1
        _save(COUNTER_FILE, total)
        return total
    return _load(COUNTER_FILE)
