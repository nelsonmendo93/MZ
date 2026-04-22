import pandas as pd
import streamlit as st
import os

# Per-90 columns to convert to totals
PER_90_COLUMNS = [
    'Duels per 90', 'Successful defensive actions per 90', 'Defensive duels per 90',
    'Aerial duels per 90', 'Sliding tackles per 90', 'Shots blocked per 90',
    'Interceptions per 90', 'Fouls per 90', 'Yellow cards per 90', 'Red cards per 90',
    'Successful attacking actions per 90', 'Goals per 90', 'Non-penalty goals per 90',
    'xG per 90', 'Head goals per 90', 'Shots per 90', 'Assists per 90',
    'Crosses per 90', 'Crosses from left flank per 90', 'Crosses from right flank per 90',
    'Crosses to goalie box per 90', 'Dribbles per 90', 'Offensive duels per 90',
    'Touches in box per 90', 'Progressive runs per 90', 'Accelerations per 90',
    'Received passes per 90', 'Received long passes per 90', 'Fouls suffered per 90',
    'Passes per 90', 'Forward passes per 90', 'Back passes per 90', 'Lateral passes per 90',
    'Short / medium passes per 90', 'Long passes per 90', 'xA per 90',
    'Shot assists per 90',
    'Smart passes per 90', 'Key passes per 90', 'Passes to final third per 90',
    'Passes to penalty area per 90', 'Through passes per 90', 'Deep completions per 90',
    'Deep completed crosses per 90', 'Progressive passes per 90', 'Exits per 90'
    # Nota: 'Second assists per 90' y 'Third assists per 90' se excluyen intencionalmente
]

# Columnas per-90 que se eliminan del df (no se muestran en la app)
EXCLUDED_COLUMNS = [
    'Second assists per 90',
    'Third assists per 90',
    'Second assists',
    'Third assists',
    'Smart passes per 90',
    'Accurate smart passes, %',
    'Accurate smart passes per 90'
    
]

# Overrides manuales de posición: se aplican sobre cualquier database descargada
PLAYER_POSITION_OVERRIDES = {
    'F. Cardozo':    'RCMF',
    'L. Amarilla':   'CF',
    'D. Rodríguez':  'LW',
    'R. Prieto':     'LW',
    'F. Carrizo':    'LW',
    'Brahian Ayala': 'LCMF',
    'C. Miño':       'RW',
    'A. Benítez':    'RB',
    'H. Fernández':  'LW',
    'A. González':  'LW',
    'E. Vera':      'LAMF'
}

