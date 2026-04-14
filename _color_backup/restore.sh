#!/usr/bin/env bash
# Restore all files to their original colors.
# Run from any directory:  bash /path/to/_color_backup/restore.sh
set -e
BACKUP_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$BACKUP_DIR")"

cp "$BACKUP_DIR/app.py"        "$ROOT_DIR/app.py"
cp "$BACKUP_DIR/Inicio.py"     "$ROOT_DIR/Inicio.py"
cp "$BACKUP_DIR/pages/1_📊_Jugadores.py"   "$ROOT_DIR/pages/1_📊_Jugadores.py"
cp "$BACKUP_DIR/pages/2_⚽_Predictor.py"   "$ROOT_DIR/pages/2_⚽_Predictor.py"
cp "$BACKUP_DIR/pages/3_Tiempo_efectivo.py" "$ROOT_DIR/pages/3_Tiempo_efectivo.py"
cp "$BACKUP_DIR/utils/pizza_chart.py"      "$ROOT_DIR/utils/pizza_chart.py"
cp "$BACKUP_DIR/utils/bar_chart.py"        "$ROOT_DIR/utils/bar_chart.py"
cp "$BACKUP_DIR/utils/xy_chart.py"         "$ROOT_DIR/utils/xy_chart.py"

echo "✅ All files restored to original colors."
