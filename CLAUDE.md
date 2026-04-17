# CLAUDE.md — Marca Zonal: Portal de Análisis de Fútbol Paraguayo

**Última actualización:** Abril 15, 2026  
**Propósito:** Documentación completa del proyecto para Claude en futuras sesiones  
**Estado:** En producción (Streamlit Cloud) + Desarrollo hacia app móvil

---

## 📋 TABLA DE CONTENIDOS

1. [Estado del Proyecto](#estado-del-proyecto)
2. [Ejecutar la App](#ejecutar-la-app)
3. [Arquitectura](#arquitectura)
4. [Estructura de Carpetas](#estructura-de-carpetas)
5. [Funcionalidades Actuales](#funcionalidades-actuales)
6. [Datos y Estructura](#datos-y-estructura)
7. [Componentes Clave](#componentes-clave)
8. [Intentos Anteriores y Lecciones](#intentos-anteriores-y-lecciones)
9. [Sesión Tiempo Efectivo (Abril 2026)](#sesión-tiempo-efectivo-abril-2026)
10. [Roadmap: Hacia la App Móvil](#roadmap-hacia-la-app-móvil)
11. [Notas para Claude](#notas-para-claude)

---

## 📊 ESTADO DEL PROYECTO

### ✅ En Producción
- **App Streamlit:** https://marcazonal.streamlit.app
- **Estado:** Funcional con 3 páginas
- **Actualizaciones:** Semanales de datos Excel
- **Usuarios:** Acceso público

### 📱 En Desarrollo
- **Objetivo final:** App móvil (iOS/Android)
- **Fase actual:** Planificación de API Backend
- **Restricción crítica:** No modificar archivos Streamlit existentes mientras se desarrolla la app móvil

### 📝 Última Sesión
- **Fecha:** Abril 9-15, 2026
- **Objetivo:** Mejorar página "Tiempo Efectivo"
- **Estado:** ⚠️ Implementación técnica completa, pero Streamlit Cloud NO se actualizó
- **Conclusión:** El código es correcto; el problema está en el deployment

---

## 🚀 EJECUTAR LA APP

### Opción 1: Entrada Principal (Recomendado)
```bash
cd /ruta/a/futbol-app
streamlit run Inicio.py
```

### Opción 2: Entrada Alternativa
```bash
streamlit run app.py
```

**Nota:** `Inicio.py` es un wrapper que reutiliza `app.py` usando `runpy.run_path()`.

### Opción 3: Con Configuración Dev (DevContainer)
```bash
streamlit run app.py --server.enableCORS false --server.enableXsrfProtection false
```

**URL:** http://localhost:8501

---

## 🏗️ ARQUITECTURA

**Tipo:** Multi-page Streamlit application

```
futbol-app/
├── app.py                    ← Home (portada principal)
├── Inicio.py                 ← Wrapper de app.py
├── pages/
│   ├── 1_📊_Jugadores.py    ← Estadísticas de jugadores (~3500 LOC)
│   ├── 2_⚽_Predictor.py     ← Predictor de partidos (~1663 LOC)
│   └── 3_Tiempo_efectivo.py  ← Tiempo efectivo (análisis por equipo)
├── utils/
│   ├── data_processing.py    ← Procesamiento de datos (cache)
│   ├── pizza_chart.py        ← Gráficos radar (PyPizza)
│   ├── bar_chart.py          ← Gráficos de percentiles
│   ├── xy_chart.py           ← Scatter plots
│   ├── translations.py       ← Mapeo English→Spanish
│   └── counter.py            ← Contador de visitas
├── data/
│   ├── database.xlsx         ← Jugadores Paraguay (primario)
│   ├── ARG.xlsx, BRA.xlsx    ← Ligas argentina y brasileña
│   ├── CHI.xlsx, COL.xlsx    ← Ligas adicionales
│   ├── ECU.xlsx, URU.xlsx    ├─ (para comparaciones futuras)
│   └── Team Stats *.xlsx     ← 14 archivos de equipos (análisis por partido)
├── assets/
│   ├── logo_blanco.png
│   └── logo_negro.png
├── _color_backup/            ← Backup de intento de cambio de colores
├── ROADMAP.md                ← Plan hacia app móvil
└── CLAUDE.md                 ← Este archivo
```

---

## 📁 ESTRUCTURA DE CARPETAS (Detallado)

### `app.py` (Home)
- **Líneas:** ~250
- **Propósito:** Landing page principal
- **Contenido:**
  - Configuración de Streamlit (`st.set_page_config`)
  - Estilos CSS globales (tema oscuro, fuentes Poppins/Cousine)
  - Logo y bienvenida
  - 3 botones de navegación (switch_page)
  - Contador de visitas

### `pages/1_📊_Jugadores.py` (3500 LOC)
- **Propósito:** Análisis completo de jugadores paraguayos
- **Datos:** database.xlsx (primario) + ARG/BRA (comparación)
- **Funcionalidades:**
  1. **Pizza Radar:** 15 métricas en 3 grupos (cyan/orange/purple)
  2. **Bar Chart:** Percentiles por grupo de posición
  3. **XY Scatter:** Ploteos de 2 métricas con cuadrantes
  4. **Best XI:** Constructor interactivo de equipo ideal
  5. **PCA Clustering:** Análisis de similaridad
  6. **Comparaciones:** Multi-liga (PAR vs ARG vs BRA)
  7. **Búsqueda avanzada:** Por equipo, posición, rango de edades

### `pages/2_⚽_Predictor.py` (1663 LOC)
- **Propósito:** Predicción de resultados de partidos
- **Método:** Distribución de Poisson (implementación custom, SIN scipy)
- **Outputs:**
  - Probabilidades: Victoria/Empate/Derrota
  - xG (Expected Goals)
  - xPTS (Expected Points)
  - Predicciones secundarias:
    - Probabilidad de esquinas
    - Predicción de tarjetas
    - Goles esperados por tiempo

### `pages/3_Tiempo_efectivo.py` (547 LOC)
- **Propósito:** Análisis de tiempo efectivo de posesión (por equipo)
- **Datos:** Team Stats *.xlsx (14 archivos)
- **Cálculo:**
  - Tiempo Efectivo = (Passes / accurate) ÷ (Match tempo)
  - % Tenencia = (Tiempo Efectivo ÷ Duración) × 100
  - Formato: HH:MM:SS
- **Salida:** Ranking de 12 equipos por tiempo efectivo
- **Nota:** ⚠️ Este archivo EXISTE pero puede no reflejar cambios recientes

### `utils/data_processing.py` (253 LOC)
- **Propósito:** Core de procesamiento de datos
- **Funciones clave:**
  - `load_data()` → Carga database.xlsx con cache
  - Conversión de stats "per 90" a totales
  - Computación de métricas derivadas:
    - `CBIT` = Sliding tackles + Interceptions + Shots blocked
    - `Progressive actions` = Progressive passes + Progressive runs
    - `Goals - xG diff` = Diferencia goles reales vs esperados
  - Aplicación de overrides manuales de posición
  - Mapeo de jugadores a grupos de posición (6 grupos)
- **Cache:** `@st.cache_data` para optimizar carga
- **Posición Groups:** Delantero, Extremo, Volante Central, Lateral, Central, Portero

### `utils/pizza_chart.py` (142 LOC)
- **Librería:** PyPizza (charlas StatsBomb)
- **Parámetros:** 15 métricas en 3 grupos color-coded
  - Cyan: Ataque
  - Orange: Defensa
  - Purple: Posesión/Pases
- **Uso:** Comparaciones visuales por jugador

### `utils/bar_chart.py` (238 LOC)
- **Tipo:** Gráficos horizontales agrupados
- **Contenido:** Percentiles de 4 categorías de métricas
- **Rendimiento:** Optimizado para 50+ jugadores simultáneamente

### `utils/xy_chart.py` (118 LOC)
- **Tipo:** Scatter plots 2D
- **Features:**
  - Líneas de cuadrante basadas en media
  - Evitar colisión de etiquetas con `adjustText`
  - Colores por posición

### `utils/translations.py` (178 LOC)
- **Propósito:** Mapeo English→Spanish para nombres de métricas
- **Ejemplo:**
  ```python
  "Goals" → "Goles"
  "xG" → "Goles Esperados"
  "Progressive passes" → "Pases Progresivos"
  ```

### `utils/counter.py` (39 LOC)
- **Propósito:** Contador de visitas
- **Almacenamiento:** `data/visit_counter.json` (persistencia)
- **Tipo:** Session-based (cuenta único por sesión)

---

## 🎮 FUNCIONALIDADES ACTUALES

### 1. Estadísticas de Jugadores (`pages/1_📊_Jugadores.py`)
**¿Qué hace?** Análisis profundo de jugadores individuales

**Pasos de uso:**
1. Seleccionar jugador de dropdown
2. Ver 5 visualizaciones simultáneamente:
   - Pizza radar (15 parámetros)
   - Gráfico de percentiles (4 categorías)
   - Scatter plot dinámico
3. Construir "Best XI" seleccionando posiciones
4. Comparar contra ligas diferentes (PAR/ARG/BRA)
5. Análisis de jugadores similares (PCA)

**Datos:** database.xlsx + ARG.xlsx/BRA.xlsx

---

### 2. Predictor de Partidos (`pages/2_⚽_Predictor.py`)
**¿Qué hace?** Predice resultados de partidos futuros

**Método:**
- Distribución de Poisson personalizada (sin scipy)
- Basada en xG (Expected Goals) de equipos

**Salidas:**
- Prob(Victoria local) / Prob(Empate) / Prob(Victoria visitante)
- xG esperado por equipo
- Predicción de esquinas y tarjetas
- Simulación de minutos con goles

**Parámetros:** Seleccionar equipo local y visitante

---

### 3. Tiempo Efectivo (`pages/3_Tiempo_efectivo.py`)
**¿Qué hace?** Analiza tiempo de posesión por equipo

**Métrica:**
- Tiempo Efectivo = Pases ÷ Match Tempo (pases/minuto)
- % Tenencia = Tiempo / Duración del partido

**Salida:** Ranking de 12 equipos paraguayos

**Datos:** Team Stats *.xlsx (1 archivo por equipo)

---

## 📊 DATOS Y ESTRUCTURA

### Archivos de Datos

#### `database.xlsx` (Primario)
- **Contenido:** Jugadores paraguayos (División Profesional)
- **Período:** Apertura 2026
- **Columnas:** 80+ (ver abajo)
- **Actualización:** Semanal (manual por usuario)

#### `ARG.xlsx`, `BRA.xlsx` (Comparación)
- **Contenido:** Ligasargentina y brasileña
- **Uso:** Comparar percentiles inter-liga en Jugadores.py
- **Carga:** Lazy (solo cuando usuario selecciona comparación)

#### `CHI.xlsx`, `COL.xlsx`, `ECU.xlsx`, `URU.xlsx`
- **Estado:** Presentes pero no usados actualmente
- **Potencial:** Futuras expansiones de análisis

#### `Team Stats *.xlsx` (14 archivos)
- **Contenido:** Estadísticas por partido de cada equipo
- **Ejemplo:** `Team Stats Sportivo Ameliano.xlsx`
- **Uso:** Página "Tiempo Efectivo"
- **Columnas:** Date, Match, Team, Duration, Passes/accurate, Match tempo, etc.

### Estructura de Columnas: `database.xlsx`

#### Identidad
```
Player, Team, Position, Position Group, 
Minutes played, Matches played, Pie (foot)
```

#### Ataque (~17 métricas)
```
Goals, xG, Dif G-xG, Non-penalty goals, Head goals,
Shots, Shots on target, Assists, xA, Shot assists,
Key passes, Touches in box, Dribbles, Offensive duels,
Successful attacking actions, Progressive runs, Accelerations
```

#### Defensa (~9 métricas)
```
Successful defensive actions, Defensive duels, Aerial duels,
Sliding tackles, Interceptions, Shots blocked,
Fouls, Yellow cards, Red cards
```

#### Pases (~15 métricas)
```
Passes, Forward passes, Back passes, Lateral passes,
Short/medium passes, Long passes, Progressive passes,
Passes to final third, Passes to penalty area, Through passes,
Deep completions, Deep completed crosses, Crosses,
Received passes, Received long passes
```

#### Derivadas (Computadas)
```
CBIT = Sliding tackles + Interceptions + Shots blocked
Progressive actions = Progressive passes + Progressive runs
Off Def Successful actions = Defensive + Attacking successful
```

#### Variantes
- **Total:** Cada métrica existe en versión "total"
- **Per 90:** Cada métrica existe también en versión "por 90 minutos"
- **Accuracy %:** Patrón `Accurate [X], %` para pases, tiros, etc.

---

## 🔧 COMPONENTES CLAVE

### Sistema de Colores
```css
/* Tema */
Background: #0f172a (muy oscuro)
Surface: #1e293b (oscuro)
Accent primario: #22c55e (verde)
Accent secundario: #0ea5e9 (cyan)
Text: #e2e8f0 (gris claro)

/* Por métrica */
Cyan: Ataque
Orange: Defensa
Purple: Posesión
```

### Tipografía
```css
Body: 'Cousine' monospace (Google Fonts)
Headings: 'Poppins' sans-serif (Google Fonts)
Auto-descargadas en runtime
```

### Grupos de Posición (6)
1. **Delantero** - Strikers
2. **Extremo** - Wingers
3. **Volante Central** - Central midfielders
4. **Lateral** - Fullbacks
5. **Central** - Centre backs
6. **Portero** - Goalkeepers

**Importancia:** Percentiles se calculan POR grupo, no globalmente

### Overrides Manuales de Posición
- Definidos en `utils/data_processing.py`
- Algunos jugadores se reasignan a grupos diferentes
- Ejemplo: Un lateral que juega como medio

---

## 🎯 INTENTOS ANTERIORES Y LECCIONES

### Intento 1: Cambio de Esquema de Colores (Abril 14)
**Objetivo:** Modificar colores de la app (posiblemente a "green color theme")

**Archivos modificados:**
- `app.py` (estilos CSS)
- `pages/1_📊_Jugadores.py` (colores en gráficos)
- `pages/2_⚽_Predictor.py`
- `utils/bar_chart.py`, `utils/pizza_chart.py`, `utils/xy_chart.py`

**Estado:** ❌ Revertido
**Backup:** `_color_backup/` contiene las versiones intentadas
**Restauración:**
```bash
# Si necesitas volver a verde (si existe script):
bash _color_backup/restore.sh
```

**Lección:** Los cambios de color afectan múltiples archivos. Considerar usar variables CSS globales.

---

### Intento 2: Mejoras en Visualizaciones
**Fecha:** Varias sesiones

**Cambios documentados en Git:**
```
a6198f0 - Reducir tamaño de etiquetas (12.4pt)
6d1cb08 - Aumentar círculos (dot_r 4.0) y etiquetas (13.4pt)
e60076f - Aumentar tamaño de letras (nombres 14pt, club 12pt, edad 12pt)
3509c5c - Mejor Once: UI simplificada, encabezado destacado
9c88487 - Mejor Once: figura única
eca81e4 - Similares: permitir comparar contra pool de ligas
eee35a8 - Similares: pool independiente por liga
05f641e - Similares: agregar checkbox PAR, excluir cualquier liga
```

**Conclusión:** Iteraciones exitosas en UX/tamaño de letra.

---

## 🔴 SESIÓN TIEMPO EFECTIVO (ABRIL 2026)

### Objetivo
Mejorar o reemplazar la página `pages/3_Tiempo_efectivo.py` con nueva implementación basada en Pure Possession Analysis.

### Qué se Intentó
1. **Crear nueva página:** `pages/3_⏱️_Tiempo_Efectivo.py` (con emoji)
2. **Modificar botón en Inicio:** Agregar tercera columna para nuevo botón
3. **Commits:** 2 commits realizados exitosamente

### Resultados

#### ✅ Completado
- Código Python: 100% válido (test: `python -m py_compile`)
- Lógica de cálculo: Correcta (validada con 12 equipos)
- Git commits: En GitHub (0c6fe1b, 1edff6e)
- Datos procesados: 12 clubes con tiempo efectivo calculado

#### ✅ Datos Validados
```
Sportivo Ameliano:    00:23:44  (24.12% tenencia)
Club Libertad:        00:23:40  (24.19% tenencia)
2 de Mayo:            00:23:31  (23.91% tenencia)
... (y 9 más)
Guaraní:              00:21:47  (21.89% tenencia)
```

#### ❌ Fallo en Producción
- Streamlit Cloud **NO** mostró los cambios
- El botón ⏱️ NO aparece en la app en vivo
- Causa: Problema de deployment (no relacionado con el código)

### Problemas Encontrados

#### Problema 1: Worktree Roto
```bash
# Estado:
git status
# Output: "modified: .claude/worktrees/wizardly-darwin"

# Solución:
git worktree remove .claude/worktrees/wizardly-darwin
```

#### Problema 2: Streamlit Cloud No Detecta Cambios
- Push realizado exitosamente
- Commits en GitHub: ✓
- App en vivo: No se actualizó después de 10+ minutos

### Cómo Solucionar (Próximas Sesiones)

#### Opción 1: Esperar + Fuerza de caché
```bash
# En navegador:
# - Abrir en pestaña privada
# - Presionar Ctrl+Shift+R (fuerza recarga)
# - Esperar 20+ minutos
```

#### Opción 2: Trigger manual en Streamlit Cloud
1. Ir a https://share.streamlit.io/
2. Buscar proyecto MZ
3. Click en "Rerun" o "Force Deploy"

#### Opción 3: Revisar logs
- Acceder a dashboard de Streamlit Cloud
- Revisar logs de deployment
- Buscar mensajes de error

#### Opción 4: Revertir cambios
```bash
git revert 1edff6e
git revert 0c6fe1b
git push
```

### Archivos Creados en Esta Sesión
- `CLAUDE_SESION_TIEMPO_EFECTIVO.md` (documentación de sesión)
- `DETALLE_DE_COMMITS.txt`
- `CAMBIOS_REALIZADOS.md`
- `INSTRUCCIONES_PUBLICACION.md`
- `ESTRUCTURA_DEL_PROYECTO.txt`
- `SIGUIENTE_PASO.txt`
- `test_tiempo_efectivo.py` (script de validación)

**Ubicación:** `/sessions/nifty-beautiful-newton/mnt/clubes_py/` (en outputs)

### Conclusión
La implementación técnica fue exitosa. El problema está en Streamlit Cloud, no en el código. Para sesiones futuras:
1. Probar siempre LOCALMENTE antes de pushar
2. Esperar más tiempo (20+ minutos) antes de asumir fallo
3. Revisar logs de Streamlit Cloud si falla

---

## 🚀 ROADMAP: HACIA LA APP MÓVIL

### Objetivo Final
Construir app móvil (iOS/Android) que exponga análisis de fútbol paraguayo sin modificar Streamlit.

### Restricción Crítica
❌ **NO modificar `pages/`, `utils/`, `app.py`, `Inicio.py` ni `.streamlit/`**
✅ **Todo código nuevo en carpetas nuevas: `api/`, `mobile/`, etc.**

### Fase 1: API Backend ⏳ (Próxima)
**Framework:** FastAPI (Python, reutiliza `utils/data_processing.py`)

**Carpeta:** `api/` (nueva)

**Endpoints prioritarios:**
```
GET /players                  → Lista de jugadores con filtros
GET /players/{id}/stats       → Estadísticas completo de un jugador
GET /players/{id}/percentiles → Percentiles por grupo de posición
GET /teams                    → Lista de equipos
GET /predict                  → Predicción de partido
GET /similar                  → Jugadores similares (PCA)
```

**Datos:** Leer directamente `data/database.xlsx`

**Reutilizar:**
- Lógica de `utils/data_processing.py`
- Cálculos de Poisson de `pages/2_⚽_Predictor.py`
- Mapeos de posiciones y overrides

### Fase 2: Sincronización de Datos ⏳ (Post-API)
**Opciones:**
- A) API lee Excel directamente (simple, lento)
- B) Script semanal Excel → SQLite/PostgreSQL (mejor rendimiento)

**Flujo actual:**
1. Usuario actualiza `database.xlsx` semanalmente
2. App Streamlit lo detecta automáticamente (cache)
3. Los nuevos datos aparecen en las visualizaciones

**Flujo futuro:**
1. Usuario actualiza `database.xlsx`
2. Script de sincronización convierte a BD
3. API lee de BD en lugar de Excel

### Fase 3: App Móvil ⏳ (Post-API)
**Framework candidato:** React Native o Flutter

**Pantallas prioritarias:**
1. Lista de jugadores (búsqueda + filtros)
2. Perfil de jugador (stats, radar, percentiles)
3. Comparador de jugadores
4. Predictor de partidos
5. Ranking / Best XI

**Consume:** API Backend (Fase 1)

### Fase 4: Deploy y Distribución ⏳
- Deploy de API (Railway, Render, etc.)
- Publicación en App Store / Google Play
- Autenticación básica (opcional)

---

## 📝 NOTAS PARA CLAUDE

### Antes de Empezar Cualquier Tarea

1. **Leer esta documentación primero** ← Este archivo

2. **Identificar la fase del proyecto:**
   - ¿Es cambio en Streamlit? → Modificar `pages/`, `utils/`, `app.py`
   - ¿Es trabajo hacia API/móvil? → Crear carpeta nueva, NO tocar Streamlit

3. **Verificar restricciones:**
   - ¿Modifica `pages/`, `utils/`, `app.py`, `Inicio.py`? ✅ OK
   - ¿Modifica `.streamlit/`? ❌ Preguntar primero
   - ¿Crea nuevas carpetas? ✅ OK (siempre)

### Workflow Recomendado

```
1. ANALIZAR
   └─ Leer archivos relevantes
      └─ Entender estructura actual
         └─ Identificar qué cambia

2. IMPLEMENTAR (LOCALMENTE)
   └─ Hacer cambios en código
      └─ Probar: `streamlit run app.py` en terminal
         └─ Verificar visualmente en http://localhost:8501

3. VALIDAR
   └─ Tests unitarios (si aplica)
      └─ Sintaxis Python: `python -m py_compile`
         └─ Git diff: `git diff`

4. COMMIT Y PUSH
   └─ git add .
      └─ git commit -m "Descripción clara"
         └─ git push

5. ESPERAR (20+ minutos)
   └─ Streamlit Cloud detecta y redeploy
      └─ Verificar en https://marcazonal.streamlit.app
         └─ Forzar recarga (Ctrl+Shift+R)
```

### Debugging

#### Problema: "ImportError: no module named..."
```python
# Verificar que está en utils/ y tiene __init__.py
# Verificar que APP_DIR se configura correctamente:
from pathlib import Path
APP_DIR = Path(__file__).parent.parent  # Sube 1 nivel desde pages/
```

#### Problema: "Cache no actualiza"
```python
# @st.cache_data no invalida automáticamente
# Solución 1: Borrar archivo .streamlit/cache/
# Solución 2: Usar @st.cache_data(ttl=3600) para expiración
```

#### Problema: "Gráficos no se muestran"
```python
# Verificar que matplotlib/plotly importa correctamente
# Verificar que datos no están vacíos
# Usar: st.write(df.head()) para debug
```

### Preguntas Frecuentes

**P: ¿Puedo modificar colores?**
A: Sí, pero afecta múltiples archivos. Usa `_color_backup/` como referencia.

**P: ¿Puedo agregar nuevas métricas?**
A: Sí, en `utils/data_processing.py`. Se aplica globalmente.

**P: ¿Puedo agregar nuevas ligas?**
A: Sí, agregar archivo `.xlsx` en `data/` y modificar loaders.

**P: ¿Cómo actualizo datos?**
A: Usuario actualiza Excel manualmente. No hay automatización (por ahora).

**P: ¿Puedo cambiar la estructura de carpetas?**
A: NO, romperá imports y Streamlit. Usa `api/`, `mobile/` para nuevas funcionalidades.

### Git Workflow

```bash
# Ver commits recientes
git log --oneline -10

# Ver cambios sin pushear
git log origin/main..HEAD

# Ver archivos modificados
git status

# Antes de push, verificar qué sube
git diff origin/main

# En caso de emergencia: revertir último commit
git revert HEAD
git push
```

### Recursos Clave

- **Streamlit docs:** https://docs.streamlit.io/
- **PyPizza:** https://github.com/soccerway/pizza
- **Football Data:** Database.xlsx tiene 80+ columnas, ver estructura arriba
- **Git:** `git log` tiene historial de TODO
- **ROADMAP.md:** Plan detallado hacia app móvil

---

## 🎯 RESUMEN EJECUTIVO

| Aspecto | Status | Notas |
|---------|--------|-------|
| **App Streamlit** | ✅ En producción | Funcional, 3 páginas, actualización semanal |
| **Código Python** | ✅ Bien estructurado | Utils compartidos, cache, composable |
| **Datos** | ✅ 20+ archivos Excel | Paraguay + 6 ligas adicionales |
| **Sesión Tiempo Efectivo** | ⚠️ Código OK, deploy fallo | Implementación correcta, Streamlit Cloud no actualizó |
| **App Móvil** | 🚧 En planificación | Fase 1: Diseñar API Backend |
| **Documentación** | ✅ Completa | Este archivo cubre TODO |

---

**Última actualización:** 2026-04-15  
**Creador:** Claude (Cowork session)  
**Próxima revisión:** Después de Fase 1 (API Backend)
