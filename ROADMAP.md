# ROADMAP — Futbol App → Mobile App

## Objetivo Final

Construir una **aplicación móvil** (iOS / Android) que exponga los análisis de fútbol paraguayo actualmente disponibles en la app Streamlit. Los datos se actualizan semanalmente (database.xlsx y archivos de equipos).

---

## Estado Actual (Streamlit)

- App funcional en producción con análisis de jugadores (radar, percentiles, XY, Best XI, PCA)
- Predictor de partidos con distribución de Poisson personalizada
- Soporte multi-liga: Paraguay, Argentina, Brasil
- Actualización semanal manual de datos Excel

---

## Fases hacia la App Móvil

### Fase 1 — API Backend
Crear una API REST que exponga los datos y cálculos del proyecto Streamlit sin tocar los archivos actuales.

- Carpeta sugerida: `api/` (independiente de `pages/` y `utils/`)
- Framework candidato: **FastAPI** (Python, compatible con la lógica existente)
- Endpoints clave:
  - `GET /players` — lista de jugadores con filtros por posición, equipo, liga
  - `GET /players/{id}/stats` — estadísticas completas de un jugador
  - `GET /players/{id}/percentiles` — percentiles por grupo de posición
  - `GET /teams` — lista de equipos
  - `GET /predict` — predicción de partido (parámetros: equipo local, visitante)
- Reutilizar directamente `utils/data_processing.py` para el procesamiento de datos

### Fase 2 — Sincronización de Datos
Definir cómo la API consume los archivos Excel actualizados semanalmente.

- Opción A: La API lee directamente `data/database.xlsx` (más simple, misma carpeta)
- Opción B: Script de exportación que convierte Excel → SQLite/PostgreSQL para mejor rendimiento
- El flujo de actualización semanal del usuario no debe cambiar

### Fase 3 — App Móvil
Construir la interfaz móvil consumiendo la API.

- Framework candidato: **React Native** o **Flutter**
- Pantallas prioritarias:
  1. Lista de jugadores con búsqueda y filtros
  2. Perfil de jugador (stats, radar chart, percentiles)
  3. Comparador de jugadores
  4. Predictor de partidos
  5. Ranking / Best XI

### Fase 4 — Autenticación y Deploy
- Autenticación básica para la API (si es pública)
- Deploy del backend (Railway, Render, o similar)
- Publicación en App Store / Google Play

---

## Restricciones Importantes

- **La app Streamlit debe permanecer funcional** durante todo el desarrollo
- No modificar archivos en `pages/`, `utils/`, `Inicio.py`, `app.py`, `.streamlit/`
- Todo código nuevo va en carpetas nuevas (`api/`, `mobile/`, etc.)
- El flujo de actualización semanal de Excel no debe verse afectado

---

## Notas Técnicas

- La lógica de percentiles por grupo de posición es central — debe replicarse en la API exactamente como está en `data_processing.py`
- Los overrides manuales de posición (`PLAYER_POSITION_OVERRIDES`) deben mantenerse sincronizados entre Streamlit y la API
- El cálculo de Poisson en `pages/2_⚽_Predictor.py` no usa scipy — la implementación custom debe portarse a la API
