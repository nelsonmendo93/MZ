# 📚 Documentación del Proyecto Marca Zonal

**Índice de documentos disponibles en la carpeta futbol-app**

---

## 📄 Documentos de Referencia

### 1. **CLAUDE.md** (22 KB) ⭐ PRINCIPAL
**Propósito:** Documentación completa del proyecto para Claude en futuras sesiones

**Contenido:**
- ✅ Estado actual del proyecto
- ✅ Cómo ejecutar la app
- ✅ Arquitectura completa (3 páginas + utils)
- ✅ Estructura de carpetas detallada
- ✅ Explicación de cada archivo (propósito, LOC, funciones)
- ✅ Estructura de datos (database.xlsx con 80+ columnas)
- ✅ Componentes clave (colores, tipografía, posiciones)
- ✅ Intentos anteriores y lecciones aprendidas
- ✅ Sesión Tiempo Efectivo: qué pasó y lecciones
- ✅ Roadmap hacia app móvil (4 fases)
- ✅ Notas para Claude (FAQ, debugging, workflow)

**Cuándo leerlo:**
- Al iniciar una nueva sesión
- Antes de hacer cambios al proyecto
- Para entender la arquitectura
- Para resolver problemas

---

### 2. **ROADMAP.md** (3.0 KB)
**Propósito:** Plan detallado hacia la construcción de la app móvil

**Contenido:**
- Objetivo final: App móvil (iOS/Android)
- Fase 1: API Backend (FastAPI)
- Fase 2: Sincronización de datos
- Fase 3: App móvil (React Native/Flutter)
- Fase 4: Deploy y distribución
- Restricciones importantes
- Notas técnicas

**Importante:**
- ❌ NO modificar Streamlit mientras se desarrolla API
- ✅ Todo código nuevo en carpetas `api/`, `mobile/`, etc.

---

### 3. **CLAUDE_SESION_TIEMPO_EFECTIVO.md** (8.7 KB)
**Propósito:** Documentación específica de la sesión Tiempo Efectivo

**Contenido:**
- Estado actual: ⚠️ Código OK, deployment falló
- Situación: No funciona en Streamlit Cloud
- Historial de intentos (5 intentos diferentes)
- Análisis del problema
- Próximos pasos (4 opciones)
- Recomendaciones para futuros trabajos
- Datos validados (12 equipos)
- Tabla de verificación completa

**Lección clave:**
- La implementación técnica fue exitosa
- El problema está en Streamlit Cloud, no en el código
- Próxima vez: esperar 20+ minutos, revisar logs

---

### 4. **requirements.txt** (103 bytes)
**Propósito:** Dependencias del proyecto

**Librerías:**
```
streamlit              ← Framework web
pandas                 ← Manipulación de datos
matplotlib             ← Gráficos
mplsoccer (PyPizza)    ← Radares de fútbol
Pillow                 ← Procesamiento de imágenes
requests               ← HTTP requests
numpy                  ← Cálculos numéricos
openpyxl               ← Lectura de Excel
adjustText             ← Evitar superposición de labels
scikit-learn           ← Machine learning (PCA)
```

**Instalar:**
```bash
pip install -r requirements.txt
```

---

### 5. **packages.txt** (15 bytes)
**Propósito:** Dependencias del sistema (para DevContainer)

**Contenido:** Vacío o minimal (solo Streamlit las necesita)

---

## 📊 Comparación de Documentos

| Documento | Tamaño | Nivel | Propósito | Lector |
|-----------|--------|-------|----------|--------|
| CLAUDE.md | 22 KB | Completo | Referencia general | Claude + Usuario |
| ROADMAP.md | 3 KB | Alto nivel | Visión a futuro | Usuario |
| CLAUDE_SESION_TIEMPO_EFECTIVO.md | 8.7 KB | Específico | Sesión pasada | Claude |
| requirements.txt | 103 B | Técnico | Dependencias | Sistema |

---

## 🎯 Cómo Usar Esta Documentación

### Para Claude en próximas sesiones:
1. Lee **CLAUDE.md** primero (referencia general)
2. Lee **CLAUDE_SESION_TIEMPO_EFECTIVO.md** para contexto de lo que pasó
3. Lee **ROADMAP.md** para entender dónde va el proyecto

### Para el usuario (Nelson):
1. **ROADMAP.md** → Entender dónde va el proyecto
2. **CLAUDE.md** → Entender cómo está estructurado todo
3. Usar como referencia cuando des instrucciones a Claude

---

## 📝 Últimas Notas

### Qué está documentado:
✅ Arquitectura actual (Streamlit)
✅ Estructura de datos
✅ Intentos anteriores
✅ Sesión Tiempo Efectivo
✅ Roadmap hacia app móvil
✅ FAQ y debugging

### Qué falta documentar:
⏳ API Backend (cuando se cree)
⏳ App móvil (cuando se cree)
⏳ Scripts de automatización

---

**Creado:** Abril 15, 2026
**Próxima actualización:** Después de implementar Fase 1 (API Backend)