# Renombrado de jugadores con nombre idéntico: clave (Player, Team) -> nombre final
# Modificar el valor para diferenciar jugadores homónimos dentro de la misma liga
PLAYER_NAME_OVERRIDES = {
    # ─────────────── PAR ───────────────
    ('Alan Benítez', 'Club Libertad'): 'Alan Benítez',  # RAMF | 32 años | 470 min
    ('Alan Cano', 'Sportivo Trinidense'): 'Alan Cano',  # CF | 21 años | 143 min
    ('Alexis Cañete', 'Nacional Asunción'): 'Alexis Cañete',  # RCB | 22 años | 1567 min
    ('Axel Cañete', 'Sportivo Trinidense'): 'Axel Cañete',  # RB | 24 años | 660 min
    ('Alexis Duarte', 'Club Libertad'): 'Alexis Duarte',  # LCB | 25 años | 29 min
    ('Alex Franco', 'Olimpia'): 'Alex Franco',  # RCMF | 24 años | 735 min
    ('Angel González', 'Club Libertad'): 'Angel González',  # GK | 23 años | 97 min
    ('Aldo González', 'Deportivo Recoleta'): 'Aldo González',  # CF | 29 años | 858 min
    ('Alan Gómez', '2 de Mayo'): 'Alan Gómez',  # RW | 23 años | 882 min
    ('Alexandro Maidana', 'Guaraní'): 'Alexandro Maidana',  # LB | 20 años | 512 min
    ('Amin Molinas', 'Club Libertad'): 'Amin Molinas',  # LCMF | 20 años | 710 min
    ('Antonio Oviedo', 'Sportivo San Lorenzo'): 'Antonio Oviedo',  # CF | 29 años | 176 min
    ('Aldo Pérez', 'Guaraní'): 'Aldo Pérez',  # GK | 25 años | 104 min
    ('Alex Álvarez', 'Sportivo San Lorenzo'): 'Alex Álvarez',  # CF | 28 años | 694 min
    ('Clementino González', 'Sportivo Trinidense'): 'Clementino González',  # CF | 35 años | 1067 min
    ('Cesar Ramírez', 'Guaraní'): 'Cesar Ramírez',  # LCB | 22 años | 63 min
    ('Diego Fernández', 'Guaraní'): 'Diego Fernández',  # RW | 23 años | 868 min
    ('Derlis Rodríguez', 'Guaraní'): 'Derlis Rodríguez',  # LWF | 28 años | 951 min
    ('Estifen Díaz', 'Club Libertad'): 'Estifen Díaz',  # RW | 21 años | 69 min
    ('Fernando Benítez', 'Sportivo Luqueño'): 'Fernando Benítez',  # DMF | 26 años | 576 min
    ('Fernando Díaz', 'Nacional Asunción'): 'Fernando Díaz',  # LB | 25 años | 958 min
    ('Fernando Fernández', 'Guaraní'): 'Fernando Fernández',  # CF | 34 años | 651 min
    ('Fabrizio Jara', 'Nacional Asunción'): 'Fabrizio Jara',  # RCMF | 23 años | 784 min
    ('Fernando Romero', 'Sportivo Trinidense'): 'Fernando Romero',  # CF | 25 años | 1025 min
    ('Fernando J. Román', 'Sportivo Trinidense'): 'Fernando J. Román',  # RCB | 25 años | 121 min
    ('Fredy Vera', 'Sportivo Ameliano'): 'Fredy Vera',  # RAMF | 27 años | 833 min
    ('Fernando Martínez', 'Rubio Ñú'): 'Fernando Martínez',  # RCMF | 31 años | 1319 min
    ('Angel G. Benítez', 'Cerro Porteño'): 'Angel G. Benítez',  # LB | 32 años | 469 min
    ('Gaston Benítez', 'Nacional Asunción'): 'Gaston Benítez',  # LCB | 23 años | 208 min
    ('Gustavo Viera', 'Sportivo Trinidense'): 'Gustavo Viera',  # RCMF | 30 años | 1042 min
    ('Hugo J. Benítez', 'Nacional Asunción'): 'Hugo J. Benítez',  # CF | 22 años | 451 min
    ('Hugo A. Benítez', 'Sportivo Ameliano'): 'Hugo A. Benítez',  # RB | 27 años | 8 min
    ('Ivan Ramírez', 'Club Libertad'): 'Ivan Ramírez',  # RB | 31 años | 868 min
    ('Jonathan Benítez', 'Sportivo Ameliano'): 'Jonathan Benítez',  # LDMF | 25 años | 1223 min
    ('Juan A. Franco', 'Deportivo Recoleta'): 'Juan A. Franco',  # RCMF | 23 años | 1274 min
    ('Jorge D. González', 'Rubio Ñú'): 'Jorge D. González',  # LCB | 29 años | 330 min
    ('Julio González', 'Sportivo Ameliano'): 'Julio González',  # RCB | 33 años | 1580 min
    ('Juan I. Núñez', 'Deportivo Recoleta'): 'Juan I. Núñez',  # LCB | 36 años | 162 min
    ('Dani Pérez', 'Guaraní'): 'Dani Pérez',  # RB | 32 años | 969 min
    ('John Jairo Sánchez', 'Guaraní'): 'John Jairo Sánchez',  # RWF | 26 años | 557 min
    ('Jonatan Torres', 'Cerro Porteño'): 'Jonatan Torres',  # CF | 29 años | 632 min
    ('Luis Ayala', 'Sportivo Ameliano'): 'Luis Ayala',  # RW | 20 años | 530 min
    ('L. González Gamarra', 'Nacional Asunción'): 'L. González Gamarra',  # CF | 28 años | 463 min
    ('Lucas D. González', 'Sportivo Trinidense'): 'Lucas D. González',  # RCMF | 21 años | 510 min
    ('Lucas Gómez', 'Rubio Ñú'): 'Lucas Gómez',  # RCB | 20 años | 388 min
    ('Luis Martínez', 'Guaraní'): 'Luis Martínez',  # DMF | 26 años | 985 min
    ('Fernando M. Cáceres', '2 de Mayo'): 'Fernando M. Cáceres',  # CF | 29 años | 494 min
    ('Marcelo Fernández', 'Club Libertad'): 'Marcelo Fernández',  # RW | 24 años | 236 min
    ('Marcos Gómez', 'Guaraní'): 'Marcos Gómez',  # RCMF | 24 años | 76 min
    ('Matias López', 'Guaraní'): 'Matias López',  # RCMF | 22 años | 1046 min
    ('Mario López', 'Sportivo San Lorenzo'): 'Mario López',  # LCB | 30 años | 1207 min
    ('Miguel Martínez', 'Sportivo Ameliano'): 'Miguel Martínez',  # GK | 27 años | 1580 min
    ('Roberto Martínez', 'Sportivo San Lorenzo'): 'Roberto Martínez',  # LW | 31 años | 233 min
    ('Matias Pérez', 'Cerro Porteño'): 'Matias Pérez',  # LCB | 27 años | 1164 min
    ('Pedro Álvarez', 'Rubio Ñú'): 'Pedro Álvarez',  # LB | 25 años | 544 min
    ('Romeo Benítez', 'Olimpia'): 'Romeo Benítez',  # LWF | 23 años | 106 min
    ('Raul Cabral', 'Sportivo Ameliano'): 'Raul Cabral',  # AMF | 21 años | 927 min
    ('Roberto Fernández', 'Cerro Porteño'): 'Roberto Fernández',  # GK | 38 años | 98 min
    ('Rodrigo Gómez', 'Cerro Porteño'): 'Rodrigo Gómez',  # RB | 19 años | 286 min
    ('Roberto Ramírez', 'Nacional Asunción'): 'Roberto Ramírez',  # RCMF | 25 años | 1074 min
    ('Rodney Redes', 'Olimpia'): 'Rodney Redes',  # RWF | 26 años | 181 min
    ('R. Rodríguez', '2 de Mayo'): 'R. Rodríguez',  # RB | 24 años | 272 min
    ('Robert Rojas', 'Club Libertad'): 'Robert Rojas',  # RCB | 29 años | 330 min
    ('Richard Sánchez', 'Olimpia'): 'Richard Sánchez',  # RCMF | 30 años | 432 min
    ('Sergio Díaz', 'Sportivo Luqueño'): 'Sergio Díaz',  # LW | 28 años | 679 min
    ('Stevens Gómez', 'Rubio Ñú'): 'Stevens Gómez',  # LCMF | 26 años | 27 min
    ('Sergio Mendoza', 'Sportivo Trinidense'): 'Sergio Mendoza',  # LB | 31 años | 999 min
    ('Ángel I. Martínez', '2 de Mayo'): 'Ángel I. Martínez',  # GK | 23 años | 1575 min
    ('Álvaro Martínez', 'Sportivo Luqueño'): 'Álvaro Martínez',  # LB | 24 años | 755 min
    ('Óscar Romero', '2 de Mayo'): 'Óscar Romero',  # LCMF | 27 años | 706 min
    # ─────────────── ARG ───────────────
    ('A. Benítez', 'Belgrano'): 'A. Benítez',  # RB | 23 años | 905 min
    ('A. Cardozo', 'Lanús'): 'A. Cardozo',  # LCMF | 28 años | 1163 min
    ('A. Fernández', 'Racing Club'): 'A. Fernández',  # LCMF | 24 años | 601 min
    ('A. Maidana', 'Talleres Córdoba'): 'A. Maidana',  # LB | 20 años | 410 min
    ('A. Maldonado', 'Belgrano'): 'A. Maldonado',  # RCB | 28 años | 795 min
    ('A. Martínez', 'Huracán'): 'A. Martínez',  # RW | 29 años | 420 min
    ('A. Martínez', 'Racing Club'): 'A. Martínez',  # CF | 33 años | 976 min
    ('A. Medina', 'Lanús'): 'A. Medina',  # RCMF | 19 años | 675 min
    ('A. Molinas', 'Defensa y Justicia'): 'A. Molinas',  # LCMF | 25 años | 1268 min
    ('A. Moreno', 'River Plate'): 'A. Moreno',  # DMF | 26 años | 1207 min
    ('A. Méndez', "Newell's Old Boys"): 'A. Méndez',  # RB | 30 años | 1012 min
    ('A. Oviedo', 'Tigre'): 'A. Oviedo',  # CF | 30 años | 331 min
    ('A. Sosa', 'Aldosivi'): 'A. Sosa',  # CF | 22 años | 556 min
    ('A. Sánchez', 'Belgrano'): 'A. Sánchez',  # RCMF | 26 años | 1114 min
    ('B. Cabrera', 'Lanús'): 'B. Cabrera',  # RW | 22 años | 338 min
    ('B. Cabrera', "Newell's Old Boys"): 'B. Cabrera',  # RCB | 28 años | 355 min
    ('B. Rodríguez', 'Racing Club'): 'B. Rodríguez',  # RCMF | 22 años | 463 min
    ('C. Medina', 'Estudiantes'): 'C. Medina',  # AMF | 23 años | 471 min
    ('D. Fernández', 'Defensa y Justicia'): 'D. Fernández',  # LCB | 25 años | 790 min
    ('D. Martínez', 'Barracas Central'): 'D. Martínez',  # RB | 36 años | 417 min
    ('D. Martínez', 'Defensa y Justicia'): 'D. Martínez',  # LCB | 28 años | 956 min
    ('D. Romero', 'Tigre'): 'D. Romero',  # CF | 23 años | 808 min
    ('E. Martínez', 'Gimnasia La Plata'): 'E. Martínez',  # LCB | 27 años | 1369 min
    ('E. Meza', 'Estudiantes'): 'E. Meza',  # RB | 27 años | 931 min
    ('F. Jara', 'Instituto'): 'F. Jara',  # CF | 37 años | 634 min
    ('F. Pardo', 'Racing Club'): 'F. Pardo',  # RCB | 29 años | 519 min
    ('F. Perez', 'Estudiantes'): 'F. Perez',  # LW | 20 años | 858 min
    ('F. Romero', 'Estudiantes Río Cuarto'): 'F. Romero',  # DMF | 27 años | 757 min
    ('F. Román', 'Aldosivi'): 'F. Román',  # LB | 27 años | 1065 min
    ('F. Sanguinetti', 'Banfield'): 'F. Sanguinetti',  # GK | 25 años | 1280 min
    ('F. Torres', 'Gimnasia La Plata'): 'F. Torres',  # LW | 26 años | 610 min
    ('F. Vera', 'Huracán'): 'F. Vera',  # RB | 28 años | 487 min
    ('F. Álvarez', 'Argentinos Juniors'): 'F. Álvarez',  # RCB | 26 años | 1165 min
    ('F. Álvarez', 'Tigre'): 'F. Álvarez',  # LB | 31 años | 1190 min
    ('Fernando Martínez', 'Central Córdoba SdE'): 'Fernando Martínez',  # RW | 25 años | 394 min
    ('G. Rodríguez', 'San Lorenzo'): 'G. Rodríguez',  # LAMF | 26 años | 550 min
    ('I. González', 'Gimnasia Mendoza'): 'I. González',  # LCB | 28 años | 634 min
    ('I. Méndez', 'Instituto'): 'I. Méndez',  # LCMF | 28 años | 616 min
    ('I. Ramírez', "Newell's Old Boys"): 'I. Ramírez',  # CF | 29 años | 423 min
    ('I. Tapia', 'Barracas Central'): 'I. Tapia',  # LCMF | 27 años | 1055 min
    ('J. Arias', 'Aldosivi'): 'J. Arias',  # CF | 32 años | 776 min
    ('J. Caicedo', 'Huracán'): 'J. Caicedo',  # CF | 28 años | 1132 min
    ('J. Ceballos', 'Gimnasia Mendoza'): 'J. Ceballos',  # RW | 21 años | 413 min
    ('J. Fernández', 'Rosario Central'): 'J. Fernández',  # LW | 22 años | 585 min
    ('J. Franco', 'Gimnasia Mendoza'): 'J. Franco',  # RB | 34 años | 336 min
    ('J. García', 'Vélez Sarsfield'): 'J. García',  # RB | 24 años | 768 min
    ('J. Gutiérrez', 'Defensa y Justicia'): 'J. Gutiérrez',  # CF | 24 años | 1210 min
    ('J. Gómez', 'Sarmiento'): 'J. Gómez',  # LCMF | 36 años | 353 min
    ('J. Herrera', 'Deportivo Riestra'): 'J. Herrera',  # CF | 34 años | 883 min
    ('J. Palacios', 'Unión Santa Fe'): 'J. Palacios',  # RW | 27 años | 938 min
    ('J. Palomino', 'Talleres Córdoba'): 'J. Palomino',  # LCB | 36 años | 437 min
    ('J. Quintero', 'River Plate'): 'J. Quintero',  # AMF | 33 años | 546 min
    ('J. Romaña', 'San Lorenzo'): 'J. Romaña',  # RCB | 27 años | 1028 min
    ('L. Castro', 'Gimnasia La Plata'): 'L. Castro',  # LCMF | 37 años | 339 min
    ('L. Díaz', 'Atlético Tucumán'): 'L. Díaz',  # CF | 33 años | 886 min
    ('L. González', 'Central Córdoba SdE'): 'L. González',  # LCMF | 25 años | 748 min
    ('L. Gómez', 'Banfield'): 'L. Gómez',  # RW | 22 años | 613 min
    ('L. Gómez', 'Independiente Rivadavia'): 'L. Gómez',  # LB | 30 años | 450 min
    ('L. Morales', 'Belgrano'): 'L. Morales',  # RCB | 35 años | 1150 min
    ('L. Paredes', 'Boca Juniors'): 'L. Paredes',  # DMF | 31 años | 917 min
    ('L. Paredes', 'Gimnasia Mendoza'): 'L. Paredes',  # RB | 23 años | 900 min
    ('L. Rodríguez', 'Aldosivi'): 'L. Rodríguez',  # LB | 32 años | 542 min
    ('L. Ríos', 'Banfield'): 'L. Ríos',  # RCMF | 25 años | 333 min
    ('M. Acuña', 'River Plate'): 'M. Acuña',  # LB | 34 años | 581 min
    ('M. Amondarain', 'Estudiantes'): 'M. Amondarain',  # RDMF | 21 años | 898 min
    ('M. Barrios', 'Platense'): 'M. Barrios',  # RDMF | 27 años | 330 min
    ('M. Cáceres', 'Talleres Córdoba'): 'M. Cáceres',  # RW | 23 años | 478 min
    ('M. Fernández', 'Independiente Rivadavia'): 'M. Fernández',  # CF | 24 años | 954 min
    ('M. García', 'Deportivo Riestra'): 'M. García',  # DMF | 30 años | 501 min
    ('M. García', 'Sarmiento'): 'M. García',  # RCMF | 26 años | 798 min
    ('M. Martínez', 'Sarmiento'): 'M. Martínez',  # LDMF | 33 años | 524 min
    ('M. Moreno', 'Lanús'): 'M. Moreno',  # AMF | 30 años | 432 min
    ('M. Rodríguez', 'Unión Santa Fe'): 'M. Rodríguez',  # RCB | 22 años | 1195 min
    ('M. Sepúlveda', 'Lanús'): 'M. Sepúlveda',  # RAMF | 27 años | 337 min
    ('M. Torres', 'Gimnasia La Plata'): 'M. Torres',  # CF | 28 años | 1155 min
    ('N. Fernández', 'Belgrano'): 'N. Fernández',  # CF | 30 años | 786 min
    ('R. Arias', 'Tigre'): 'R. Arias',  # RCB | 33 años | 335 min
    ('R. Castillo', 'Lanús'): 'R. Castillo',  # CF | 27 años | 397 min
    ('S. Arias', 'Independiente'): 'S. Arias',  # RB | 34 años | 732 min
    # ─────────────── BRA ───────────────
    ('J. Correa', 'Botafogo'): 'J. Correa',  # CF | 31 años | 126 min
    ('L. Pérez', 'Grêmio'): 'L. Pérez',  # DMF | 21 años | 244 min
    # ─────────────── URU ───────────────
    ('A. Muñoz', 'Torque'): 'A. Muñoz',  # CF | 19 años | 23 min
    ('A. Romero', 'Albion'): 'A. Romero',  # RB | 27 años | 860 min
    ('A. Vera', 'Albion'): 'A. Vera',  # LAMF | 22 años | 564 min
    ('E. Castillo', 'Liverpool'): 'E. Castillo',  # LCB | 25 años | 898 min
    ('G. Montes', 'Torque'): 'G. Montes',  # LCMF | 31 años | 565 min
    ('J. Moreno', 'Cerro Largo'): 'J. Moreno',  # GK | 26 años | 391 min
    ('K. Silva', 'Torque'): 'K. Silva',  # RCB | 23 años | 302 min
    ('M. Peralta', 'Danubio'): 'M. Peralta',  # LCMF | 20 años | 878 min
    ('R. Peralta', 'Juventud'): 'R. Peralta',  # LDMF | 22 años | 820 min
    ('S. González', 'Deportivo Maldonado'): 'S. González',  # DMF | 26 años | 263 min
    ('V. Rodríguez', 'Defensor Sporting'): 'V. Rodríguez',  # LB | 24 años | 125 min
    # ─────────────── COL ───────────────
    ('A. Arroyo', 'Fortaleza'): 'A. Arroyo',  # AMF | 24 años | 1404 min
    ('A. Gutiérrez', 'Atlético Bucaramanga'): 'A. Gutiérrez',  # RB | 27 años | 1198 min
    ('A. Ramos', 'América de Cali'): 'A. Ramos',  # CF | 40 años | 130 min
    ('A. Salazar', 'Águilas Doradas'): 'A. Salazar',  # GK | 32 años | 692 min
    ('B. Angulo', 'Jaguares de Córdoba'): 'B. Angulo',  # RCMF | 25 años | 128 min
    ('D. Ramírez', 'Boyacá Chicó'): 'D. Ramírez',  # RW | 25 años | 1052 min
    ('F. Chaverra', 'Medellín'): 'F. Chaverra',  # LWB | 26 años | 1229 min
    ('J. Cuesta', 'Once Caldas'): 'J. Cuesta',  # RB | 28 años | 1576 min
    ('J. Escobar', 'América de Cali'): 'J. Escobar',  # LCMF | 21 años | 1151 min
    ('J. Figueroa', 'Alianza'): 'J. Figueroa',  # RCB | 30 años | 791 min
    ('J. Lovera', 'Jaguares de Córdoba'): 'J. Lovera',  # RCB | 21 años | 228 min
    ('J. Obando', 'Fortaleza'): 'J. Obando',  # LCB | 20 años | 96 min
    ('J. Ortiz', 'Medellín'): 'J. Ortiz',  # LCB | 27 años | 1188 min
    ('J. Salas', 'Fortaleza'): 'J. Salas',  # CF | 22 años | 224 min
    ('J. Sinisterra', 'Fortaleza'): 'J. Sinisterra',  # CF | 17 años | 186 min
    ('J. Soto', 'América de Cali'): 'J. Soto',  # GK | 32 años | 596 min
    ('J. Valoyes', 'Alianza'): 'J. Valoyes',  # RCMF | 16 años | 73 min
    ('K. Moreno', 'Alianza'): 'K. Moreno',  # LCB | 25 años | 387 min
    ('L. Mosquera', 'Deportivo Pereira'): 'L. Mosquera',  # AMF | 23 años | 222 min
    ('N. Hernández', 'América de Cali'): 'N. Hernández',  # LCB | 28 años | 688 min
    # ─────────────── ECU ───────────────
    ('A. Velasco', 'Independiente del Valle'): 'A. Velasco',  # CB | 27 años | 125 min
    ('J. Jiménez', 'Macará'): 'J. Jiménez',  # RCB | 31 años | 100 min
    ('J. Medina', 'LDU Quito'): 'J. Medina',  # RAMF | 31 años | 170 min
    ('J. Quiñones', 'Mushuc Runa'): 'J. Quiñones',  # LCB | 23 años | 122 min
    ('P. Guzmán', 'Aucas'): 'P. Guzmán',  # RCMF | 22 años | 684 min
    # ─────────────── CHI ───────────────
    ('A. Uribe', 'Univ. Concepción'): 'A. Uribe',  # CF | 27 años | 260 min
    ('B. Palacios', 'Universidad Católica'): 'B. Palacios',  # CF | 31 años | 277 min
    ('C. Suárez', 'Concepción'): 'C. Suárez',  # RCB | 39 años | 437 min
    ('C. Zambrano', 'Univ. Concepción'): 'C. Zambrano',  # RW | 17 años | 124 min
    ("F. González", "O'Higgins"): "F. González",  # RW | 25 años | 668 min
    ('J. Fuentes', 'Cobresal'): 'J. Fuentes',  # CB | 31 años | 445 min
    ('J. Vargas', 'La Serena'): 'J. Vargas',  # LWF | 28 años | 850 min
    ("L. Díaz", "O'Higgins"): "L. Díaz",  # LB | 27 años | 291 min
    ('R. Sandoval', 'Cobresal'): 'R. Sandoval',  # LB | 25 años | 345 min
    # ─────────────── PER ───────────────
    ('A. Arroyo', 'UTC Cajamarca'): 'A. Arroyo',  # CF | 32 años | 480 min
    ('A. Duarte', 'Alianza Lima'): 'A. Duarte',  # GK | 32 años | 1001 min
    ('A. Flores', 'Atlético Grau'): 'A. Flores',  # LAMF | 21 años | 58 min
    ('A. González', 'Deportivo Garcilaso'): 'A. González',  # LCMF | 29 años | 813 min
    ('A. Gutiérrez', 'ADT'): 'A. Gutiérrez',  # LB | 25 años | 402 min
    ('A. Gómez', 'Deportivo Garcilaso'): 'A. Gómez',  # RCB | 29 años | 1001 min
    ('A. Muñoz', 'Alianza Atlético'): 'A. Muñoz',  # LDMF | 25 años | 450 min
    ('A. Muñoz', 'UTC Cajamarca'): 'A. Muñoz',  # LAMF | 28 años | 913 min
    ('A. Polo', 'Universitario'): 'A. Polo',  # RB | 31 años | 877 min
    ('A. Quintana', 'Los Chankas'): 'A. Quintana',  # LB | 25 años | 822 min
    ('A. Ramos', 'Melgar'): 'A. Ramos',  # RB | 27 años | 385 min
    ('A. Rodríguez', 'ADT'): 'A. Rodríguez',  # RAMF | 31 años | 330 min
    ('A. Rodríguez', 'Comerciantes Unidos'): 'A. Rodríguez',  # RDMF | 25 años | 662 min
    ('A. Salazar', 'Deportivo Garcilaso'): 'A. Salazar',  # RB | 31 años | 329 min
    ('A. Sánchez', 'Juan Pablo II College'): 'A. Sánchez',  # LCB | 22 años | 1015 min
    ('B. Angulo', 'CD Moquegua'): 'B. Angulo',  # CF | 30 años | 227 min
    ('B. Palacios', 'FC Cajamarca'): 'B. Palacios',  # LAMF | 28 años | 380 min
    ('C. Ramírez', 'CD Moquegua'): 'C. Ramírez',  # RDMF | 25 años | 237 min
    ('C. Zambrano', 'Sport Boys'): 'C. Zambrano',  # CB | 21 años | 111 min
    ('D. Ramírez', 'CD Moquegua'): 'D. Ramírez',  # RCMF | 31 años | 345 min
    ('D. Rodríguez', 'Atlético Grau'): 'D. Rodríguez',  # RWB | 23 años | 145 min
    ('D. Romero', 'Universitario'): 'D. Romero',  # GK | 24 años | 603 min
    ('E. Castillo', 'Alianza Lima'): 'E. Castillo',  # LW | 31 años | 842 min
    ('F. Torres', 'Los Chankas'): 'F. Torres',  # CF | 29 años | 900 min
    ('Gabriel', 'Sporting Cristal'): 'Gabriel',  # RWF | 36 años | 353 min
    ('I. Tapia', 'Atlético Grau'): 'I. Tapia',  # LCB | 27 años | 993 min
    ('J. Bolívar', 'Cusco'): 'J. Bolívar',  # LB | 26 años | 453 min
    ('J. Castillo', 'Alianza Lima'): 'J. Castillo',  # LCMF | 30 años | 237 min
    ('J. Castillo', 'Universitario'): 'J. Castillo',  # DMF | 24 años | 872 min
    ('J. Durán', 'Juan Pablo II College'): 'J. Durán',  # LCMF | 34 años | 974 min
    ('J. Escobar', 'Melgar'): 'J. Escobar',  # RCB | 30 años | 554 min
    ('J. González', 'Sporting Cristal'): 'J. González',  # RB | 30 años | 351 min
    ('J. Herrera', 'Comerciantes Unidos'): 'J. Herrera',  # RAMF | 27 años | 571 min
    ('J. Herrera', 'Cusco'): 'J. Herrera',  # LW | 21 años | 97 min
    ('J. Jiménez', 'CD Moquegua'): 'J. Jiménez',  # LB | 23 años | 60 min
    ('J. Martínez', 'Sport Huancayo'): 'J. Martínez',  # RWF | 21 años | 77 min
    ('J. Medina', 'FC Cajamarca'): 'J. Medina',  # GK | 32 años | 113 min
    ('J. Núñez', 'UTC Cajamarca'): 'J. Núñez',  # LW | 22 años | 89 min
    ('J. Palomino', 'Los Chankas'): 'J. Palomino',  # DMF | 30 años | 954 min
    ('J. Pérez', 'Alianza Atlético'): 'J. Pérez',  # LCMF | 24 años | 502 min
    ('J. Quintero', 'Los Chankas'): 'J. Quintero',  # CF | 32 años | 462 min
    ('J. Quiñones', 'Alianza Atlético'): 'J. Quiñones',  # LB | 24 años | 109 min
    ('J. Rojas', 'ADT'): 'J. Rojas',  # LW | 36 años | 524 min
    ('J. Salas', 'Melgar'): 'J. Salas',  # LCMF | 32 años | 851 min
    ('J. Sinisterra', 'Deportivo Garcilaso'): 'J. Sinisterra',  # LW | 27 años | 469 min
    ('J. Soto', 'ADT'): 'J. Soto',  # LCB | 22 años | 719 min
    ('J. Torres', 'Sport Boys'): 'J. Torres',  # AMF | 25 años | 546 min
    ('J. Valencia', 'ADT'): 'J. Valencia',  # GK | 33 años | 814 min
    ('J. Valoyes', 'Sport Huancayo'): 'J. Valoyes',  # LCB | 39 años | 865 min
    ('K. Moreno', 'CD Moquegua'): 'K. Moreno',  # LB | 28 años | 86 min
    ('L. Díaz', 'Sporting Cristal'): 'L. Díaz',  # LCB | 21 años | 90 min
    ('L. Sosa', 'Sporting Cristal'): 'L. Sosa',  # RB | 31 años | 668 min
    ('M. Amondarain', 'Cienciano'): 'M. Amondarain',  # RCB | 33 años | 539 min
    ('M. Peralta', 'Juan Pablo II College'): 'M. Peralta',  # RCB | 22 años | 522 min
    ('M. Pérez', 'Comerciantes Unidos'): 'M. Pérez',  # CF | 30 años | 325 min
    ('M. Rodríguez', 'Sporting Cristal'): 'M. Rodríguez',  # RWF | 19 años | 39 min
    ('M. Torres', 'Los Chankas'): 'M. Torres',  # CF | 23 años | 328 min
    ('P. Guzmán', 'Comerciantes Unidos'): 'P. Guzmán',  # RCB | 26 años | 449 min
    ('P. Álvarez', 'Atlético Grau'): 'P. Álvarez',  # GK | 32 años | 993 min
    ('R. Figueroa', 'CD Moquegua'): 'R. Figueroa',  # GK | 27 años | 203 min
    ('R. Garcés', 'Alianza Lima'): 'R. Garcés',  # RCB | 29 años | 975 min
    ('R. Rojas', 'Comerciantes Unidos'): 'R. Rojas',  # RB | 26 años | 311 min
    ('R. Sandoval', 'Cienciano'): 'R. Sandoval',  # LAMF | 31 años | 127 min
    ('S. Arias', 'Cienciano'): 'S. Arias',  # RDMF | 30 años | 279 min
    ('S. Fernández', 'Alianza Atlético'): 'S. Fernández',  # RCMF | 24 años | 357 min
    ('S. González', 'Atlético Grau'): 'S. González',  # RB | 25 años | 414 min
    ('S. González', 'Sporting Cristal'): 'S. González',  # RW | 26 años | 434 min
    ('S. Ramírez', 'Deportivo Garcilaso'): 'S. Ramírez',  # LCMF | 23 años | 18 min
    # ─────────────── VEN ───────────────
    ('A. Cardozo', 'Anzoátegui FC'): 'A. Cardozo',  # RDMF | 31 años | 212 min
    ('A. Fernández', 'Caracas'): 'A. Fernández',  # CF | 33 años | 605 min
    ('A. Flores', 'Zamora'): 'A. Flores',  # LCMF | 35 años | 570 min
    ('A. González', 'Carabobo'): 'A. González',  # RB | 33 años | 527 min
    ('A. Maldonado', 'Trujillanos'): 'A. Maldonado',  # LCB | 32 años | 297 min
    ('A. Martínez', 'UCV'): 'A. Martínez',  # RCB | 32 años | 461 min
    ('A. Moreno', 'Anzoátegui FC'): 'A. Moreno',  # RDMF | 28 años | 843 min
    ('A. Polo', 'Trujillanos'): 'A. Polo',  # RW | 21 años | 485 min
    ('A. Pérez', 'Deportivo Táchira'): 'A. Pérez',  # LDMF | 25 años | 653 min
    ('A. Rodríguez', 'Deportivo La Guaira'): 'A. Rodríguez',  # LAMF | 30 años | 155 min
    ('A. Romero', 'Monagas'): 'A. Romero',  # CF | 29 años | 33 min
    ('A. Uribe', 'Deportivo La Guaira'): 'A. Uribe',  # CF | 35 años | 503 min
    ('A. Velasco', 'Anzoátegui FC'): 'A. Velasco',  # CF | 26 años | 984 min
    ('A. Vera', 'Anzoátegui FC'): 'A. Vera',  # LB | 22 años | 244 min
    ('B. Rodríguez', 'Zamora'): 'B. Rodríguez',  # RCB | 29 años | 727 min
    ('C. Ramírez', 'Monagas'): 'C. Ramírez',  # LB | 22 años | 727 min
    ('C. Suárez', 'Portuguesa'): 'C. Suárez',  # LCMF | 33 años | 117 min
    ('E. Castillo', 'Carabobo'): 'E. Castillo',  # DMF | 31 años | 461 min
    ('F. Benítez', 'Caracas'): 'F. Benítez',  # GK | 21 años | 998 min
    ('F. Chaverra', 'Trujillanos'): 'F. Chaverra',  # LCB | 21 años | 698 min
    ('F. Díaz', 'Rayo Zuliano'): 'F. Díaz',  # RCB | 22 años | 449 min
    ('F. González', 'Monagas'): 'F. González',  # RDMF | 29 años | 154 min
    ('G. Benítez', 'Zamora'): 'G. Benítez',  # LB | 32 años | 50 min
    ('G. Montes', 'Estudiantes de Mérida'): 'G. Montes',  # RB | 30 años | 56 min
    ('J. Arias', 'Rayo Zuliano'): 'J. Arias',  # RCMF | 27 años | 522 min
    ('J. Bolívar', 'UCV'): 'J. Bolívar',  # CF | 24 años | 518 min
    ('J. Caraballo', 'Anzoátegui FC'): 'J. Caraballo',  # LAMF | 30 años | 337 min
    ('J. Caraballo', 'Monagas'): 'J. Caraballo',  # LCMF | 23 años | 660 min
    ('J. Castillo', 'Academia Puerto Cabello'): 'J. Castillo',  # LAMF | 23 años | 785 min
    ('J. Correa', 'Deportivo La Guaira'): 'J. Correa',  # DMF | 20 años | 666 min
    ('J. Cuesta', 'UCV'): 'J. Cuesta',  # LW | 24 años | 736 min
    ('J. Durán', 'Carabobo'): 'J. Durán',  # LCB | 22 años | 29 min
    ('J. Figueroa', 'Trujillanos'): 'J. Figueroa',  # RCMF | 33 años | 184 min
    ('J. Fuentes', 'Carabobo'): 'J. Fuentes',  # LCB | 29 años | 573 min
    ('J. González', 'Zamora'): 'J. González',  # RB | 30 años | 342 min
    ('J. Graterol', 'Academia Puerto Cabello'): 'J. Graterol',  # GK | 28 años | 803 min
    ('J. Graterol', 'Zamora'): 'J. Graterol',  # GK | 26 años | 99 min
    ('J. Gutiérrez', 'Deportivo La Guaira'): 'J. Gutiérrez',  # LB | 27 años | 789 min
    ('J. Gutiérrez', 'Estudiantes de Mérida'): 'J. Gutiérrez',  # RCB | 28 años | 325 min
    ('J. Gómez', 'Rayo Zuliano'): 'J. Gómez',  # DMF | 28 años | 797 min
    ('J. Hernández', 'Academia Puerto Cabello'): 'J. Hernández',  # LWF | 29 años | 576 min
    ('J. Lovera', 'Anzoátegui FC'): 'J. Lovera',  # RB | 26 años | 838 min
    ('J. Martínez', 'Academia Puerto Cabello'): 'J. Martínez',  # LAMF | 24 años | 83 min
    ('J. Martínez', 'Rayo Zuliano'): 'J. Martínez',  # LCMF | 27 años | 393 min
    ('J. Moreno', 'Academia Puerto Cabello'): 'J. Moreno',  # LDMF | 32 años | 327 min
    ('J. Moreno', 'Anzoátegui FC'): 'J. Moreno',  # RCB | 26 años | 204 min
    ('J. Moreno', 'Carabobo'): 'J. Moreno',  # CF | 31 años | 277 min
    ('J. Moreno', 'Portuguesa'): 'J. Moreno',  # AMF | 34 años | 676 min
    ('J. Mosquera', 'Zamora'): 'J. Mosquera',  # LCB | 24 años | 628 min
    ('J. Obando', 'Carabobo'): 'J. Obando',  # LAMF | 19 años | 17 min
    ('J. Ortiz', 'Trujillanos'): 'J. Ortiz',  # RW | 32 años | 469 min
    ('J. Pérez', 'Carabobo'): 'J. Pérez',  # LB | 27 años | 381 min
    ('J. Quintero', 'Caracas'): 'J. Quintero',  # RCB | 25 años | 640 min
    ('J. Ramírez', 'Metropolitanos'): 'J. Ramírez',  # CF | 24 años | 316 min
    ('J. Soto', 'Portuguesa'): 'J. Soto',  # LDMF | 31 años | 850 min
    ('J. Sánchez', 'Deportivo La Guaira'): 'J. Sánchez',  # GK | 19 años | 346 min
    ('J. Sánchez', 'Deportivo Táchira'): 'J. Sánchez',  # LB | 20 años | 769 min
    ('J. Vargas', 'Academia Puerto Cabello'): 'J. Vargas',  # RB | 31 años | 765 min
    ('J. Vargas', 'Deportivo La Guaira'): 'J. Vargas',  # RAMF | 26 años | 113 min
    ('J. Zapata', 'UCV'): 'J. Zapata',  # CF | 32 años | 169 min
    ('K. Silva', 'UCV'): 'K. Silva',  # RB | 32 años | 794 min
    ('L. González', 'Anzoátegui FC'): 'L. González',  # RCMF | 27 años | 99 min
    ('L. González', 'Deportivo Táchira'): 'L. González',  # AMF | 35 años | 445 min
    ('L. Martínez', 'Carabobo'): 'L. Martínez',  # CF | 21 años | 422 min
    ('L. Morales', 'UCV'): 'L. Morales',  # GK | 26 años | 203 min
    ('L. Mosquera', 'Trujillanos'): 'L. Mosquera',  # LCMF | 24 años | 277 min
    ('L. Peña', 'Deportivo La Guaira'): 'L. Peña',  # RB | 24 años | 693 min
    ('L. Peña', 'Rayo Zuliano'): 'L. Peña',  # CF | 22 años | 475 min
    ('L. Pérez', 'Anzoátegui FC'): 'L. Pérez',  # RAMF | 25 años | 83 min
    ('L. Romero', 'Academia Puerto Cabello'): 'L. Romero',  # GK | 35 años | 306 min
    ('M. Acuña', 'Portuguesa'): 'M. Acuña',  # RCB | 29 años | 370 min
    ('M. Díaz', 'Metropolitanos'): 'M. Díaz',  # RW | 22 años | 185 min
    ('M. Fernández', 'Trujillanos'): 'M. Fernández',  # LCMF | 40 años | 285 min
    ('M. González', 'Rayo Zuliano'): 'M. González',  # RW | 19 años | 121 min
    ('M. González', 'Trujillanos'): 'M. González',  # LB | 37 años | 669 min
    ('N. Hernández', 'Deportivo La Guaira'): 'N. Hernández',  # RB | 33 años | 365 min
    ('P. Álvarez', 'Anzoátegui FC'): 'P. Álvarez',  # LDMF | 25 años | 342 min
    ('R. Figueroa', 'Metropolitanos'): 'R. Figueroa',  # RW | 29 años | 954 min
    ('R. Garcés', 'Metropolitanos'): 'R. Garcés',  # RB | 33 años | 15 min
    ('R. Peralta', 'Monagas'): 'R. Peralta',  # LCB | 32 años | 816 min
    ('R. Ramírez', 'Rayo Zuliano'): 'R. Ramírez',  # GK | 23 años | 100 min
    ('R. Ramírez', 'UCV'): 'R. Ramírez',  # RCB | 30 años | 347 min
    ('R. Rojas', 'Portuguesa'): 'R. Rojas',  # LAMF | 33 años | 681 min
    ('S. Mendoza', 'Carabobo'): 'S. Mendoza',  # RDMF | 20 años | 335 min
    ('S. Ramírez', 'Metropolitanos'): 'S. Ramírez',  # LW | 24 años | 646 min
    ('S. Sosa', 'UCV'): 'S. Sosa',  # CF | 26 años | 604 min
    ('V. Rodríguez', 'UCV'): 'V. Rodríguez',  # LCMF | 31 años | 410 min
}

