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
            # Aplicar overrides de equipo ANTES de procesar (deben preceder a PLAYER_NAME_OVERRIDES)
            if 'Team' in df.columns:
                for (team, league), new_name in TEAM_NAME_OVERRIDES.items():
                    if league == league_name:
                        df.loc[df['Team'] == team, 'Team'] = new_name
            return process_database(df)
    return None
