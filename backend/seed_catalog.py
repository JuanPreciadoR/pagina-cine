from datetime import date, datetime, time

from db import get_db


CINEMAS = {
    "Bogotá": ("Andino", "Plaza Central", "Titán Plaza", "Santa Fe"),
    "Medellín": ("El Tesoro", "Oviedo", "Florida"),
    "Cali": ("Chipichape", "Unicentro", "Jardín Plaza"),
}
FILMS = (
    ("Harry Potter y la piedra filosofal", "harryPotter.webp", "Fantasía", 152, "Todos", "2001-11-16"),
    ("Cars", "cars.webp", "Animación", 117, "Todos", "2006-06-09"),
    ("Toy Story", "toyStory.webp", "Animación", 81, "Todos", "1995-11-22"),
    ("Spider-Man", "spiderman.webp", "Acción", 121, "Todos", "2002-05-03"),
)
SHOWTIMES = ("12:30", "15:10", "17:45", "20:20", "22:50")
SEAT_ROWS = "ABCDE"
SEATS_PER_ROW = 6
TICKET_PRICE = 16000
PAYMENT_TYPES = ("Efectivo", "Tarjeta Crédito", "Tarjeta Débito", "PSE", "Nequi", "Daviplata")
STATES = (
    ("Activo", "Registro activo dentro del sistema"),
    ("Inactivo", "Registro desactivado sin borrar su historial"),
    ("Suspendido", "Registro suspendido temporalmente"),
    ("Pendiente", "Registro pendiente de validación"),
)


