import os
import sys
from pathlib import Path

# Agregar la carpeta backend al path de Python
sys.path.append(str(Path(__file__).resolve().parent))

from db import get_db

def poblar_semillas():
    print("Iniciando actualización de semillas en la Base de Datos...")
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. Asegurar que existan Géneros base
        generos = [('Fantasía',), ('Animación',), ('Acción',)]
        for g in generos:
            cursor.execute("""
                IF NOT EXISTS (SELECT 1 FROM Generos WHERE Nombre = ?)
                INSERT INTO Generos (Nombre, Descripcion, IdEstado) VALUES (?, 'Género principal', 1)
            """, (g[0], g[0]))

        # 2. Insertar las 4 películas semilla oficiales
        peliculas_semilla = [
            (1, 1, 'Harry Potter', 152, '10+', '2026-01-01', 'Película de Fantasía y Magia', 1),
            (2, 1, 'Cars', 117, 'Todo público', '2026-01-01', 'Película Animada de Autos', 1),
            (3, 1, 'Spiderman', 121, '12+', '2026-01-01', 'Película de Acción y Superhéroes', 1),
            (2, 1, 'Toy Story', 81, 'Todo público', '2026-01-01', 'Película Animada de Juguetes', 1)
        ]

        for p in peliculas_semilla:
            cursor.execute("""
                IF NOT EXISTS (SELECT 1 FROM Peliculas WHERE Titulo = ?)
                INSERT INTO Peliculas (IdGenero, IdCine, Titulo, Duracion, Clasificacion, FechaEstreno, Descripcion, IdEstado)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (p[2], p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7]))
            
        conn.commit()
        print("¡Las 4 películas semilla fueron insertadas correctamente en SQL Server!")

if __name__ == "__main__":
    poblar_semillas()