# Action-percentage pairs for calculating successful actions
ACTION_PERCENTAGE_PAIRS = {
    'Duels': 'Duels won, %',
    'Defensive duels': 'Defensive duels won, %',
    'Aerial duels': 'Aerial duels won, %',
    'Crosses': 'Accurate crosses, %',
    'Crosses from left flank': 'Accurate crosses from left flank, %',
    'Crosses from right flank': 'Accurate crosses from right flank, %',
    'Dribbles': 'Successful dribbles, %',
    'Offensive duels': 'Offensive duels won, %',
    'Passes': 'Accurate passes, %',
    'Forward passes': 'Accurate forward passes, %',
    'Back passes': 'Accurate back passes, %',
    'Lateral passes': 'Accurate lateral passes, %',
    'Short / medium passes': 'Accurate short / medium passes, %',
    'Long passes': 'Accurate long passes, %',
    'Smart passes': 'Accurate smart passes, %',
    'Passes to final third': 'Accurate passes to final third, %',
    'Passes to penalty area': 'Accurate passes to penalty area, %',
    'Through passes': 'Accurate through passes, %',
    'Progressive passes': 'Accurate progressive passes, %',
    'Shots': 'Shots on target, %',
}

# Position to group mapping
POSITION_GROUP_MAPPING = {
    'CF': 'Delantero',
    'RW': 'Extremo',
    'RWF': 'Extremo',
    'LWF': 'Extremo',
    'LW': 'Extremo',
    'AMF': 'Volante Ofensivo',
    'RAMF': 'Extremo',
    'LAMF': 'Extremo',
    'RCMF': 'Volante Central',
    'LCMF': 'Volante Central',
    'RDMF': 'Volante Central',
    'LDMF': 'Volante Central',
    'DMF': 'Volante Central',
    'RWB': 'Lateral',
    'RB': 'Lateral',
    'LWB': 'Lateral',
    'LB': 'Lateral',
    'LCB': 'Central',
    'RCB': 'Central',
    'GK': 'Portero',
}