def get_or_create_state(cursor, name, description):
    cursor.execute("SELECT IdEstado FROM Estados WHERE Nombre = ?", (name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute(
        "INSERT INTO Estados (Nombre, Descripcion) OUTPUT INSERTED.IdEstado VALUES (?, ?)",
        (name, description),
    )
    return cursor.fetchone()[0]


def get_or_create_named(cursor, table, name, state_id):
    id_column = {
        "Generos": "IdGenero",
        "TiposAsiento": "IdTipoAsiento",
        "TiposPago": "IdTipoPago",
    }[table]
    cursor.execute(f"SELECT {id_column} FROM {table} WHERE Nombre = ?", (name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    cursor.execute(
        f"INSERT INTO {table} (Nombre, Descripcion, IdEstado) OUTPUT INSERTED.{id_column} VALUES (?, ?, ?)",
        (name, f"{name} para CineStar", state_id),
    )
    return cursor.fetchone()[0]


def add_cinemas(cursor, state_id):
    cinemas = []
    for city, venues in CINEMAS.items():
        for venue in venues:
            cursor.execute(
                "SELECT IdCine FROM Cines WHERE Nombre = ? AND Ciudad = ?",
                (venue, city),
            )
            row = cursor.fetchone()
            if row:
                cinema_id = row[0]
            else:
                cursor.execute(
                    "INSERT INTO Cines (Nombre, Ciudad, Tipo, Documento, EsExtranjero, Descripcion, IdEstado) "
                    "OUTPUT INSERTED.IdCine VALUES (?, ?, ?, ?, 0, ?, ?)",
                    (venue, city, "Sede", f"CINE-{city[:3].upper()}-{len(cinemas) + 1:02d}", f"CineStar {venue}", state_id),
                )
                cinema_id = cursor.fetchone()[0]
            cinemas.append((city, venue, cinema_id))
    return cinemas


def add_seats_and_shows(cursor, state_id, seat_type_id, cinemas, films):
    today = date.today()
    for _, venue, cinema_id in cinemas:
        cursor.execute("SELECT IdSala FROM Salas WHERE IdCine = ? AND Nombre = ?", (cinema_id, "Sala 1"))
        row = cursor.fetchone()
        if row:
            room_id = row[0]
        else:
            cursor.execute(
                "INSERT INTO Salas (IdCine, Nombre, Capacidad, Descripcion, IdEstado) "
                "OUTPUT INSERTED.IdSala VALUES (?, ?, ?, ?, ?)",
                (cinema_id, "Sala 1", len(SEAT_ROWS) * SEATS_PER_ROW, f"Sala principal de {venue}", state_id),
            )
            room_id = cursor.fetchone()[0]

        for row_name in SEAT_ROWS:
            for number in range(1, SEATS_PER_ROW + 1):
                cursor.execute(
                    "SELECT IdAsiento FROM Asientos WHERE IdSala = ? AND Fila = ? AND Numero = ?",
                    (room_id, row_name, number),
                )
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO Asientos (IdSala, IdTipoAsiento, Fila, Numero, IdEstado) VALUES (?, ?, ?, ?, ?)",
                        (room_id, seat_type_id, row_name, number, state_id),
                    )

        for film_id in films:
            for showtime in SHOWTIMES:
                show_time = time.fromisoformat(showtime)
                cursor.execute(
                    "SELECT IdFuncion FROM Funciones "
                    "WHERE IdPelicula = ? AND IdSala = ? AND CAST(FechaFuncion AS DATE) = ? "
                    "AND Hora = ? AND Formato = ?",
                    (film_id, room_id, today, show_time, "2D"),
                )
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO Funciones (IdPelicula, IdSala, FechaFuncion, Hora, Formato, Precio, IdEstado) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (film_id, room_id, datetime.combine(today, time.min), show_time, "2D", TICKET_PRICE, state_id),
                    )


def seed_catalog():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "IF COL_LENGTH('dbo.Cines', 'Ciudad') IS NULL "
            "ALTER TABLE dbo.Cines ADD Ciudad VARCHAR(100) NULL; "
            "IF COL_LENGTH('dbo.Peliculas', 'Poster') IS NULL "
            "ALTER TABLE dbo.Peliculas ADD Poster VARCHAR(150) NULL; "
            "IF COL_LENGTH('dbo.Funciones', 'Formato') IS NULL "
            "ALTER TABLE dbo.Funciones ADD Formato VARCHAR(20) NOT NULL "
            "CONSTRAINT DF_Funciones_Formato DEFAULT '2D' WITH VALUES;"
        )
        states = {name: get_or_create_state(cursor, name, description) for name, description in STATES}
        state_id = states["Activo"]
        cinemas = add_cinemas(cursor, state_id)
        genres = {
            name: get_or_create_named(cursor, "Generos", name, state_id)
            for name in {film[2] for film in FILMS}
        }
        seat_type_id = get_or_create_named(cursor, "TiposAsiento", "General", state_id)
        for payment_type in PAYMENT_TYPES:
            get_or_create_named(cursor, "TiposPago", payment_type, state_id)

        cursor.execute("SELECT IdCine FROM Cines WHERE Ciudad = ? ORDER BY IdCine", ("Bogotá",))
        home_cinema_id = cursor.fetchone()[0]
        film_ids = []
        for title, poster, genre, duration, rating, release_date in FILMS:
            cursor.execute("SELECT IdPelicula FROM Peliculas WHERE Titulo = ?", (title,))
            row = cursor.fetchone()
            if row:
                film_id = row[0]
                cursor.execute(
                    "UPDATE Peliculas SET Poster = ? WHERE IdPelicula = ? AND Poster IS NULL",
                    (poster, film_id),
                )
            else:
                cursor.execute(
                    "INSERT INTO Peliculas "
                    "(IdGenero, IdCine, Titulo, Poster, Duracion, Clasificacion, FechaEstreno, Descripcion, IdEstado) "
                    "OUTPUT INSERTED.IdPelicula VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (genres[genre], home_cinema_id, title, poster, duration, rating,
                     datetime.strptime(release_date, "%Y-%m-%d"), f"{title} en CineStar", state_id),
                )
                film_id = cursor.fetchone()[0]
            film_ids.append(film_id)

        add_seats_and_shows(cursor, state_id, seat_type_id, cinemas, film_ids)
        conn.commit()
        return len(cinemas), len(film_ids)


if __name__ == "__main__":
    cinema_count, film_count = seed_catalog()
    print(f"Catálogo listo: {film_count} películas, {cinema_count} sedes, "
          f"{cinema_count * len(SEAT_ROWS) * SEATS_PER_ROW} sillas y funciones para hoy.")