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

# Overrides de nombres de equipos que colisionan entre ligas distintas
TEAM_NAME_OVERRIDES = {
    ('Universidad Católica', 'ECU'): 'Universidad Católica (ECU)',
    ('Universidad Católica', 'CHI'): 'Universidad Católica (CHI)',
    # MEX — agregar duplicados cuando se carguen los datos
    # MLS — agregar duplicados cuando se carguen los datos
}

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
    'E. Vera':      'LW'
}

# Renombrado de jugadores con nombre idéntico: clave (Player, Team) -> nombre final
# Modificar el valor para diferenciar jugadores homónimos dentro de la misma liga
PLAYER_NAME_OVERRIDES = {
    # ─────────────── PAR ───────────────
    ('A. Benítez', 'Club Libertad'): 'Alan Benítez',  # RAMF | 32 años | 470 min
    ('A. Cano', 'Sportivo Trinidense'): 'Alan Cano',  # CF | 21 años | 143 min
    ('A. Cañete', 'Nacional Asunción'): 'Alexis Cañete',  # RCB | 22 años | 1567 min
    ('A. Cañete', 'Sportivo Trinidense'): 'Axel Cañete',  # RB | 24 años | 660 min
    ('A. Duarte', 'Club Libertad'): 'Alexis Duarte',  # LCB | 25 años | 29 min
    ('A. Franco', 'Olimpia'): 'Alex Franco',  # RCMF | 24 años | 735 min
    ('A. González', 'Club Libertad'): 'Angel González',  # GK | 23 años | 97 min
    ('A. González', 'Deportivo Recoleta'): 'Aldo González',  # CF | 29 años | 858 min
    ('A. Gómez', '2 de Mayo'): 'Alan Gómez',  # RW | 23 años | 882 min
    ('A. Maidana', 'Guaraní'): 'Alexandro Maidana',  # LB | 20 años | 512 min
    ('A. Molinas', 'Club Libertad'): 'Amin Molinas',  # LCMF | 20 años | 710 min
    ('A. Oviedo', 'Sportivo San Lorenzo'): 'Antonio Oviedo',  # CF | 29 años | 176 min
    ('A. Pérez', 'Guaraní'): 'Aldo Pérez',  # GK | 25 años | 104 min
    ('A. Álvarez', 'Sportivo San Lorenzo'): 'Alex Álvarez',  # CF | 28 años | 694 min
    ('C. González', 'Sportivo Trinidense'): 'Clementino González',  # CF | 35 años | 1067 min
    ('C. Ramírez', 'Guaraní'): 'Cesar Ramírez',  # LCB | 22 años | 63 min
    ('D. Fernández', 'Guaraní'): 'Diego Fernández',  # RW | 23 años | 868 min
    ('D. Rodríguez', 'Guaraní'): 'Derlis Rodríguez',  # LWF | 28 años | 951 min
    ('E. Díaz', 'Club Libertad'): 'Estifen Díaz',  # RW | 21 años | 69 min
    ('F. Benítez', 'Sportivo Luqueño'): 'Fernando Benítez',  # DMF | 26 años | 576 min
    ('F. Díaz', 'Nacional Asunción'): 'Fernando Díaz',  # LB | 25 años | 958 min
    ('F. Fernández', 'Guaraní'): 'Fernando Fernández',  # CF | 34 años | 651 min
    ('F. Jara', 'Nacional Asunción'): 'Fabrizio Jara',  # RCMF | 23 años | 784 min
    ('F. Romero', 'Sportivo Trinidense'): 'Fernando Romero',  # CF | 25 años | 1025 min
    ('F. Román', 'Sportivo Trinidense'): 'Fernando J. Román',  # RCB | 25 años | 121 min
    ('F. Vera', 'Sportivo Ameliano'): 'Fredy Vera',  # RAMF | 27 años | 833 min
    ('G. Benítez', 'Cerro Porteño'): 'Angel G. Benítez',  # LB | 32 años | 469 min
    ('G. Benítez', 'Nacional Asunción'): 'Gaston Benítez',  # LCB | 23 años | 208 min
    ('G. Viera', 'Sportivo Trinidense'): 'Gustavo Viera',  # RCMF | 30 años | 1042 min
    ('H. Benítez', 'Nacional Asunción'): 'Hugo J. Benítez',  # CF | 22 años | 451 min
    ('H. Benítez', 'Sportivo Ameliano'): 'Hugo A. Benítez',  # RB | 27 años | 8 min
    ('I. Ramírez', 'Club Libertad'): 'Ivan Ramírez',  # RB | 31 años | 868 min
    ('J. Benítez', 'Sportivo Ameliano'): 'Jonathan Benítez',  # LDMF | 25 años | 1223 min
    ('J. Franco', 'Deportivo Recoleta'): 'Juan A. Franco',  # RCMF | 23 años | 1274 min
    ('J. González', 'Rubio Ñú'): 'Jorge D. González',  # LCB | 29 años | 330 min
    ('J. González', 'Sportivo Ameliano'): 'Julio González',  # RCB | 33 años | 1580 min
    ('J. Núñez', 'Deportivo Recoleta'): 'Juan I. Núñez',  # LCB | 36 años | 162 min
    ('J. Pérez', 'Guaraní'): 'Dani Pérez',  # RB | 32 años | 969 min
    ('J. Sánchez', 'Guaraní'): 'John Jairo Sánchez',  # RWF | 26 años | 557 min
    ('J. Torres', 'Cerro Porteño'): 'Jonatan Torres',  # CF | 29 años | 632 min
    ('L. Ayala', 'Sportivo Ameliano'): 'Luis Ayala',  # RW | 20 años | 530 min
    ('L. González', 'Nacional Asunción'): 'L. González Gamarra',  # CF | 28 años | 463 min
    ('L. González', 'Sportivo Trinidense'): 'Lucas D. González',  # RCMF | 21 años | 510 min
    ('L. Gómez', 'Rubio Ñú'): 'Lucas Gómez',  # RCB | 20 años | 388 min
    ('L. Martínez', 'Guaraní'): 'Luis Martínez',  # DMF | 26 años | 985 min
    ('M. Cáceres', '2 de Mayo'): 'Fernando M. Cáceres',  # CF | 29 años | 494 min
    ('M. Fernández', 'Club Libertad'): 'Marcelo Fernández',  # RW | 24 años | 236 min
    ('M. Gómez', 'Guaraní'): 'Marcos Gómez',  # RCMF | 24 años | 76 min
    ('M. López', 'Guaraní'): 'Matias López',  # RCMF | 22 años | 1046 min
    ('M. López', 'Sportivo San Lorenzo'): 'Mario López',  # LCB | 30 años | 1207 min
    ('M. Martínez', 'Sportivo Ameliano'): 'Miguel Martínez',  # GK | 27 años | 1580 min
    ('M. Martínez', 'Sportivo San Lorenzo'): 'Roberto Martínez',  # LW | 31 años | 233 min
    ('M. Pérez', 'Cerro Porteño'): 'Matias Pérez',  # LCB | 27 años | 1164 min
    ('P. Álvarez', 'Rubio Ñú'): 'Pedro Álvarez',  # LB | 25 años | 544 min
    ('R. Benítez', 'Olimpia'): 'Romeo Benítez',  # LWF | 23 años | 106 min
    ('R. Cabral', 'Sportivo Ameliano'): 'Raul Cabral',  # AMF | 21 años | 927 min
    ('R. Fernández', 'Cerro Porteño'): 'Roberto Fernández',  # GK | 38 años | 98 min
    ('R. Gómez', 'Cerro Porteño'): 'Rodrigo Gómez',  # RB | 19 años | 286 min
    ('R. Ramírez', 'Nacional Asunción'): 'Roberto Ramírez',  # RCMF | 25 años | 1074 min
    ('R. Redes', 'Olimpia'): 'Rodney Redes',  # RWF | 26 años | 181 min
    ('R. Rojas', 'Club Libertad'): 'Robert Rojas',  # RCB | 29 años | 330 min
    ('R. Sánchez', 'Olimpia'): 'Richard Sánchez',  # RCMF | 30 años | 432 min
    ('S. Díaz', 'Sportivo Luqueño'): 'Sergio Díaz',  # LW | 28 años | 679 min
    ('S. Gómez', 'Rubio Ñú'): 'Stevens Gómez',  # LCMF | 26 años | 27 min
    ('S. Mendoza', 'Sportivo Trinidense'): 'Sergio Mendoza',  # LB | 31 años | 999 min
    ('Á. Martínez', '2 de Mayo'): 'Ángel I. Martínez',  # GK | 23 años | 1575 min
    ('Á. Martínez', 'Sportivo Luqueño'): 'Álvaro Martínez',  # LB | 24 años | 755 min
    ('Ó. Romero', '2 de Mayo'): 'Óscar Romero',  # LCMF | 27 años | 706 min
    # ─────────────── ARG ───────────────
    ('A. Cardozo', 'Lanús'): 'Agustin Cardozo',  # LCMF | 28 años | 1163 min
    ('A. Fernández', 'Racing Club'): 'Adrian Fernández',  # LCMF | 24 años | 601 min
    ('A. Maldonado', 'Belgrano'): 'Alexis Maldonado',  # RCB | 28 años | 795 min
    ('A. Martínez', 'Huracán'): 'Silvio Martínez',  # RW | 29 años | 420 min
    ('A. Martínez', 'Racing Club'): 'Adrian Martínez',  # CF | 33 años | 976 min
    ('A. Moreno', 'River Plate'): 'Anibal Moreno',  # DMF | 26 años | 1207 min
    ('A. Méndez', "Newell's Old Boys"): 'Armando Méndez',  # RB | 30 años | 1012 min
    ('A. Sánchez', 'Belgrano'): 'Adrian Sánchez',  # RCMF | 26 años | 1114 min
    ('B. Cabrera', "Newell's Old Boys"): 'Bruno L. Cabrera',  # RCB | 28 años | 355 min
    ('B. Rodríguez', 'Racing Club'): 'Baltasar Rodríguez',  # RCMF | 22 años | 463 min
    ('D. Martínez', 'Barracas Central'): 'Damian Martínez',  # RB | 36 años | 417 min
    ('D. Martínez', 'Defensa y Justicia'): 'Hector Martínez',  # LCB | 28 años | 956 min
    ('D. Romero', 'Tigre'): 'Jose Romero',  # CF | 23 años | 808 min
    ('F. Torres', 'Gimnasia La Plata'): 'Franco Torres',  # LW | 26 años | 610 min
    ('F. Álvarez', 'Argentinos Juniors'): 'Francisco Álvarez',  # RCB | 26 años | 1165 min
    ('F. Álvarez', 'Tigre'): 'Federico Álvarez',  # LB | 31 años | 1190 min
    ('Fernando Martínez', 'Central Córdoba SdE'): 'Fernando D. Martínez',  # RW | 25 años | 394 min
    ('I. Ramírez', "Newell's Old Boys"): 'Juan I. Ramírez',  # CF | 29 años | 423 min
    ('I. Tapia', 'Barracas Central'): 'Ivan Tapia',  # LCMF | 27 años | 1055 min
    ('J. Arias', 'Aldosivi'): 'Junior Arias',  # CF | 32 años | 776 min
    ('J. Gutiérrez', 'Defensa y Justicia'): 'Juan Gutiérrez',  # CF | 24 años | 1210 min
    ('J. Gómez', 'Sarmiento'): 'Jonathan Gómez',  # LCMF | 36 años | 353 min
    ('J. Herrera', 'Deportivo Riestra'): 'Jonathan Herrera',  # CF | 34 años | 883 min
    ('J. Palomino', 'Talleres Córdoba'): 'Jose L. Palomino',  # LCB | 36 años | 437 min
    ('J. Quintero', 'River Plate'): 'Juanfer Quintero',  # AMF | 33 años | 546 min
    ('L. Díaz', 'Atlético Tucumán'): 'Leandro Díaz',  # CF | 33 años | 886 min
    ('L. González', 'Central Córdoba SdE'): 'Lucas N. González',  # LCMF | 25 años | 748 min
    ('L. Gómez', 'Banfield'): 'Lautaro Gómez',  # RW | 22 años | 613 min
    ('L. Morales', 'Belgrano'): 'Luciano Morales',  # RCB | 35 años | 1150 min
    ('L. Paredes', 'Boca Juniors'): 'Leo Paredes',  # DMF | 31 años | 917 min
    ('L. Paredes', 'Gimnasia Mendoza'): 'Luciano Paredes',  # RB | 23 años | 900 min
    ('M. Acuña', 'River Plate'): 'Marcos Acuña',  # LB | 34 años | 581 min
    ('M. Amondarain', 'Estudiantes'): 'Mikel Amondarain',  # RDMF | 21 años | 898 min
    ('M. Fernández', 'Independiente Rivadavia'): 'Matias Fernández',  # CF | 24 años | 954 min
    ('M. García', 'Deportivo Riestra'): 'Matias García',  # DMF | 30 años | 501 min
    ('M. García', 'Sarmiento'): 'Manuel García',  # RCMF | 26 años | 798 min
    ('M. Rodríguez', 'Unión Santa Fe'): 'Alex Rodríguez',  # RCB | 22 años | 1195 min
    ('M. Torres', 'Gimnasia La Plata'): 'Luis M. Torres',  # CF | 28 años | 1155 min
    ('S. Arias', 'Independiente'): 'Santiago Arias',  # RB | 34 años | 732 min
    # ─────────────── BRA ───────────────
    ('Allan', 'Corinthians'): 'Allan Marques',  # LDMF | 29 años | 382 min
    ('Bruno Henrique', 'Flamengo'): 'Bruno Henrique Pinto',  # CF | 35 años | 168 min
    ('Danilo', 'Flamengo'): 'Danilo Luiz',  # RCB | 34 años | 144 min
    ('Dudu', 'Atlético Mineiro'): 'Dudu Pereira',  # LW | 34 años | 335 min
    ('E. Martínez', 'Palmeiras'): 'Emiliano Martínez',  # LDMF | 26 años | 57 min
    ('E. Martínez', 'Vitória'): 'Leandro Martínez',  # LCMF | 31 años | 599 min
    ('Eduardo', 'Mirassol'): 'Eduardo de Olveira',  # AMF | 36 años | 365 min
    ('Eduardo', 'Red Bull Bragantino'): 'Eduardo Gonzaga',  # LCB | 28 años | 141 min
    ('Erick', 'Bahia'): 'Erick Luis',  # DMF | 28 años | 557 min
    ('Fabinho', 'Coritiba'): 'Fabio Augusto',  # CF | 26 años | 128 min
    ('Gabriel', 'Red Bull Bragantino'): 'Gabriel Franco',  # LDMF | 33 años | 751 min
    ('Gustavo Henrique', 'Corinthians'): 'Gustavo H. Vernes',  # LCB | 33 años | 1045 min
    ('João Paulo', 'Bahia'): 'João Paulo Silva',  # GK | 30 años | 63 min
    ('João Pedro', 'Remo'): 'João Pedro Sousa',  # CF | 29 años | 315 min
    ('J. Correa', 'Botafogo'): 'Joaquin Correa',  # CF | 31 años | 126 min
    ('L. Pérez', 'Grêmio'): 'Leonel Pérez',  # DMF | 21 años | 244 min
    ('L. Villalba', 'Cruzeiro'): 'Lucas Villalba',  # LCB | 31 años | 732 min
    ('L. Villalba', 'Botafogo'): 'Lucas M. Villalba',  # RAMF | 24 años | 237 min
    ('Matheus Pereira', 'Corinthians'): 'Matheus Pereira da Silva',  # LCMF | 28 años | 434 min
    ('Matheuzinho', 'Corinthians'): 'Matheuzinho Franca',  # RB | 25 años | 924 min
    ('René', 'Fluminense'): 'René R. Martins',  # LB | 33 años | 691 min
    ('Ronaldo', 'Internacional'): 'Ronaldo Strada',  # LCMF | 29 años | 377 min
    ('Tetê', 'Grêmio'): 'Mateus Cardoso',  # RW | 26 años | 564 min
    ('Vitinho', 'Internacional'): 'Vitor Hugo',  # RAMF | 27 años | 866 min
    ('Vitinho', 'Botafogo'): 'Victor da Silva',  # RB | 26 años | 941 min
    # ─────────────── URU ───────────────
    ('A. Muñoz', 'Torque'): 'Andres Muñoz',  # CF | 19 años | 23 min
    ('A. Romero', 'Albion'): 'Andres Romero',  # RB | 27 años | 860 min
    ('A. Vera', 'Albion'): 'Agustin Vera',  # LAMF | 22 años | 564 min
    ('E. Castillo', 'Liverpool'): 'Enzo Castillo',  # LCB | 25 años | 898 min
    ('G. Montes', 'Torque'): 'Gonzalo Montes',  # LCMF | 31 años | 565 min
    ('J. Moreno', 'Cerro Largo'): 'Juan E. Moreno',  # GK | 26 años | 391 min
    ('K. Silva', 'Torque'): 'Kevin Silva',  # RCB | 23 años | 302 min
    ('M. Peralta', 'Danubio'): 'Mateo Peralta',  # LCMF | 20 años | 878 min
    ('R. Peralta', 'Juventud'): 'Ramiro Peralta',  # LDMF | 22 años | 820 min
    ('S. González', 'Deportivo Maldonado'): 'Sebastian González',  # DMF | 26 años | 263 min
    ('V. Rodríguez', 'Defensor Sporting'): 'Valentin Rodríguez',  # LB | 24 años | 125 min
    # ─────────────── COL ───────────────
    ('A. Arroyo', 'Fortaleza'): 'Andres J. Arroyo',  # AMF | 24 años | 1404 min
    ('A. Gutiérrez', 'Atlético Bucaramanga'): 'Aldair Gutiérrez',  # RB | 27 años | 1198 min
    ('A. Ramos', 'América de Cali'): 'Gustavo Ramos',  # CF | 40 años | 130 min
    ('A. Salazar', 'Águilas Doradas'): 'Andres Salazar',  # GK | 32 años | 692 min
    ('B. Angulo', 'Jaguares de Córdoba'): 'Bladimir Angulo',  # RCMF | 25 años | 128 min
    ('D. Ramírez', 'Boyacá Chicó'): 'Delio A. Ramírez',  # RW | 25 años | 1052 min
    ('F. Chaverra', 'Medellín'): 'Francisco Chaverra',  # LWB | 26 años | 1229 min
    ('J. Cuesta', 'Once Caldas'): 'Juan D. Cuesta',  # RB | 28 años | 1576 min
    ('J. Escobar', 'América de Cali'): 'Josen Escobar',  # LCMF | 21 años | 1151 min
    ('J. Figueroa', 'Alianza'): 'Jesus Figueroa',  # RCB | 30 años | 791 min
    ('J. Lovera', 'Jaguares de Córdoba'): 'Jonathan Lovera',  # RCB | 21 años | 228 min
    ('J. Obando', 'Fortaleza'): 'Jeferson Medina',  # LCB | 20 años | 96 min
    ('J. Ortiz', 'Medellín'): 'Jose E. Ortiz',  # LCB | 27 años | 1188 min
    ('J. Salas', 'Fortaleza'): 'Jhonier Salas',  # CF | 22 años | 224 min
    ('J. Sinisterra', 'Fortaleza'): 'Julio Sinisterra',  # CF | 17 años | 186 min
    ('J. Soto', 'América de Cali'): 'Jorge Soto',  # GK | 32 años | 596 min
    ('J. Valoyes', 'Alianza'): 'Jhon Valoyes',  # RCMF | 16 años | 73 min
    ('K. Moreno', 'Alianza'): 'Kevin Moreno',  # LCB | 25 años | 387 min
    ('L. Mosquera', 'Deportivo Pereira'): 'Luis F. Mosquera',  # AMF | 23 años | 222 min
    ('N. Hernández', 'América de Cali'): 'Nicolas Hernández',  # LCB | 28 años | 688 min
    # ─────────────── ECU ───────────────
    ('A. Velasco', 'Independiente del Valle'): 'Andy Velasco',  # CB | 27 años | 125 min
    ('J. Jiménez', 'Macará'): 'John J. Jiménez',  # RCB | 31 años | 100 min
    ('J. Medina', 'LDU Quito'): 'Jeison Medina',  # RAMF | 31 años | 170 min
    ('J. Quiñones', 'Mushuc Runa'): 'J. L. Mancilla',  # LCB | 23 años | 122 min
    ('P. Guzmán', 'Aucas'): 'Piero Guzmán',  # RCMF | 22 años | 684 min
    # ─────────────── CHI ───────────────
    ('A. Uribe', 'Univ. Concepción'): 'Ariel Uribe',  # CF | 27 años | 260 min
    ('B. Palacios', 'Universidad Católica (ECU)'): 'Byron Palacios',  # CF | 277 min
    ('C. Suárez', 'Concepción'): 'Cristian Suárez',  # RCB | 39 años | 437 min
    ('C. Zambrano', 'Univ. Concepción'): 'Cristobal Zambrano',  # RW | 17 años | 124 min
    ("F. González", "O'Higgins"): "Francisco A. González",  # RW | 25 años | 668 min
    ('J. Fuentes', 'Cobresal'): 'Juan E. Fuentes',  # CB | 31 años | 445 min
    ('J. Vargas', 'La Serena'): 'Jeisson Vargas',  # LWF | 28 años | 850 min
    ("L. Díaz", "O'Higgins"): "Leandro E. Díaz",  # LB | 27 años | 291 min
    ('R. Sandoval', 'Cobresal'): 'Rodrigo Sandoval',  # LB | 25 años | 345 min
    # ─────────────── PER ───────────────
    ('A. Flores', 'Atlético Grau'): 'Arnold Flores',  # LAMF | 21 años | 58 min
    ('A. Polo', 'Universitario'): 'Andy Polo',  # RB | 31 años | 877 min
    ('A. Rodríguez', 'ADT'): 'Aldair Rodríguez',  # RAMF | 31 años | 330 min
    ('J. Bolívar', 'Cusco'): 'Jose V. Bolívar',  # LB | 26 años | 453 min
    ('J. Castillo', 'Alianza Lima'): 'Jesus Castillo',  # LCMF | 30 años | 237 min
    ('J. Castillo', 'Universitario'): 'Jesus A. Castillo',  # DMF | 24 años | 872 min
    ('J. Durán', 'Juan Pablo II College'): 'Jack Durán',  # LCMF | 34 años | 974 min
    ('J. Martínez', 'Sport Huancayo'): 'Juan Martínez',  # RWF | 21 años | 77 min
    ('J. Soto', 'ADT'): 'Jhair Soto',  # LCB | 22 años | 719 min
    ('R. Figueroa', 'CD Moquegua'): 'Renzo Figueroa',  # GK | 27 años | 203 min
    ('R. Garcés', 'Alianza Lima'): 'Renzo Garcés',  # RCB | 29 años | 975 min
    ('S. Ramírez', 'Deportivo Garcilaso'): 'Sharif Ramírez',  # LCMF | 23 años | 18 min
    # ─────────────── VEN ───────────────
    ('A. Rodríguez', 'Deportivo La Guaira'): 'Alexis Rodríguez',  # LAMF | 30 años | 155 min
    ('J. Caraballo', 'Anzoátegui FC'): 'Jose E. Caraballo',  # LAMF | 30 años | 337 min
    ('J. Graterol', 'Zamora'): 'Jorge A. Graterol',  # GK | 26 años | 99 min
    ('J. Martínez', 'Rayo Zuliano'): 'Johao Martínez',  # LCMF | 27 años | 393 min
    ('J. Vargas', 'Deportivo La Guaira'): 'Jesus A. Vargas',  # RAMF | 26 años | 113 min
    ('L. Peña', 'Deportivo La Guaira'): 'Luis A. Peña',  # RB | 24 años | 693 min
    ('M. González', 'Rayo Zuliano'): 'Mayken González',  # RW | 19 años | 121 min
    ('M. González', 'Trujillanos'): 'Mayker González',  # LB | 37 años | 669 min
    # ─────────────── PAR (nuevos) ───────────────
    ('A. Cañete', 'Cerro Porteño'): 'A. Cañete (Cerro Porteño)',
    ('M. López', 'Deportes Iquique'): 'M. López (Sportivo San Lorenzo)',
    ('M. Martínez', 'Deportivo Santaní'): 'M. Martínez (Sportivo San Lorenzo)',
    ('M. Martínez', 'Guaraní'): 'M. Martínez (Guaraní)',
    ('M. Pérez', 'Racing Club'): 'M. Pérez (Cerro Porteño)',
    ('M. Pérez', 'Sportivo Luqueño'): 'M. Pérez (Sportivo Luqueño)',
    ('Á. Martínez', 'Cerro Porteño'): 'Á. Martínez (Cerro Porteño)',
    # ─────────────── ARG (nuevos) ───────────────
    ('A. Martínez', 'Nacional'): 'A. Martínez (Huracán)',
    ('B. Cabrera', 'San Martín Tucumán'): 'B. Cabrera (Lanús)',
    ('D. Martínez', 'Independiente'): 'D. Martínez (Independiente)',
    ('E. Giménez', 'Querétaro'): 'E. Giménez (Rosario Central)',
    ('E. Giménez', 'Sarmiento'): 'E. Giménez (Sarmiento)',
    ('F. Vázquez', 'Argentinos Juniors'): 'F. Vázquez (Argentinos Juniors)',
    ('F. Vázquez', 'Belgrano'): 'F. Vázquez (Belgrano)',
    ('F. Álvarez', 'Banfield'): 'F. Álvarez (Banfield)',
    ('G. González', 'River Plate'): 'G. González (River Plate)',
    ('G. González', 'Sarmiento'): 'G. González (Sarmiento)',
    ('J. Fernández', 'Atlético Tucumán'): 'J. Fernández (Atlético Tucumán)',
    ('J. Fernández', 'Rosario Central'): 'J. Fernández (Rosario Central)',
    ('L. Blondel', 'Chauvigny'): 'L. Blondel (Huracán)',
    ('L. Blondel', 'Huracán'): 'L. Blondel (Huracán)',
    ('L. Díaz', 'Racing Club'): 'L. Díaz (Racing Club)',
    ('L. Godoy', 'Atlético Tucumán'): 'L. Godoy (Atlético Tucumán)',
    ('L. Godoy', 'Independiente'): 'L. Godoy (Independiente)',
    ('L. González', 'Estudiantes Río Cuarto'): 'L. González (Estudiantes Río Cuarto)',
    ('L. Gómez', 'Independiente Rivadavia'): 'L. Gómez (Independiente Rivadavia)',
    ('L. Gómez', "Newell's Old Boys"): "L. Gómez (Newell's Old Boys)",
    ('L. Herrera', 'Estudiantes Río Cuarto Reserve'): 'L. Herrera (Estudiantes Río Cuarto)',
    ('L. Herrera', 'Pumas UNAM'): "L. Herrera (Newell's Old Boys)",
    ('L. Morales', 'Tigre'): 'L. Morales (Tigre)',
    ('L. Sequeira', 'Central Córdoba SdE'): 'L. Sequeira (Central Córdoba SdE)',
    ('L. Sequeira', 'Independiente Rivadavia'): 'L. Sequeira (Independiente Rivadavia)',
    ('M. Fernández', 'Tigre'): 'M. Fernández (Tigre)',
    ('M. García', "Newell's Old Boys"): "M. García (Newell's Old Boys)",
    ('M. Giménez', 'Argentinos Juniors'): 'M. Giménez (Argentinos Juniors)',
    ('M. Giménez', 'Boca Juniors'): 'M. Giménez (Boca Juniors)',
    ('M. Rodríguez', 'Defensa y Justicia'): 'M. Rodríguez (Defensa y Justicia)',
    ('M. Rodríguez', 'Krasnodar'): 'M. Rodríguez (Unión Santa Fe)',
    ('N. Paz', 'Banfield'): 'N. Paz (Banfield)',
    ('N. Paz', 'San Martín San Juan'): 'N. Paz (Unión Santa Fe)',
    ('S. López', 'Banfield'): 'S. López (Banfield)',
    ('S. López', 'Tigre'): 'S. López (Tigre)',
    ('S. Sosa', 'Defensa y Justicia'): 'S. Sosa (Defensa y Justicia)',
    ('S. Sosa', 'Racing Club'): 'S. Sosa (Racing Club)',
    ('T. González', 'Deportivo Riestra'): 'T. González (Deportivo Riestra)',
    ('T. González', 'Estudiantes Río Cuarto'): 'T. González (Estudiantes Río Cuarto)',
    ('T. Palacios', 'Estudiantes'): 'T. Palacios (Estudiantes)',
    # ─────────────── BRA (nuevos) ───────────────
    ('Allan', 'Botafogo'): 'Allan (Botafogo)',
    ('Bruninho', 'Athletico Paranaense'): 'Bruninho (Athletico Paranaense)',
    ('Bruninho', 'Red Bull Bragantino'): 'Bruninho (Red Bull Bragantino)',
    ('Bruno Henrique', 'Internacional'): 'Bruno Henrique (Internacional)',
    ('Claudinho', 'Athletico Paranaense'): 'Claudinho (Athletico Paranaense)',
    ('Claudinho', 'Sport Recife'): 'Claudinho (Vitória)',
    ('Danilo', 'Botafogo'): 'Danilo (Botafogo)',
    ('Dudu', 'Chapecoense'): 'Dudu (Chapecoense)',
    ('Dudu', 'Vitória'): 'Dudu (Vitória)',
    ('Erick', 'Vitória'): 'Erick (Vitória)',
    ('Fabinho', 'Red Bull Bragantino'): 'Fabinho (Red Bull Bragantino)',
    ('Fernando', 'Chapecoense'): 'Fernando (Chapecoense)',
    ('Fernando', 'Red Bull Bragantino'): 'Fernando (Red Bull Bragantino)',
    ('Gabriel', 'Mirassol'): 'Gabriel (Mirassol)',
    ('Gabriel', 'Vitória'): 'Gabriel (Vitória)',
    ('Gustavo Henrique', 'Santos U20'): 'Gustavo Henrique (Santos)',
    ('João Paulo', 'Chapecoense'): 'João Paulo (Chapecoense)',
    ('João Paulo', 'Santos B'): 'João Paulo (Bahia)',
    ('João Pedro', 'Atlético GO'): 'João Pedro (Remo)',
    ('João Pedro', 'Grêmio'): 'João Pedro (Grêmio)',
    ('João Victor', 'Flamengo U20'): 'João Victor (Flamengo)',
    ('João Victor', 'Internacional'): 'João Victor (Internacional)',
    ('João Victor', 'Mirassol'): 'João Victor (Mirassol)',
    ('João Vitor', 'Athletico Paranaense'): 'João Vitor (Athletico Paranaense)',
    ('João Vitor', 'Londrina'): 'João Vitor (Chapecoense)',
    ('Lucas Silva', 'Cruzeiro'): 'Lucas Silva (Cruzeiro)',
    ('Lucas Silva', 'Vitória'): 'Lucas Silva (Vitória)',
    ('Marlon', 'Grêmio'): 'Marlon (Grêmio)',
    ('Marlon', 'Remo'): 'Marlon (Remo)',
    ('Marquinhos', 'Botafogo'): 'Marquinhos (Botafogo)',
    ('Marquinhos', 'Cruzeiro'): 'Marquinhos (Cruzeiro)',
    ('Matheus Pereira', 'Cruzeiro'): 'Matheus Pereira (Cruzeiro)',
    ('Matheuzinho', 'Vitória'): 'Matheuzinho (Vitória)',
    ('Paulinho', 'Botafogo'): 'Paulinho (Botafogo)',
    ('Paulinho', 'Internacional'): 'Paulinho (Internacional)',
    ('Paulinho', 'Palmeiras'): 'Paulinho (Palmeiras)',
    ('Renê', 'Fluminense'): 'Renê (Fluminense)',
    ('Renê', 'Vitória'): 'Renê (Vitória)',
    ('Ronaldo', 'Bahia'): 'Ronaldo (Bahia)',
    ('Tetê', 'São Paulo U20'): 'Tetê (São Paulo)',
    ('Vitinho', 'Corinthians'): 'Vitinho (Corinthians)',
    # ─────────────── URU (nuevos) ───────────────
    ('A. Hernández', 'Cerro Largo'): 'A. Hernández (Cerro Largo)',
    ('A. Hernández', 'Peñarol'): 'A. Hernández (Peñarol)',
    ('F. González', 'Peñarol'): 'F. González (Peñarol)',
    ('F. González', 'Racing'): 'F. González (Racing)',
    ('F. Martínez', 'Boston River'): 'F. Martínez (Boston River)',
    ('F. Martínez', 'Liverpool'): 'F. Martínez (Liverpool)',
    ('F. Martínez', 'Torque'): 'F. Martínez (Torque)',
    ('G. Rodríguez', 'Cerro'): 'G. Rodríguez (Cerro)',
    ('G. Rodríguez', 'Torque'): 'G. Rodríguez (Torque)',
    ('J. Millán', 'Danubio'): 'J. Millán (Danubio)',
    ('J. Millán', 'Fluminense'): 'J. Millán (Nacional)',
    ('L. Fernández', 'Central Español'): 'L. Fernández (Central Español)',
    ('L. Fernández', 'Peñarol'): 'L. Fernández (Peñarol)',
    ('L. Rodríguez', 'Albion'): 'L. Rodríguez (Albion)',
    ('L. Rodríguez', 'Nacional'): 'L. Rodríguez (Nacional)',
    ('M. Ferreira', 'Danubio'): 'M. Ferreira (Danubio)',
    ('M. Ferreira', 'Racing'): 'M. Ferreira (Racing)',
    ('M. González', 'Boston River'): 'M. González (Boston River)',
    ('M. González', 'Central Español'): 'M. González (Central Español)',
    ('M. González', 'Deportivo Maldonado'): 'M. González (Deportivo Maldonado)',
    ('N. Fernández', "Al Zawra'a"): 'N. Fernández (Progreso)',
    ('N. Fernández', 'Peñarol'): 'N. Fernández (Peñarol)',
    ('S. Rodríguez', 'Danubio'): 'S. Rodríguez (Danubio)',
    ('S. Rodríguez', 'Torque'): 'S. Rodríguez (Torque)',
    # ─────────────── COL (nuevos) ───────────────
    ('D. Moreno', 'Medellín'): 'D. Moreno (Medellín)',
    ('D. Moreno', 'Once Caldas'): 'D. Moreno (Once Caldas)',
    ('D. Quintero', 'Llaneros'): 'D. Quintero (Llaneros)',
    ('D. Quintero', 'Millonarios'): 'D. Quintero (Millonarios)',
    ('E. Moreno', 'Deportivo Pereira'): 'E. Moreno (Deportivo Pereira)',
    ('F. Mosquera', 'Jaguares de Córdoba'): 'F. Mosquera (Jaguares de Córdoba)',
    ('J. Castillo', 'Alianza'): 'J. Castillo (Alianza)',
    ('J. Castillo', 'Fortaleza'): 'J. Castillo (Fortaleza)',
    ('J. Mena', 'Boyacá Chicó'): 'J. Mena (Boyacá Chicó)',
    ('J. Mena', 'Medellín'): 'J. Mena (Medellín)',
    ('J. Mena', 'Águilas Doradas'): 'J. Mena (Águilas Doradas)',
    ('J. Mosquera', 'Atlético Bucaramanga'): 'J. Mosquera (Atlético Bucaramanga)',
    ('J. Mosquera', 'Tolima'): 'J. Mosquera (Tolima)',
    ('J. Quiñónes', 'Deportivo Pasto'): 'J. Quiñónes (Deportivo Pasto)',
    ('J. Quiñónes', 'Once Caldas'): 'J. Quiñónes (Once Caldas)',
    ('J. Ramírez', 'Cúcuta Deportivo'): 'J. Ramírez (Cúcuta Deportivo)',
    ('J. Ramírez', 'Llaneros'): 'J. Ramírez (Llaneros)',
    ('J. Valencia', 'Necaxa'): 'J. Valencia (Inter Bogotá)',
    ('J. Valencia', 'Tolima'): 'J. Valencia (Tolima)',
    ('J. Viveros', 'Alianza'): 'J. Viveros (Alianza)',
    ('J. Zapata', 'Atlético Nacional'): 'J. Zapata (Atlético Nacional)',
    ('J. Zapata', 'Once Caldas'): 'J. Zapata (Once Caldas)',
    ('K. Londoño', 'Atlético Bucaramanga'): 'K. Londoño (Atlético Bucaramanga)',
    ('K. Londoño', 'Cúcuta Deportivo'): 'K. Londoño (Cúcuta Deportivo)',
    ('Y. Moreno', 'Marathón'): 'Y. Moreno (Jaguares de Córdoba)',
    ('Y. Moreno', 'Tolima'): 'Y. Moreno (Tolima)',
    # ─────────────── ECU (nuevos) ───────────────
    ('A. Mina', 'Emelec'): 'A. Mina (Emelec)',
    ('A. Rodríguez', 'Independiente del Valle'): 'A. Rodríguez (Independiente del Valle)',
    ('A. Rodríguez', 'Universidad Católica'): 'A. Rodríguez (Universidad Católica)',
    ('B. Caicedo', 'Libertad'): 'B. Caicedo (Libertad)',
    ('B. Caicedo', 'Orense'): 'B. Caicedo (Orense)',
    ('B. Carabalí', 'Aucas'): 'B. Carabalí (Aucas)',
    ('B. Carabalí', 'Barcelona'): 'B. Carabalí (Barcelona)',
    ('D. Cabezas', 'Libertad'): 'D. Cabezas (Libertad)',
    ('E. Caicedo', 'Delfin'): 'E. Caicedo (Delfin)',
    ('E. Caicedo', 'Libertad'): 'E. Caicedo (Libertad)',
    ('E. Caicedo', 'Mushuc Runa'): 'E. Caicedo (Mushuc Runa)',
    ('J. Angulo', 'Barcelona'): 'J. Angulo (Barcelona)',
    ('J. Angulo', 'Manta'): 'J. Angulo (Manta)',
    ('J. Arroyo', 'Independiente del Valle'): 'J. Arroyo (Independiente del Valle)',
    ('J. Arroyo', 'Leones del Norte'): 'J. Arroyo (Leones del Norte)',
    ('J. Ayoví', 'Emelec'): 'J. Ayoví (Emelec)',
    ('J. Ayoví', 'Guayaquil City'): 'J. Ayoví (Guayaquil City)',
    ('J. Caicedo', 'Guayaquil City'): 'J. Caicedo (Guayaquil City)',
    ('J. Caicedo', 'Mushuc Runa'): 'J. Caicedo (Mushuc Runa)',
    ('J. Caicedo', 'Técnico Universitario'): 'J. Caicedo (Técnico Universitario)',
    ('J. Chalá', 'Barcelona'): 'J. Chalá (Barcelona)',
    ('J. Chalá', 'Macará'): 'J. Chalá (Macará)',
    ('J. Jiménez', 'Manta'): 'J. Jiménez (Manta)',
    ('J. Mina', 'Manta'): 'J. Mina (Manta)',
    ('J. Mina', 'Universidad Católica'): 'J. Mina (Universidad Católica)',
    ('J. Nazareno', 'Manta'): 'J. Nazareno (Manta)',
    ('J. Quiñónez', 'Barcelona'): 'J. Quiñónez (Barcelona)',
    ('J. Quiñónez', 'Guayaquil City'): 'J. Quiñónez (Guayaquil City)',
    ('J. Rodríguez', 'LDU Quito'): 'J. Rodríguez (LDU Quito)',
    ('J. Rodríguez', 'Libertad'): 'J. Rodríguez (Libertad)',
    ('M. Díaz', 'Deportivo Cuenca'): 'M. Díaz (Deportivo Cuenca)',
    ('M. Díaz', 'Universidad Católica'): 'M. Díaz (Universidad Católica)',
    ('R. Mina', 'LDU Quito'): 'R. Mina (LDU Quito)',
    ('V. Branda', 'Libertad'): 'V. Branda (Libertad)',
    # ─────────────── CHI (nuevos) ───────────────
    ('A. Castillo', 'Cobresal'): 'A. Castillo (Cobresal)',
    ('A. Castillo', "O'Higgins"): "A. Castillo (O'Higgins)",
    ('C. Morales', 'Deportes Limache'): 'C. Morales (Deportes Limache)',
    ('C. Morales', "O'Higgins"): "C. Morales (O'Higgins)",
    ('I. González', 'Everton'): 'I. González (Everton)',
    ('I. González', 'Univ. Concepción'): 'I. González (Univ. Concepción)',
    ('J. Tapia', 'La Serena'): 'J. Tapia (La Serena)',
    ('J. Tapia', "O'Higgins"): "J. Tapia (O'Higgins)",
    ('L. Romero', 'Concepción'): 'L. Romero (Concepción)',
    ('L. Romero', 'Juárez'): 'L. Romero (Universidad de Chile)',
    ('M. Sandoval', 'Audax Italiano'): 'M. Sandoval (Audax Italiano)',
    ('M. Sandoval', 'Concepción'): 'M. Sandoval (Concepción)',
    ('Santiago Silva', 'Nacional'): 'Santiago Silva (Huachipato)',
    ('Santiago Silva', 'Univ. Concepción'): 'Santiago Silva (Univ. Concepción)',
    # ─────────────── PER (nuevos) ───────────────
    ('A. Muñoz', 'Alianza Atlético'): 'A. Muñoz (Alianza Atlético)',
    ('A. Muñoz', 'UTC Cajamarca'): 'A. Muñoz (UTC Cajamarca)',
    ('A. Rodríguez', 'Comerciantes Unidos'): 'A. Rodríguez (Comerciantes Unidos)',
    ('C. Zambrano', 'Peñarol Reserve'): 'C. Zambrano (Sport Boys)',
    ('C. Zambrano', 'Sport Boys'): 'C. Zambrano (Sport Boys)',
    ('J. Castillo', 'ES Tunis'): 'J. Castillo (Universitario)',
    ('J. Herrera', 'Comerciantes Unidos'): 'J. Herrera (Comerciantes Unidos)',
    ('J. Herrera', 'Cusco'): 'J. Herrera (Cusco)',
    ('J. Soto', 'FC Cajamarca'): 'J. Soto (FC Cajamarca)',
    ('J. Torres', 'Juan Pablo II College'): 'J. Torres (Juan Pablo II College)',
    ('J. Torres', 'Phoenix Rising'): 'J. Torres (Sport Boys)',
    ('R. Suárez', 'Alianza Atlético'): 'R. Suárez (Alianza Atlético)',
    ('R. Suárez', 'FC Cajamarca'): 'R. Suárez (FC Cajamarca)',
    ('S. González', 'Sporting Cristal'): 'S. González (Sporting Cristal)',
    ('A. Arroyo', 'UTC Cajamarca'): 'A. Arroyo (UTC Cajamarca)',
    ('A. Duarte', 'Alianza Lima'): 'A. Duarte (Alianza Lima)',
    ('A. González', 'Deportivo Garcilaso'): 'A. González (Deportivo Garcilaso)',
    ('A. Gutiérrez', 'ADT'): 'A. Gutiérrez (ADT)',
    ('A. Gómez', 'Deportivo Garcilaso'): 'A. Gómez (Deportivo Garcilaso)',
    ('A. Quintana', 'Los Chankas'): 'A. Quintana (Los Chankas)',
    ('A. Ramos', 'Melgar'): 'A. Ramos (Melgar)',
    ('A. Salazar', 'Deportivo Garcilaso'): 'A. Salazar (Deportivo Garcilaso)',
    ('A. Sánchez', 'Juan Pablo II College'): 'A. Sánchez (Juan Pablo II College)',
    ('B. Angulo', 'CD Moquegua'): 'B. Angulo (CD Moquegua)',
    ('B. Palacios', 'FC Cajamarca'): 'B. Palacios (FC Cajamarca)',
    ('B. Palacios', 'Universidad Católica'): 'B. Palacios (Universidad Católica)',
    ('C. Ramírez', 'CD Moquegua'): 'C. Ramírez (CD Moquegua)',
    ('D. Ramírez', 'CD Moquegua'): 'D. Ramírez (CD Moquegua)',
    ('D. Rodríguez', 'Atlético Grau'): 'D. Rodríguez (Atlético Grau)',
    ('D. Romero', 'Universitario'): 'D. Romero (Universitario)',
    ('E. Castillo', 'Alianza Lima'): 'E. Castillo (Alianza Lima)',
    ('F. Torres', 'Los Chankas'): 'F. Torres (Los Chankas)',
    ('Gabriel', 'Sporting Cristal'): 'Gabriel (Sporting Cristal)',
    ('I. Tapia', 'Atlético Grau'): 'I. Tapia (Atlético Grau)',
    ('J. Escobar', 'Melgar'): 'J. Escobar (Melgar)',
    ('J. González', 'Sporting Cristal'): 'J. González (Sporting Cristal)',
    ('J. Jiménez', 'CD Moquegua'): 'J. Jiménez (CD Moquegua)',
    ('J. Medina', 'FC Cajamarca'): 'J. Medina (FC Cajamarca)',
    ('J. Núñez', 'UTC Cajamarca'): 'J. Núñez (UTC Cajamarca)',
    ('J. Palomino', 'Los Chankas'): 'J. Palomino (Los Chankas)',
    ('J. Pérez', 'Alianza Atlético'): 'J. Pérez (Alianza Atlético)',
    ('J. Quintero', 'Los Chankas'): 'J. Quintero (Los Chankas)',
    ('J. Quiñones', 'Alianza Atlético'): 'J. Quiñones (Alianza Atlético)',
    ('J. Rojas', 'ADT'): 'J. Rojas (ADT)',
    ('J. Salas', 'Melgar'): 'J. Salas (Melgar)',
    ('J. Sinisterra', 'Deportivo Garcilaso'): 'J. Sinisterra (Deportivo Garcilaso)',
    ('J. Torres', 'Sport Boys'): 'J. Torres (Sport Boys)',
    ('J. Valencia', 'ADT'): 'J. Valencia (ADT)',
    ('J. Valoyes', 'Sport Huancayo'): 'J. Valoyes (Sport Huancayo)',
    ('K. Moreno', 'CD Moquegua'): 'K. Moreno (CD Moquegua)',
    ('L. Díaz', 'Sporting Cristal'): 'L. Díaz (Sporting Cristal)',
    ('L. Sosa', 'Sporting Cristal'): 'L. Sosa (Sporting Cristal)',
    ('M. Amondarain', 'Cienciano'): 'M. Amondarain (Cienciano)',
    ('M. Peralta', 'Juan Pablo II College'): 'M. Peralta (Juan Pablo II College)',
    ('M. Pérez', 'Comerciantes Unidos'): 'M. Pérez (Comerciantes Unidos)',
    ('M. Rodríguez', 'Sporting Cristal'): 'M. Rodríguez (Sporting Cristal)',
    ('M. Torres', 'Los Chankas'): 'M. Torres (Los Chankas)',
    ('P. Guzmán', 'Comerciantes Unidos'): 'P. Guzmán (Comerciantes Unidos)',
    ('P. Álvarez', 'Atlético Grau'): 'P. Álvarez (Atlético Grau)',
    ('R. Rojas', 'Comerciantes Unidos'): 'R. Rojas (Comerciantes Unidos)',
    ('R. Sandoval', 'Cienciano'): 'R. Sandoval (Cienciano)',
    ('S. Arias', 'Cienciano'): 'S. Arias (Cienciano)',
    ('S. Fernández', 'Alianza Atlético'): 'S. Fernández (Alianza Atlético)',
    ('S. González', 'Atlético Grau'): 'S. González (Atlético Grau)',
    # ─────────────── VEN (nuevos) ───────────────
    ('A. Romero', 'Monagas'): 'A. Romero (Monagas)',
    ('J. Caraballo', 'Deportivo Táchira'): 'J. Caraballo (Deportivo Táchira)',
    ('J. Graterol', 'Academia Puerto Cabello'): 'J. Graterol (Academia Puerto Cabello)',
    ('J. Gutiérrez', 'Estudiantes de Mérida'): 'J. Gutiérrez (Estudiantes de Mérida)',
    ('J. Gutiérrez', 'Universitario'): 'J. Gutiérrez (Deportivo La Guaira)',
    ('J. Hernández', 'Academia Puerto Cabello'): 'J. Hernández (Academia Puerto Cabello)',
    ('J. Hernández', 'Estudiantes de Mérida'): 'J. Hernández (Estudiantes de Mérida)',
    ('J. Martínez', 'Academia Puerto Cabello'): 'J. Martínez (Academia Puerto Cabello)',
    ('J. Moreno', 'Academia Puerto Cabello'): 'J. Moreno (Academia Puerto Cabello)',
    ('J. Moreno', 'KuPS'): 'J. Moreno (Carabobo)',
    ('J. Moreno', 'Portuguesa'): 'J. Moreno (Portuguesa)',
    ('J. Moreno', 'Zamora'): 'J. Moreno (Zamora)',
    ('J. Sánchez', 'Deportivo La Guaira'): 'J. Sánchez (Deportivo La Guaira)',
    ('J. Sánchez', 'Deportivo Táchira'): 'J. Sánchez (Deportivo Táchira)',
    ('J. Vargas', 'Academia Puerto Cabello'): 'J. Vargas (Academia Puerto Cabello)',
    ('J. Vargas', 'Metropolitanos'): 'J. Vargas (Metropolitanos)',
    ('L. Peña', 'Rayo Zuliano'): 'L. Peña (Rayo Zuliano)',
    ('M. González', 'Deportivo La Guaira'): 'M. González (Deportivo La Guaira)',
    ('R. Ramírez', 'Al Shorta'): 'R. Ramírez (UCV)',
    ('R. Ramírez', 'Rayo Zuliano'): 'R. Ramírez (Rayo Zuliano)',
    ('Y. Lacruz Marquez', 'Estudiantes de Mérida'): 'Y. Lacruz Marquez (Estudiantes de Mérida)',
    ('A. Cardozo', 'Anzoátegui FC'): 'A. Cardozo (Anzoátegui FC)',
    ('A. Fernández', 'Caracas'): 'A. Fernández (Caracas)',
    ('A. Flores', 'Zamora'): 'A. Flores (Zamora)',
    ('A. González', 'Carabobo'): 'A. González (Carabobo)',
    ('A. Maldonado', 'Trujillanos'): 'A. Maldonado (Trujillanos)',
    ('A. Martínez', 'UCV'): 'A. Martínez (UCV)',
    ('A. Moreno', 'Anzoátegui FC'): 'A. Moreno (Anzoátegui FC)',
    ('A. Polo', 'Trujillanos'): 'A. Polo (Trujillanos)',
    ('A. Pérez', 'Deportivo Táchira'): 'A. Pérez (Deportivo Táchira)',
    ('A. Uribe', 'Deportivo La Guaira'): 'A. Uribe (Deportivo La Guaira)',
    ('A. Velasco', 'Anzoátegui FC'): 'A. Velasco (Anzoátegui FC)',
    ('A. Vera', 'Anzoátegui FC'): 'A. Vera (Anzoátegui FC)',
    ('B. Rodríguez', 'Zamora'): 'B. Rodríguez (Zamora)',
    ('C. Ramírez', 'Monagas'): 'C. Ramírez (Monagas)',
    ('C. Suárez', 'Portuguesa'): 'C. Suárez (Portuguesa)',
    ('E. Castillo', 'Carabobo'): 'E. Castillo (Carabobo)',
    ('F. Benítez', 'Caracas'): 'F. Benítez (Caracas)',
    ('F. Chaverra', 'Trujillanos'): 'F. Chaverra (Trujillanos)',
    ('F. Díaz', 'Rayo Zuliano'): 'F. Díaz (Rayo Zuliano)',
    ('F. González', 'Monagas'): 'F. González (Monagas)',
    ('G. Benítez', 'Zamora'): 'G. Benítez (Zamora)',
    ('G. Montes', 'Estudiantes de Mérida'): 'G. Montes (Estudiantes de Mérida)',
    ('J. Arias', 'Rayo Zuliano'): 'J. Arias (Rayo Zuliano)',
    ('J. Bolívar', 'UCV'): 'J. Bolívar (UCV)',
    ('J. Caraballo', 'Monagas'): 'J. Caraballo (Monagas)',
    ('J. Castillo', 'Academia Puerto Cabello'): 'J. Castillo (Academia Puerto Cabello)',
    ('J. Correa', 'Deportivo La Guaira'): 'J. Correa (Deportivo La Guaira)',
    ('J. Cuesta', 'UCV'): 'J. Cuesta (UCV)',
    ('J. Durán', 'Carabobo'): 'J. Durán (Carabobo)',
    ('J. Figueroa', 'Trujillanos'): 'J. Figueroa (Trujillanos)',
    ('J. Fuentes', 'Carabobo'): 'J. Fuentes (Carabobo)',
    ('J. González', 'Zamora'): 'J. González (Zamora)',
    ('J. Gutiérrez', 'Deportivo La Guaira'): 'J. Gutiérrez (Deportivo La Guaira)',
    ('J. Gómez', 'Rayo Zuliano'): 'J. Gómez (Rayo Zuliano)',
    ('J. Lovera', 'Anzoátegui FC'): 'J. Lovera (Anzoátegui FC)',
    ('J. Moreno', 'Anzoátegui FC'): 'J. Moreno (Anzoátegui FC)',
    ('J. Moreno', 'Carabobo'): 'J. Moreno (Carabobo)',
    ('J. Mosquera', 'Zamora'): 'J. Mosquera (Zamora)',
    ('J. Obando', 'Carabobo'): 'J. Obando (Carabobo)',
    ('J. Ortiz', 'Trujillanos'): 'J. Ortiz (Trujillanos)',
    ('J. Pérez', 'Carabobo'): 'J. Pérez (Carabobo)',
    ('J. Quintero', 'Caracas'): 'J. Quintero (Caracas)',
    ('J. Ramírez', 'Metropolitanos'): 'J. Ramírez (Metropolitanos)',
    ('J. Soto', 'Portuguesa'): 'J. Soto (Portuguesa)',
    ('J. Zapata', 'UCV'): 'J. Zapata (UCV)',
    ('K. Silva', 'UCV'): 'K. Silva (UCV)',
    ('L. González', 'Anzoátegui FC'): 'L. González (Anzoátegui FC)',
    ('L. González', 'Deportivo Táchira'): 'L. González (Deportivo Táchira)',
    ('L. Martínez', 'Carabobo'): 'L. Martínez (Carabobo)',
    ('L. Morales', 'UCV'): 'L. Morales (UCV)',
    ('L. Mosquera', 'Trujillanos'): 'L. Mosquera (Trujillanos)',
    ('L. Pérez', 'Anzoátegui FC'): 'L. Pérez (Anzoátegui FC)',
    ('L. Romero', 'Academia Puerto Cabello'): 'L. Romero (Academia Puerto Cabello)',
    ('M. Acuña', 'Portuguesa'): 'M. Acuña (Portuguesa)',
    ('M. Díaz', 'Metropolitanos'): 'M. Díaz (Metropolitanos)',
    ('M. Fernández', 'Trujillanos'): 'M. Fernández (Trujillanos)',
    ('N. Hernández', 'Deportivo La Guaira'): 'N. Hernández (Deportivo La Guaira)',
    ('P. Álvarez', 'Anzoátegui FC'): 'P. Álvarez (Anzoátegui FC)',
    ('R. Figueroa', 'Metropolitanos'): 'R. Figueroa (Metropolitanos)',
    ('R. Garcés', 'Metropolitanos'): 'R. Garcés (Metropolitanos)',
    ('R. Peralta', 'Monagas'): 'R. Peralta (Monagas)',
    ('R. Ramírez', 'UCV'): 'R. Ramírez (UCV)',
    ('R. Rojas', 'Portuguesa'): 'R. Rojas (Portuguesa)',
    ('S. Mendoza', 'Carabobo'): 'S. Mendoza (Carabobo)',
    ('S. Ramírez', 'Metropolitanos'): 'S. Ramírez (Metropolitanos)',
    ('S. Sosa', 'UCV'): 'S. Sosa (UCV)',
    ('V. Rodríguez', 'UCV'): 'V. Rodríguez (UCV)',
    # ─────────────── MEX (nuevos) ───────────────
    ('A. González', 'Atlas'): 'A. González (Atlas)',
    ('A. González', 'Olympiacos Piraeus'): 'A. González (Guadalajara)',
    ('A. Sánchez', 'Atlas'): 'A. Sánchez (Atlas)',
    ('A. Sánchez', 'Atlético de San Luis'): 'A. Sánchez (Atlético de San Luis)',
    ('C. Vargas', 'Atlas'): 'C. Vargas (Atlas)',
    ('C. Vargas', 'Necaxa'): 'C. Vargas (Necaxa)',
    ('E. Aguirre', 'Monterrey'): 'E. Aguirre (Monterrey)',
    ('E. Aguirre', 'Santos Laguna'): 'E. Aguirre (Santos Laguna)',
    ('E. López', 'Juárez'): 'E. López (Juárez)',
    ('E. López', 'Toluca'): 'E. López (Toluca)',
    ('E. Álvarez', 'Guadalajara'): 'E. Álvarez (Guadalajara)',
    ('I. Moreno', 'León'): 'I. Moreno (León)',
    ('I. Moreno', 'Puebla'): 'I. Moreno (Puebla)',
    ('J. Díaz', 'Cruz Azul Hidalgo'): 'J. Díaz (Cruz Azul)',
    ('J. Díaz', 'Toluca'): 'J. Díaz (Toluca)',
    ('J. Pérez', 'Guadalajara'): 'J. Pérez (Guadalajara)',
    ('J. Pérez', 'Santos Laguna'): 'J. Pérez (Santos Laguna)',
    ('J. Rodríguez', 'Atlas'): 'J. Rodríguez (Atlas)',
    ('J. Rodríguez', 'Juárez'): 'J. Rodríguez (Juárez)',
    ('J. Rodríguez', 'Monterrey'): 'J. Rodríguez (Monterrey)',
    ('J. Torres', 'Juárez'): 'J. Torres (Juárez)',
    ('J. Torres', 'Necaxa'): 'J. Torres (Necaxa)',
    ('L. Romero', 'Cruz Azul'): 'L. Romero (Cruz Azul)',
    ('R. Juárez', 'América'): 'R. Juárez (América)',
    ('R. Juárez', 'Juárez U21'): 'R. Juárez (Juárez)',
    ('V. Guzmán', 'Monterrey'): 'V. Guzmán (Monterrey)',
    ('V. Guzmán', 'Toluca'): 'V. Guzmán (Toluca)',
    # ─────────────── MLS (nuevos) ───────────────
    ('A. Herrera', 'Columbus Crew'): 'A. Herrera (Columbus Crew)',
    ('J. Nelson', 'Bolton Wanderers'): 'J. Nelson (Austin FC)',
    ('J. Nelson', 'LA Galaxy'): 'J. Nelson (LA Galaxy)',
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

    # Aplicar renombrado de jugadores homónimos
    if 'Player' in df.columns and 'Team' in df.columns:
        for (player, team), new_name in PLAYER_NAME_OVERRIDES.items():
            mask = (df['Player'] == player) & (df['Team'] == team)
            if mask.any():
                df.loc[mask, 'Player'] = new_name

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


def _parquet_path(xlsx_path: str) -> str:
    return xlsx_path.replace('.xlsx', '.parquet')


def _load_with_parquet_cache(xlsx_path: str, league_name: str | None = None):
    """Read xlsx or its parquet cache (whichever is newer). Save parquet after processing."""
    pq_path = _parquet_path(xlsx_path)
    xlsx_mtime = os.path.getmtime(xlsx_path)
    use_cache = os.path.exists(pq_path) and os.path.getmtime(pq_path) >= xlsx_mtime
    if use_cache:
        return pd.read_parquet(pq_path)
    # Excel is newer — reprocess and update cache
    df = pd.read_excel(xlsx_path)
    if league_name and 'Team' in df.columns:
        for (team, league), new_name in TEAM_NAME_OVERRIDES.items():
            if league == league_name:
                df.loc[df['Team'] == team, 'Team'] = new_name
    processed = process_database(df)
    try:
        processed.to_parquet(pq_path, index=False)
    except Exception:
        pass  # parquet save failure is non-fatal
    return processed


@st.cache_data
def load_and_process_data():
    """Load PAR.xlsx (or parquet cache) and process it. Cached by Streamlit."""
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'PAR.xlsx'),
        os.path.join('data', 'PAR.xlsx'),
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return _load_with_parquet_cache(path)
    raise FileNotFoundError("PAR.xlsx not found in data/ directory")


@st.cache_data
def load_external_league(league_name: str):
    """Load and process an external league file (e.g. ARG.xlsx or BRA.xlsx).
    Uses parquet cache when available and up-to-date. Returns None if file not found."""
    possible_paths = [
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', f'{league_name}.xlsx'),
        os.path.join('data', f'{league_name}.xlsx'),
    ]
    for path in possible_paths:
        if os.path.exists(path):
            return _load_with_parquet_cache(path, league_name)
    return None