def process_database(df):
    """Process the raw database: per-90 to totals, derived columns, position groups."""
    df = df.copy()

    # Ensure 'Pie' (Foot) column is string to avoid Arrow serialization issues
    if 'Pie' in df.columns:
        df['Pie'] = df['Pie'].astype(str)

    # Clean positions - keep only the first
    df['Position'] = df['Position'].astype(str).str.split(',').str[0].str.strip()

    # Aplicar overrides manuales de posición (prevalecen sobre el dato descargado)
    if 'Player' in df.columns:
        for player, pos in PLAYER_POSITION_OVERRIDES.items():
            mask = df['Player'] == player
            if mask.any():
                df.loc[mask, 'Position'] = pos

    # Drop PAdj columns
    padj_columns = [col for col in df.columns if 'PAdj' in col]
    df = df.drop(columns=padj_columns, errors='ignore')

    # Convert per-90 to totals
    if 'Minutes played' not in df.columns:
        raise KeyError("La columna 'Minutes played' no existe en la planilla.")

    for col in PER_90_COLUMNS:
        if col in df.columns:
            total_values = (
                (pd.to_numeric(df[col], errors='coerce').fillna(0)
                 * pd.to_numeric(df['Minutes played'], errors='coerce').fillna(0)) / 90
            ).round(1)
            new_col_name = col.replace(' per 90', '')

            # Preserve source totals from the spreadsheet when they already exist.
            # Only backfill missing values from the per-90 reconstruction.
            if new_col_name in df.columns:
                existing_values = pd.to_numeric(df[new_col_name], errors='coerce')
                df[new_col_name] = existing_values.where(existing_values.notna(), total_values)
            else:
                df[new_col_name] = total_values
            # Keep the original per-90 column (don't drop it)

    # Calculate successful actions
    for action_col, perc_col in ACTION_PERCENTAGE_PAIRS.items():
        if action_col in df.columns and perc_col in df.columns:
            if action_col == 'Shots':
                success_col_name = 'Shots on target'
            elif 'Accurate' in perc_col:
                success_col_name = f"Accurate {action_col.lower()}"
            else:
                success_col_name = f"{action_col} won"
            base = pd.to_numeric(df[action_col], errors='coerce').fillna(0)
            perc = pd.to_numeric(df[perc_col], errors='coerce').fillna(0)
            df[success_col_name] = (base * perc / 100).round(0)

    # Derived columns
    if 'Goals' in df.columns and 'xG' in df.columns:
        df['Dif G-xG'] = (
            pd.to_numeric(df['Goals'], errors='coerce').fillna(0)
            - pd.to_numeric(df['xG'], errors='coerce').fillna(0)
        ).round(2)

    if 'Accurate progressive passes' in df.columns and 'Progressive runs' in df.columns:
        df['Progressive actions'] = (
            pd.to_numeric(df['Accurate progressive passes'], errors='coerce').fillna(0)
            + pd.to_numeric(df['Progressive runs'], errors='coerce').fillna(0)
        ).round(0)

    if 'Successful defensive actions' in df.columns and 'Successful attacking actions' in df.columns:
        df['Off Def Successful actions'] = (
            pd.to_numeric(df['Successful defensive actions'], errors='coerce').fillna(0)
            + pd.to_numeric(df['Successful attacking actions'], errors='coerce').fillna(0)
        ).round(0)

    if all(col in df.columns for col in ['Sliding tackles', 'Interceptions', 'Shots blocked']):
        df['CBIT'] = (
            pd.to_numeric(df['Sliding tackles'], errors='coerce').fillna(0)
            + pd.to_numeric(df['Interceptions'], errors='coerce').fillna(0)
            + pd.to_numeric(df['Shots blocked'], errors='coerce').fillna(0)
        ).round(0)

    # Per-90 versions of derived count columns
    minutes = pd.to_numeric(df['Minutes played'], errors='coerce').replace(0, pd.NA)
    per90_divisor = minutes / 90
    for col in [
        # Duelos y tiros
        'Shots on target', 'Dribbles won',
        'Duels won', 'Defensive duels won', 'Aerial duels won', 'Offensive duels won',
        # Pases precisos (todas las variantes)
        'Accurate passes',
        'Accurate forward passes',
        'Accurate back passes',
        'Accurate lateral passes',
        'Accurate short / medium passes',
        'Accurate long passes',
        'Accurate smart passes',
        'Accurate passes to final third',
        'Accurate passes to penalty area',
        'Accurate through passes',
        'Accurate progressive passes',
        # Centros precisos
        'Accurate crosses',
        'Accurate crosses from left flank',
        'Accurate crosses from right flank',
    ]:
        if col in df.columns:
            df[f'{col} per 90'] = (
                pd.to_numeric(df[col], errors='coerce') / per90_divisor
            ).round(2)

    # Eliminar columnas excluidas de la app
    df = df.drop(columns=[c for c in EXCLUDED_COLUMNS if c in df.columns], errors='ignore')

    # Position groups
    df['Position Group'] = df['Position'].map(POSITION_GROUP_MAPPING)
    cols = df.columns.tolist()
    if 'Position' in cols and 'Position Group' in cols:
        pos_idx = cols.index('Position')
        cols.insert(pos_idx + 1, cols.pop(cols.index('Position Group')))
        df = df[cols]

    return df


@st.cache_data
def load_and_process_data():
    """Load database.xlsx and process it. Cached by Streamlit."""
    # Try multiple paths for flexibility (local dev vs deployed)
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'database.xlsx'),
        os.path.join('data', 'database.xlsx'),
    ]
    for path in possible_paths:
        if os.path.exists(path):
            df = pd.read_excel(path)
            return process_database(df)
    raise FileNotFoundError("database.xlsx not found in data/ directory")


@st.cache_data
def load_external_league(league_name: str):
    """Load and process an external league file (e.g. ARG.xlsx or BRA.xlsx).
    Returns a processed DataFrame, or None if the file is not found."""
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', f'{league_name}.xlsx'),
        os.path.join('data', f'{league_name}.xlsx'),
    ]
    for path in possible_paths:
        if os.path.exists(path):
            df = pd.read_excel(path)
            return process_database(df)
    return None
