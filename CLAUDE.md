# CLAUDE.md — Marca Zonal: Portal de Análisis de Fútbol Paraguayo

**Última actualización:** Abril 20, 2026  
**Propósito:** Documentación completa del proyecto para Claude en futuras sesiones  
**Estado:** En producción (Streamlit Cloud) + Desarrollo activo

---

## 📋 TABLA DE CONTENIDOS

1. [Estado del Proyecto](#estado-del-proyecto)
2. [Ejecutar la App](#ejecutar-la-app)
3. [Arquitectura](#arquitectura)
4. [Estructura de Archivos](#estructura-de-archivos)
5. [Funcionalidades Actuales](#funcionalidades-actuales)
6. [Datos y Estructura](#datos-y-estructura)
7. [Componentes Clave](#componentes-clave)
8. [Notas para Claude](#notas-para-claude)
9. [Roadmap: Hacia la App Móvil](#roadmap-hacia-la-app-móvil)

---

## 📊 ESTADO DEL PROYECTO

### ✅ En Producción
- **App Streamlit:** https://marcazonal.streamlit.app
- **Estado:** Funcional con 3 páginas
- **Actualizaciones:** Semanales de datos Excel (manual)
- **Datos actuales:** Apertura 2026 (actualizado 2026-04-20)

### 📱 En Desarrollo
- **Objetivo final:** App móvil (iOS/Android)
- **Fase actual:** Planificación de API Backend
- **Restricción crítica:** NO modificar `.streamlit/` sin consultar primero

---

## 🚀 EJECUTAR LA APP

```bash
# Opción principal
streamlit run Inicio.py

# Alternativa directa
streamlit run app.py
```

**Nota:** `Inicio.py` es un wrapper de `app.py` usando `runpy.run_path()`.  
**URL local:** http://localhost:8501

---

## 🏗️ ARQUITECTURA

**Tipo:** Multi-page Streamlit application

```
futbol-app/
├── app.py                    ← Home/portada principal (181 LOC)
├── Inicio.py                 ← Wrapper de app.py (14 LOC)
├── pages/
│   ├── 1_📊_Jugadores.py    ← Análisis de jugadores (3641 LOC)
│   ├── 2_⚽_Predictor.py     ← Predictor de partidos (1663 LOC)
│   └── 3_Tiempo_efectivo.py  ← Tiempo efectivo por equipo (547 LOC)
├── utils/
│   ├── data_processing.py    ← Core de datos con cache (253 LOC)
│   ├── scout_html.py         ← Tarjeta Scout HTML + exportar PNG (676 LOC)
│   ├── bar_chart.py          ← Gráficos de percentiles (501 LOC)
│   ├── pizza_chart.py        ← Gráficos radar PyPizza (142 LOC)
│   ├── xy_chart.py           ← Scatter plots 2D (118 LOC)
│   ├── translations.py       ← Mapeo English→Spanish (178 LOC)
│   ├── counter.py            ← Contador de visitas (39 LOC)
│   └── dom-to-image-more.min.js  ← Librería JS para exportar PNG
├── data/
│   ├── database.xlsx         ← Jugadores Paraguay Apertura 2026 (primario)
│   ├── ARG.xlsx              ← Liga argentina
│   ├── BRA.xlsx              ← Liga brasileña
│   ├── CHI.xlsx              ← Liga chilena
│   ├── COL.xlsx              ← Liga colombiana
│   ├── ECU.xlsx              ← Liga ecuatoriana
│   ├── URU.xlsx              ← Liga uruguaya
│   ├── Team Stats *.xlsx     ← 12 archivos (uno por equipo paraguayo)
│   └── visit_counter.json    ← Persistencia del contador de visitas
├── assets/
│   ├── logo_blanco.png
│   └── logo_negro.png
├── _color_backup/            ← Backup de colores anteriores (verde)
├── ROADMAP.md
└── CLAUDE.md                 ← Este archivo
```

---

## 📁 ESTRUCTURA DE ARCHIVOS (Detallado)

### `app.py` — Home (181 LOC)
- Configuración Streamlit (`st.set_page_config`)
- Estilos CSS globales: tema oscuro, fuentes Poppins/Cousine
- Logo, bienvenida y 3 botones de navegación (`switch_page`)
- Contador de visitas en sesión

### `pages/1_📊_Jugadores.py` — Análisis Principal (3641 LOC)

**8 tabs disponibles:**

| Tab | Nombre | Descripción |
|-----|--------|-------------|
| 1 | 📊 Tabla de datos | DataFrame interactivo con filtros |
| 2 | 📈 Gráfico XY | Scatter plot 2D con cuadrantes |
| 3 | 🏆 OVERALL | Pentágono MARCA ZONAL SCORE + Vista Scout |
| 4 | 🎯 Radial | Pizza chart (15 métricas, 3 grupos) |
| 5 | 🔍 Similares | PCA + distancia euclídea (multi-liga) |
| 6 | 🏅 Rankings | Top jugadores por métrica |
| 7 | 🐝 Swarm | Distribución métrica vs grupo posicional |
| 8 | ⚽ Mejor Once | Constructor de equipo ideal |

**Datos cargados:**
- `database.xlsx` (PAR) — siempre cargado
- `ARG.xlsx`, `BRA.xlsx`, `URU.xlsx`, `COL.xlsx`, `ECU.xlsx`, `CHI.xlsx` — lazy load

**Filtros disponibles:**
- Grupo de posición (6 grupos)
- Club/equipo
- Rango de edad (slider dinámico)
- Minutos mínimos (para pool de percentiles)

### `pages/2_⚽_Predictor.py` — Predictor (1663 LOC)
- Distribución de Poisson personalizada (sin scipy)
- Basada en xG (Expected Goals) por equipo
- **Salidas:** Prob(V/E/D), xG, xPTS, esquinas, tarjetas, goles por tiempo

### `pages/3_Tiempo_efectivo.py` — Tiempo Efectivo (547 LOC)
- Analiza posesión real por equipo
- **Fórmula:** Tiempo Efectivo = Pases ÷ Match Tempo
- **Salida:** Ranking de 12 equipos en formato HH:MM:SS
- **Datos:** 12 archivos `Team Stats *.xlsx`

### `utils/data_processing.py` — Core de Datos (253 LOC)
- `load_and_process_data()` / `process_database()` con `@st.cache_data`
- Métricas derivadas:
  - `CBIT` = Sliding tackles + Interceptions + Shots blocked
  - `Progressive actions` = Progressive passes + Progressive runs
  - `Goals - xG diff`
- Overrides manuales de posición (algunos jugadores reasignados)
- **6 grupos de posición:** Delantero, Extremo, Volante Central, Lateral, Central, Portero
- Percentiles se calculan DENTRO del grupo, no globalmente

### `utils/scout_html.py` — Tarjeta Scout (676 LOC)
- `build_scout_html()` → Genera HTML completo de ficha de jugador
- Incluye: foto posición en cancha, pentágono de atributos, TOP 5 métricas, TOP 5 similares, MARCA ZONAL SCORE
- Exportar a PNG via `dom-to-image-more.min.js`
- Colores por liga: PAR=rojo, ARG=teal, BRA=verde, URU=azul, COL=amarillo, ECU=violeta, CHI=naranja

### `utils/bar_chart.py` — Bar Chart (501 LOC)
- Percentiles horizontales por 4 categorías de métricas
- Optimizado para comparación multi-jugador

---

## 🎮 FUNCIONALIDADES ACTUALES (Detalle)

### Tab 3: 🏆 OVERALL — MARCA ZONAL SCORE

**Pentágono de 5 ejes:**
- `ATQ` = Ataque
- `POS` = Posesión
- `PAS` = Pases
- `DEF` = Defensa
- `CRE` = Creatividad

**Pesos por posición (MARCA ZONAL SCORE):**
```python
'Central':         {'DEF': 35, 'PAS': 25, 'POS': 20, 'CRE': 10, 'ATQ': 10}
'Lateral':         {'DEF': 25, 'POS': 25, 'PAS': 20, 'ATQ': 15, 'CRE': 15}
'Volante Central': {'POS': 30, 'PAS': 25, 'CRE': 20, 'DEF': 15, 'ATQ': 10}
'Extremo':         {'ATQ': 30, 'CRE': 25, 'POS': 20, 'PAS': 15, 'DEF': 10}
'Delantero':       {'ATQ': 40, 'CRE': 20, 'POS': 15, 'PAS': 15, 'DEF': 10}
```

**Vista Scout (en este mismo tab):**
- Tarjeta HTML con: posición en cancha, pentágono, TOP 5 métricas, TOP 5 similares
- Botón "Exportar PNG" — usa `dom-to-image-more.min.js` para captura fiel en móvil/desktop
- Branding Marca Zonal embebido vía canvas en la imagen exportada

### Tab 5: 🔍 Similares — PCA Multi-liga

- Algoritmo: StandardScaler → PCA (≥85% varianza, mín 3 / máx 25 componentes) → distancia euclídea
- Pool configurable: PAR + cualquier combinación de ARG, BRA, URU, COL, ECU, CHI
- Filtros: grupo de posición, edad mínima/máxima, minutos mínimos
- Resultado: 5 jugadores más similares con badge de liga

### Tab 7: 🐝 Swarm

- Distribución de una métrica del jugador vs todo su grupo posicional
- Filtros: posición, club, jugador, rango de edad, minutos mínimos del pool

### Tab 8: ⚽ Mejor Once

- Selección automática basada en métricas ponderadas por rol
- Slots: GK (1), LCB/RCB (2), LB/RB (2), MID (2), LW/RW (2), CF (2)
- Pesos específicos por posición definidos en `_B11_ROLE_METRICS`

### Rankings (Tab 6)

- Cualquier métrica numérica disponible
- Soporte expandido para porteros (columnas especiales de GK)
- Top N con barra visual y colores por ranking

---

## 📊 DATOS Y ESTRUCTURA

### Ligas disponibles (7 en total)

| Archivo | Liga | Estado |
|---------|------|--------|
| `database.xlsx` | Paraguay (PAR) | Siempre cargado |
| `ARG.xlsx` | Argentina | Activo en Similares |
| `BRA.xlsx` | Brasil | Activo en Similares |
| `URU.xlsx` | Uruguay | Activo en Similares |
| `COL.xlsx` | Colombia | Activo en Similares |
| `ECU.xlsx` | Ecuador | Activo en Similares |
| `CHI.xlsx` | Chile | Activo en Similares |

### Team Stats (12 archivos para Tiempo Efectivo)
```
Team Stats 2 de Mayo.xlsx
Team Stats Cerro Porteño.xlsx
Team Stats Club Libertad.xlsx
Team Stats Deportivo Recoleta.xlsx
Team Stats Guaraní.xlsx
Team Stats Nacional Asunción.xlsx
Team Stats Olimpia.xlsx
Team Stats Rubio Ñú.xlsx
Team Stats Sportivo Ameliano.xlsx
Team Stats Sportivo Luqueño.xlsx
Team Stats Sportivo San Lorenzo.xlsx
Team Stats Sportivo Trinidense.xlsx
```

### Columnas `database.xlsx`

**Identidad:** Player, Team, Position, Position Group, Minutes played, Matches played, Pie (foot), Age, Height, Weight

**Ataque (~17):** Goals, xG, Dif G-xG, Non-penalty goals, Head goals, Shots, Shots on target, Assists, xA, Shot assists, Key passes, Touches in box, Dribbles, Offensive duels, Successful attacking actions, Progressive runs, Accelerations

**Defensa (~9):** Successful defensive actions, Defensive duels, Aerial duels, Sliding tackles, Interceptions, Shots blocked, Fouls, Yellow cards, Red cards

**Pases (~15):** Passes, Forward passes, Back passes, Lateral passes, Short/medium passes, Long passes, Progressive passes, Passes to final third, Passes to penalty area, Through passes, Deep completions, Deep completed crosses, Crosses, Received passes, Received long passes

**Derivadas:**
- `CBIT` = Sliding tackles + Interceptions + Shots blocked
- `Progressive actions` = Progressive passes + Progressive runs
- `Goals - xG diff`

**Variantes:** Total / Per 90 / Accuracy %

---

## 🔧 COMPONENTES CLAVE

### Sistema de Colores (Ámbar Nocturno — paleta actual)
```css
Background:       #0f172a  (muy oscuro, azul navy)
Surface:          #1e293b  (oscuro)
Accent primario:  #22c55e  (verde — botones, contadores)
Accent ámbar:     #f59e0b  (ámbar — rankings #1, GK slot, categoría Pelota Parada)
Accent amarillo:  #fbbf24  (amarillo — ranking visual)
Text:             #e2e8f0  (gris claro)
Muted:            #64748b  (gris medio)
```

**Nota:** La paleta pasó de verde puro → ámbar nocturno (commit `1c1eaae`). El verde persiste en accentos de navegación; el ámbar domina rankings y elementos destacados.

### Tipografía
```
Body:     'Cousine' monospace (Google Fonts)
Headings: 'Poppins' sans-serif (Google Fonts)
```

### Grupos de Posición (6)
1. **Delantero** — Strikers (CF, ST, SS)
2. **Extremo** — Wingers (LW, RW, LWF, RWF)
3. **Volante Central** — Midfielders (DMF, CMF, AMF, LCMF, RCMF, LAMF, RAMF)
4. **Lateral** — Fullbacks (LB, RB, LWB, RWB)
5. **Central** — Centre-backs (CB, LCB, RCB)
6. **Portero** — Goalkeepers (GK)

Los percentiles, el MARCA ZONAL SCORE y el Swarm siempre calculan DENTRO del grupo.

---

## 📝 NOTAS PARA CLAUDE

### Antes de Empezar

1. Leer este archivo completo
2. Revisar `git log --oneline -10` para entender estado reciente
3. Identificar qué página/utilidad es relevante
4. Leer el archivo antes de modificarlo

### Restricciones

- ✅ Modificar `pages/`, `utils/`, `app.py`, `Inicio.py` → OK
- ❌ Modificar `.streamlit/` → Preguntar primero
- ✅ Crear nuevas carpetas (`api/`, `mobile/`) → OK para roadmap

### Workflow Recomendado

```
1. ANALIZAR  → Leer archivos relevantes, entender estructura
2. IMPLEMENTAR → Cambios en código
3. VALIDAR  → python -m py_compile pages/archivo.py
4. PROBAR LOCAL → streamlit run app.py (http://localhost:8501)
5. COMMIT Y PUSH → git add, commit, push
6. ESPERAR → 20+ min para que Streamlit Cloud redeploy
7. VERIFICAR → https://marcazonal.streamlit.app + Ctrl+Shift+R
```

### Debugging Frecuente

**ImportError:**
```python
from pathlib import Path
APP_DIR = Path(__file__).parent.parent  # desde pages/ sube un nivel
```

**Cache no actualiza:**
```python
# @st.cache_data no invalida solo
# Solución: borrar .streamlit/cache/ o usar ttl=3600
```

**Gráfico no aparece:**
```python
st.write(df.head())  # debug datos antes del gráfico
```

**Streamlit Cloud no actualizó:**
- Esperar 20+ minutos
- Ir a share.streamlit.io → Force Deploy / Rerun
- Revisar logs de deployment

### Git Workflow

```bash
git log --oneline -10          # ver historial
git log origin/main..HEAD      # commits sin pushear
git status                     # estado actual
git diff origin/main           # cambios completos
git revert HEAD && git push    # emergencia: revertir
```

### Preguntas Frecuentes

**P: ¿Puedo agregar una nueva liga para Similares?**
A: Sí. Agregar `LIGA.xlsx` en `data/`, agregar `df_liga = load_external_league('LIGA')` al inicio de Jugadores.py, y wired en el filtro de ligas del Tab 5.

**P: ¿Puedo agregar nuevas métricas?**
A: Sí, en `utils/data_processing.py`. Se propagan globalmente.

**P: ¿Cómo actualizo los datos?**
A: El usuario reemplaza el Excel manualmente. La app detecta cambios automáticamente (cache por sesión).

**P: ¿Puedo modificar el MARCA ZONAL SCORE?**
A: Sí. Los pesos están en `_resolve_scout_weights()` dentro de `_get_scout_score_data()` en Jugadores.py (~línea 1345).

---

## 🚀 ROADMAP: HACIA LA APP MÓVIL

### Objetivo Final
App móvil (iOS/Android) que consuma los mismos datos sin modificar la app Streamlit.

### Fase 1: API Backend ⏳ (Próxima)
**Framework:** FastAPI + reutilizar `utils/data_processing.py`  
**Carpeta:** `api/` (nueva, no toca Streamlit)

**Endpoints prioritarios:**
```
GET /players                  → Lista con filtros
GET /players/{id}/stats       → Estadísticas completas
GET /players/{id}/percentiles → Percentiles por grupo
GET /teams                    → Lista de equipos
GET /predict                  → Predicción de partido (Poisson)
GET /similar                  → Jugadores similares (PCA)
```

### Fase 2: Sincronización de Datos ⏳
- Opción A: API lee Excel directamente (simple)
- Opción B: Script semanal Excel → SQLite (mejor performance)

### Fase 3: App Móvil ⏳
Framework candidato: React Native o Flutter  
Pantallas: Lista jugadores, Perfil, Comparador, Predictor, Rankings

### Fase 4: Deploy ⏳
API en Railway/Render + publicación App Store/Google Play

---

## 🎯 RESUMEN EJECUTIVO

| Aspecto | Status | Notas |
|---------|--------|-------|
| **App Streamlit** | ✅ En producción | 3 páginas, datos Apertura 2026 |
| **Jugadores.py** | ✅ 8 tabs completos | Scout, Swarm, Mejor Once, PCA multi-liga |
| **Predictor.py** | ✅ Funcional | Poisson sin scipy |
| **Tiempo Efectivo** | ✅ Funcional | 12 equipos, formato HH:MM:SS |
| **Ligas comparación** | ✅ 7 ligas | PAR, ARG, BRA, URU, COL, ECU, CHI |
| **Vista Scout + PNG** | ✅ Operativo | scout_html.py + dom-to-image |
| **MARCA ZONAL SCORE** | ✅ Por posición | Pesos diferenciados por grupo |
| **App Móvil** | 🚧 Planificación | Fase 1: API Backend pendiente |

---

**Última actualización:** 2026-04-20  
**Próxima revisión:** Al iniciar Fase 1 (API Backend)
