-- ============================================================
-- BASE DE DATOS: CineDB
-- ============================================================

USE master;
GO
IF DB_ID(N'CineDB') IS NOT NULL
BEGIN
    ALTER DATABASE CineDB SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CineDB;
END;
GO

CREATE DATABASE CineDB;
GO

ALTER DATABASE CineDB SET RECOVERY SIMPLE;
GO

USE CineDB;
GO


-- ============================================================
-- 1. TABLA: Cines
-- ============================================================

CREATE TABLE Cines
(
    IdCine INT IDENTITY(1,1) NOT NULL,

    Nombre VARCHAR(100) NOT NULL,
    Tipo VARCHAR(50) NOT NULL,
    Documento VARCHAR(30) NOT NULL,
    EsExtranjero BIT NOT NULL,

    Descripcion VARCHAR(250) NULL,
    Observacion VARCHAR(500) NULL,

    Fecha DATETIME NOT NULL
        CONSTRAINT DF_Cines_Fecha DEFAULT GETDATE(),

    IdEstado INT NOT NULL,

    CONSTRAINT PK_Cines
        PRIMARY KEY (IdCine)
);
GO


-- ============================================================
-- 2. TABLA: Generos
-- ============================================================

CREATE TABLE Generos
(
    IdGenero INT IDENTITY(1,1) NOT NULL,

    Nombre VARCHAR(50) NOT NULL,

    Descripcion VARCHAR(250) NULL,
    Observacion VARCHAR(500) NULL,

    Fecha DATETIME NOT NULL
        CONSTRAINT DF_Generos_Fecha DEFAULT GETDATE(),

    IdEstado INT NOT NULL,

    CONSTRAINT PK_Generos
        PRIMARY KEY (IdGenero)
);
GO


-- ============================================================
-- 3. TABLA: TiposAsiento
-- ============================================================

CREATE TABLE TiposAsiento
(
    IdTipoAsiento INT IDENTITY(1,1) NOT NULL,

    Nombre VARCHAR(50) NOT NULL,

    Descripcion VARCHAR(250) NULL,
    Observacion VARCHAR(500) NULL,

    Fecha DATETIME NOT NULL
        CONSTRAINT DF_TiposAsiento_Fecha DEFAULT GETDATE(),

    IdEstado INT NOT NULL,

    CONSTRAINT PK_TiposAsiento
        PRIMARY KEY (IdTipoAsiento)
);
GO


-- ============================================================
-- 4. TABLA: TiposPago
-- ============================================================

CREATE TABLE TiposPago
(
    IdTipoPago INT IDENTITY(1,1) NOT NULL,

    Nombre VARCHAR(50) NOT NULL,

    Descripcion VARCHAR(250) NULL,
    Observacion VARCHAR(500) NULL,

    Fecha DATETIME NOT NULL
        CONSTRAINT DF_TiposPago_Fecha DEFAULT GETDATE(),

    IdEstado INT NOT NULL,

    CONSTRAINT PK_TiposPago
        PRIMARY KEY (IdTipoPago)
);
GO


-- ============================================================
-- 5. TABLA: Roles
-- ============================================================

CREATE TABLE Roles
(
    IdRol INT IDENTITY(1,1) NOT NULL,

    Nombre VARCHAR(50) NOT NULL,

    Descripcion VARCHAR(250) NULL,
    Observacion VARCHAR(500) NULL,

    Fecha DATETIME NOT NULL
        CONSTRAINT DF_Roles_Fecha DEFAULT GETDATE(),

    IdEstado INT NOT NULL,

    CONSTRAINT PK_Roles
        PRIMARY KEY (IdRol)
);
GO


-- ============================================================
-- 6. TABLA: Estados
-- ============================================================

CREATE TABLE Estados
(
    IdEstado INT IDENTITY(1,1) NOT NULL,

    Nombre VARCHAR(50) NOT NULL,
    Descripcion VARCHAR(250) NULL,

    Fecha_Registro DATETIME NOT NULL
        CONSTRAINT DF_Estados_Fecha_Registro DEFAULT GETDATE(),

    CONSTRAINT PK_Estados
        PRIMARY KEY (IdEstado),

    CONSTRAINT UQ_Estados_Nombre
        UNIQUE (Nombre)
);
GO


-- ============================================================
-- 7. TABLA: Usuarios
-- ============================================================

CREATE TABLE Usuarios
(
    IdUsuario INT IDENTITY(1,1) NOT NULL,

    NombreUsuario VARCHAR(50) NOT NULL,
    Clave VARCHAR(255) NOT NULL,
    Correo VARCHAR(100) NULL,

    Descripcion VARCHAR(250) NULL,
    Observacion VARCHAR(500) NULL,

    Fecha DATETIME NOT NULL
        CONSTRAINT DF_Usuarios_Fecha DEFAULT GETDATE(),

    IdEstado INT NOT NULL,

    CONSTRAINT PK_Usuarios
        PRIMARY KEY (IdUsuario),

    CONSTRAINT UQ_Usuarios_NombreUsuario
        UNIQUE (NombreUsuario)
);
GO


-- ============================================================
-- 8. TABLA: Peliculas
-- ============================================================

CREATE TABLE Peliculas
(
    IdPelicula INT IDENTITY(1,1) NOT NULL,

    IdGenero INT NOT NULL,
    IdCine INT NOT NULL,

    Titulo VARCHAR(100) NOT NULL,
    Duracion INT NOT NULL,
    Clasificacion VARCHAR(20) NOT NULL,

    FechaEstreno DATETIME NOT NULL,

    Descripcion VARCHAR(250) NULL,
    Observacion VARCHAR(500) NULL,

    Fecha DATETIME NOT NULL
        CONSTRAINT DF_Peliculas_Fecha DEFAULT GETDATE(),

    IdEstado INT NOT NULL,

    CONSTRAINT PK_Peliculas
        PRIMARY KEY (IdPelicula),

    CONSTRAINT FK_Peliculas_Generos
        FOREIGN KEY (IdGenero)
        REFERENCES Generos(IdGenero),

    CONSTRAINT FK_Peliculas_Cines
        FOREIGN KEY (IdCine)
        REFERENCES Cines(IdCine),

    CONSTRAINT CK_Peliculas_Duracion
        CHECK (Duracion > 0)
);
GO


-- ============================================================
-- 9. TABLA: Salas
-- ============================================================

CREATE TABLE Salas
(
    IdSala INT IDENTITY(1,1) NOT NULL,

    IdCine INT NOT NULL,

    Nombre VARCHAR(50) NOT NULL,
    Capacidad INT NOT NULL,

    Descripcion VARCHAR(250) NULL,
    Observacion VARCHAR(500) NULL,

    Fecha DATETIME NOT NULL
        CONSTRAINT DF_Salas_Fecha DEFAULT GETDATE(),

    IdEstado INT NOT NULL,

    CONSTRAINT PK_Salas
        PRIMARY KEY (IdSala),

    CONSTRAINT FK_Salas_Cines
        FOREIGN KEY (IdCine)
        REFERENCES Cines(IdCine),

    CONSTRAINT CK_Salas_Capacidad
        CHECK (Capacidad > 0)
);
GO


-- ============================================================
-- 10. TABLA: Asientos
-- ============================================================

CREATE TABLE Asientos
(
    IdAsiento INT IDENTITY(1,1) NOT NULL,

    IdSala INT NOT NULL,
    IdTipoAsiento INT NOT NULL,

    Fila VARCHAR(5) NOT NULL,
    Numero INT NOT NULL,

    Descripcion VARCHAR(250) NULL,
    Observacion VARCHAR(500) NULL,

    Fecha DATETIME NOT NULL
        CONSTRAINT DF_Asientos_Fecha DEFAULT GETDATE(),

    IdEstado INT NOT NULL,

    CONSTRAINT PK_Asientos
        PRIMARY KEY (IdAsiento),

    CONSTRAINT FK_Asientos_Salas
        FOREIGN KEY (IdSala)
        REFERENCES Salas(IdSala),

    CONSTRAINT FK_Asientos_TiposAsiento
        FOREIGN KEY (IdTipoAsiento)
        REFERENCES TiposAsiento(IdTipoAsiento),

    CONSTRAINT CK_Asientos_Numero
        CHECK (Numero > 0),

    CONSTRAINT UQ_Asientos_Sala_Fila_Numero
        UNIQUE (IdSala, Fila, Numero)
);
GO


-- ============================================================
-- 11. TABLA: Funciones
-- ============================================================

CREATE TABLE Funciones
(
    IdFuncion INT IDENTITY(1,1) NOT NULL,

    IdPelicula INT NOT NULL,
    IdSala INT NOT NULL,

    FechaFuncion DATETIME NOT NULL,
    Hora TIME NOT NULL,
    Precio DECIMAL(10,2) NOT NULL,

    Descripcion VARCHAR(250) NULL,
    Observacion VARCHAR(500) NULL,

    Fecha DATETIME NOT NULL
        CONSTRAINT DF_Funciones_Fecha DEFAULT GETDATE(),

    IdEstado INT NOT NULL,

    CONSTRAINT PK_Funciones
        PRIMARY KEY (IdFuncion),

    CONSTRAINT FK_Funciones_Peliculas
        FOREIGN KEY (IdPelicula)
        REFERENCES Peliculas(IdPelicula),

    CONSTRAINT FK_Funciones_Salas
        FOREIGN KEY (IdSala)
        REFERENCES Salas(IdSala),

    CONSTRAINT CK_Funciones_Precio
        CHECK (Precio >= 0)
);
GO


-- ============================================================
-- 12. TABLA: Clientes
-- ============================================================

CREATE TABLE Clientes
(
    IdCliente INT IDENTITY(1,1) NOT NULL,

    Tipo VARCHAR(30) NOT NULL,
    Documento VARCHAR(30) NOT NULL,

    Nombre VARCHAR(50) NOT NULL,
    Apellido VARCHAR(50) NOT NULL,

    EsExtranjero BIT NOT NULL,

    Telefono VARCHAR(20) NULL,
    Correo VARCHAR(100) NULL,

    Descripcion VARCHAR(250) NULL,
    Observacion VARCHAR(500) NULL,

    Fecha DATETIME NOT NULL
        CONSTRAINT DF_Clientes_Fecha DEFAULT GETDATE(),

    IdEstado INT NOT NULL,

    CONSTRAINT PK_Clientes
        PRIMARY KEY (IdCliente),

    CONSTRAINT UQ_Clientes_Documento
        UNIQUE (Documento)
);
GO


-- ============================================================
-- 13. TABLA: UsuariosRoles
-- ============================================================

CREATE TABLE UsuariosRoles
(
    IdUsuarioRol INT IDENTITY(1,1) NOT NULL,

    IdUsuario INT NOT NULL,
    IdRol INT NOT NULL,

    Descripcion VARCHAR(250) NULL,
    Observacion VARCHAR(500) NULL,

    Fecha DATETIME NOT NULL
        CONSTRAINT DF_UsuariosRoles_Fecha DEFAULT GETDATE(),

    IdEstado INT NOT NULL,

    CONSTRAINT PK_UsuariosRoles
        PRIMARY KEY (IdUsuarioRol),

    CONSTRAINT FK_UsuariosRoles_Usuarios
        FOREIGN KEY (IdUsuario)
        REFERENCES Usuarios(IdUsuario),

    CONSTRAINT FK_UsuariosRoles_Roles
        FOREIGN KEY (IdRol)
        REFERENCES Roles(IdRol),

    CONSTRAINT UQ_UsuariosRoles
        UNIQUE (IdUsuario, IdRol)
);
GO


-- ============================================================
-- 14. TABLA: Boletas
-- ============================================================

CREATE TABLE Boletas
(
    IdBoleta INT IDENTITY(1,1) NOT NULL,

    IdCliente INT NOT NULL,
    IdFuncion INT NOT NULL,
    IdTipoPago INT NOT NULL,

    FechaCompra DATETIME NOT NULL
        CONSTRAINT DF_Boletas_FechaCompra DEFAULT GETDATE(),

    Cantidad INT NOT NULL,
    Total DECIMAL(10,2) NOT NULL,

    Descripcion VARCHAR(250) NULL,
    Observacion VARCHAR(500) NULL,

    Fecha DATETIME NOT NULL
        CONSTRAINT DF_Boletas_Fecha DEFAULT GETDATE(),

    IdEstado INT NOT NULL,

    CONSTRAINT PK_Boletas
        PRIMARY KEY (IdBoleta),

    CONSTRAINT FK_Boletas_Clientes
        FOREIGN KEY (IdCliente)
        REFERENCES Clientes(IdCliente),

    CONSTRAINT FK_Boletas_Funciones
        FOREIGN KEY (IdFuncion)
        REFERENCES Funciones(IdFuncion),

    CONSTRAINT FK_Boletas_TiposPago
        FOREIGN KEY (IdTipoPago)
        REFERENCES TiposPago(IdTipoPago),

    CONSTRAINT CK_Boletas_Cantidad
        CHECK (Cantidad > 0),

    CONSTRAINT CK_Boletas_Total
        CHECK (Total >= 0)
);
GO


-- ============================================================
-- 15. TABLA: DetallesBoleta
-- ============================================================

CREATE TABLE DetallesBoleta
(
    IdDetalleBoleta INT IDENTITY(1,1) NOT NULL,

    IdBoleta INT NOT NULL,
    IdAsiento INT NOT NULL,

    Precio DECIMAL(10,2) NOT NULL,

    Descripcion VARCHAR(250) NULL,
    Observacion VARCHAR(500) NULL,

    Fecha DATETIME NOT NULL
        CONSTRAINT DF_DetallesBoleta_Fecha DEFAULT GETDATE(),

    IdEstado INT NOT NULL,

    CONSTRAINT PK_DetallesBoleta
        PRIMARY KEY (IdDetalleBoleta),

    CONSTRAINT FK_DetallesBoleta_Boletas
        FOREIGN KEY (IdBoleta)
        REFERENCES Boletas(IdBoleta),

    CONSTRAINT FK_DetallesBoleta_Asientos
        FOREIGN KEY (IdAsiento)
        REFERENCES Asientos(IdAsiento),

    CONSTRAINT CK_DetallesBoleta_Precio
        CHECK (Precio >= 0),

    CONSTRAINT UQ_DetallesBoleta
        UNIQUE (IdBoleta, IdAsiento)
);
GO


-- ============================================================
-- AGREGAR FOREIGN KEYS HACIA ESTADOS
-- ============================================================

ALTER TABLE Cines
ADD CONSTRAINT FK_Cines_Estados
    FOREIGN KEY (IdEstado)
    REFERENCES Estados(IdEstado);
GO

ALTER TABLE Generos
ADD CONSTRAINT FK_Generos_Estados
    FOREIGN KEY (IdEstado)
    REFERENCES Estados(IdEstado);
GO

ALTER TABLE TiposAsiento
ADD CONSTRAINT FK_TiposAsiento_Estados
    FOREIGN KEY (IdEstado)
    REFERENCES Estados(IdEstado);
GO

ALTER TABLE TiposPago
ADD CONSTRAINT FK_TiposPago_Estados
    FOREIGN KEY (IdEstado)
    REFERENCES Estados(IdEstado);
GO

ALTER TABLE Roles
ADD CONSTRAINT FK_Roles_Estados
    FOREIGN KEY (IdEstado)
    REFERENCES Estados(IdEstado);
GO

ALTER TABLE Usuarios
ADD CONSTRAINT FK_Usuarios_Estados
    FOREIGN KEY (IdEstado)
    REFERENCES Estados(IdEstado);
GO

ALTER TABLE Peliculas
ADD CONSTRAINT FK_Peliculas_Estados
    FOREIGN KEY (IdEstado)
    REFERENCES Estados(IdEstado);
GO

ALTER TABLE Salas
ADD CONSTRAINT FK_Salas_Estados
    FOREIGN KEY (IdEstado)
    REFERENCES Estados(IdEstado);
GO

ALTER TABLE Asientos
ADD CONSTRAINT FK_Asientos_Estados
    FOREIGN KEY (IdEstado)
    REFERENCES Estados(IdEstado);
GO

ALTER TABLE Funciones
ADD CONSTRAINT FK_Funciones_Estados
    FOREIGN KEY (IdEstado)
    REFERENCES Estados(IdEstado);
GO

ALTER TABLE Clientes
ADD CONSTRAINT FK_Clientes_Estados
    FOREIGN KEY (IdEstado)
    REFERENCES Estados(IdEstado);
GO

ALTER TABLE UsuariosRoles
ADD CONSTRAINT FK_UsuariosRoles_Estados
    FOREIGN KEY (IdEstado)
    REFERENCES Estados(IdEstado);
GO

ALTER TABLE Boletas
ADD CONSTRAINT FK_Boletas_Estados
    FOREIGN KEY (IdEstado)
    REFERENCES Estados(IdEstado);
GO

ALTER TABLE DetallesBoleta
ADD CONSTRAINT FK_DetallesBoleta_Estados
    FOREIGN KEY (IdEstado)
    REFERENCES Estados(IdEstado);
GO


-- ============================================================
-- INSERTAR ESTADOS
-- ============================================================

INSERT INTO Estados
(Nombre, Descripcion)
VALUES
('Activo', 'Registro activo dentro del sistema'),
('Inactivo', 'Registro inactivo dentro del sistema'),
('Suspendido', 'Registro suspendido temporalmente'),
('Pendiente', 'Registro pendiente de procesamiento');
GO


-- ============================================================
-- 1. CINES
-- ============================================================

INSERT INTO Cines
(
    Nombre,
    Tipo,
    Documento,
    EsExtranjero,
    Descripcion,
    Observacion,
    IdEstado
)
VALUES
('Cine Colombia Andino', 'Nacional', '900123456-1', 0,
 'Complejo de cine ubicado en Bogotá', 'Sede principal', 1),

('Cine Colombia Gran Estación', 'Nacional', '900123457-2', 0,
 'Complejo de cine en Bogotá', NULL, 1),

('Cinemark Plaza Imperial', 'Nacional', '900123458-3', 0,
 'Cine con múltiples salas', NULL, 1),

('Royal Films Unicentro', 'Nacional', '900123459-4', 0,
 'Complejo cinematográfico', NULL, 1),

('Cinepolis Centro Mayor', 'Internacional', '900123460-5', 0,
 'Complejo de cine moderno', NULL, 1),

('Cinemark Chile', 'Internacional', '76123456-7', 1,
 'Cine internacional', 'Sucursal extranjera', 1),

('Cineplanet Lima', 'Internacional', '20123456789', 1,
 'Complejo cinematográfico peruano', NULL, 1),

('Cinemex México', 'Internacional', 'MX123456789', 1,
 'Complejo cinematográfico mexicano', NULL, 1);
GO


-- ============================================================
-- 2. GENEROS
-- ============================================================

INSERT INTO Generos
(
    Nombre,
    Descripcion,
    Observacion,
    IdEstado
)
VALUES
('Acción', 'Películas con escenas de combate y aventura', NULL, 1),
('Comedia', 'Películas orientadas al humor', NULL, 1),
('Drama', 'Historias dramáticas y emocionales', NULL, 1),
('Terror', 'Películas de terror y suspenso', NULL, 1),
('Ciencia Ficción', 'Historias relacionadas con ciencia y tecnología', NULL, 1),
('Animación', 'Películas realizadas mediante técnicas de animación', NULL, 1),
('Romance', 'Historias centradas en relaciones amorosas', NULL, 1),
('Aventura', 'Historias de exploración y aventura', NULL, 1),
('Suspenso', 'Historias de tensión y misterio', NULL, 1),
('Fantasía', 'Historias con elementos fantásticos', NULL, 1);
GO


-- ============================================================
-- 3. TIPOS DE ASIENTO
-- ============================================================

INSERT INTO TiposAsiento
(
    Nombre,
    Descripcion,
    Observacion,
    IdEstado
)
VALUES
('General', 'Asiento estándar', NULL, 1),
('VIP', 'Asiento con mayor comodidad', NULL, 1),
('Premium', 'Asiento premium reclinable', NULL, 1),
('Discapacitados', 'Espacio adaptado para personas con movilidad reducida', NULL, 1),
('Pareja', 'Asiento doble para dos personas', NULL, 1);
GO


-- ============================================================
-- 4. TIPOS DE PAGO
-- ============================================================

INSERT INTO TiposPago
(
    Nombre,
    Descripcion,
    Observacion,
    IdEstado
)
VALUES
('Efectivo', 'Pago en efectivo', NULL, 1),
('Tarjeta Crédito', 'Pago mediante tarjeta de crédito', NULL, 1),
('Tarjeta Débito', 'Pago mediante tarjeta débito', NULL, 1),
('PSE', 'Pago electrónico mediante PSE', NULL, 1),
('Nequi', 'Pago mediante billetera digital', NULL, 1),
('Daviplata', 'Pago mediante billetera digital', NULL, 1);
GO


-- ============================================================
-- 5. ROLES
-- ============================================================

INSERT INTO Roles
(
    Nombre,
    Descripcion,
    Observacion,
    IdEstado
)
VALUES
('Administrador', 'Acceso completo al sistema', NULL, 1),
('Gerente', 'Gestión general del cine', NULL, 1),
('Empleado', 'Operaciones generales', NULL, 1),
('Cajero', 'Venta de boletas y manejo de caja', NULL, 1),
('Supervisor', 'Supervisión de operaciones', NULL, 1);
GO


-- ============================================================
-- 6. USUARIOS
-- ============================================================

INSERT INTO Usuarios
(
    NombreUsuario,
    Clave,
    Correo,
    Descripcion,
    Observacion,
    IdEstado
)
VALUES
('admin', 'Admin123', 'admin@cinedb.com',
 'Administrador principal', NULL, 1),

('gerente', 'Gerente123', 'gerente@cinedb.com',
 'Gerente del cine', NULL, 1),

('empleado01', 'Empleado123', 'empleado01@cinedb.com',
 'Empleado de cine', NULL, 1),

('cajero01', 'Cajero123', 'cajero01@cinedb.com',
 'Cajero principal', NULL, 1),

('cajero02', 'Cajero456', 'cajero02@cinedb.com',
 'Cajero auxiliar', NULL, 1),

('supervisor01', 'Supervisor123', 'supervisor@cinedb.com',
 'Supervisor de operaciones', NULL, 1);
GO


-- ============================================================
-- 7. PELICULAS
-- ============================================================

INSERT INTO Peliculas
(
    IdGenero,
    IdCine,
    Titulo,
    Duracion,
    Clasificacion,
    FechaEstreno,
    Descripcion,
    Observacion,
    IdEstado
)
VALUES
(1, 1, 'Misión Extrema', 135, 'PG-13',
 '20260115', 'Película de acción y espionaje', NULL, 1),

(2, 1, 'Una Noche de Locos', 110, 'PG-13',
 '20260210', 'Comedia sobre un grupo de amigos', NULL, 1),

(3, 2, 'El Último Recuerdo', 125, 'PG-13',
 '20260125', 'Drama familiar', NULL, 1),

(4, 2, 'La Casa Oscura', 105, '18+',
 '20260220', 'Historia de terror sobrenatural', NULL, 1),

(5, 3, 'Horizonte Galáctico', 145, 'PG-13',
 '20260305', 'Aventura espacial de ciencia ficción', NULL, 1),

(6, 3, 'El Mundo de Luna', 95, 'G',
 '20260312', 'Película animada para toda la familia', NULL, 1),

(7, 4, 'Cartas de Amor', 118, 'PG',
 '20260214', 'Historia romántica', NULL, 1),

(8, 4, 'La Isla Perdida', 130, 'PG-13',
 '20260301', 'Aventura en una isla misteriosa', NULL, 1),

(9, 5, 'Código Secreto', 120, 'PG-13',
 '20260310', 'Thriller de investigación', NULL, 1),

(10, 5, 'Reino Mágico', 140, 'PG',
 '20260315', 'Aventura fantástica', NULL, 1);
GO


-- ============================================================
-- 8. SALAS
-- ============================================================

INSERT INTO Salas
(
    IdCine,
    Nombre,
    Capacidad,
    Descripcion,
    Observacion,
    IdEstado
)
VALUES
(1, 'Sala 1', 100, 'Sala tradicional', NULL, 1),
(1, 'Sala 2', 80, 'Sala tradicional', NULL, 1),
(1, 'Sala VIP', 50, 'Sala VIP con sillas reclinables', NULL, 1),
(2, 'Sala 1', 120, 'Sala de gran capacidad', NULL, 1),
(2, 'Sala 2', 90, 'Sala tradicional', NULL, 1),
(3, 'Sala 1', 100, 'Sala tradicional', NULL, 1),
(3, 'Sala 3D', 80, 'Sala con proyección 3D', NULL, 1),
(4, 'Sala Premium', 60, 'Sala premium', NULL, 1),
(5, 'Sala IMAX', 150, 'Sala de formato IMAX', NULL, 1);
GO


-- ============================================================
-- 9. ASIENTOS
-- ============================================================

INSERT INTO Asientos
(
    IdSala,
    IdTipoAsiento,
    Fila,
    Numero,
    Descripcion,
    Observacion,
    IdEstado
)
VALUES

-- Sala 1
(1, 1, 'A', 1, 'Asiento general', NULL, 1),
(1, 1, 'A', 2, 'Asiento general', NULL, 1),
(1, 1, 'A', 3, 'Asiento general', NULL, 1),
(1, 1, 'A', 4, 'Asiento general', NULL, 1),
(1, 1, 'A', 5, 'Asiento general', NULL, 1),

(1, 1, 'B', 1, 'Asiento general', NULL, 1),
(1, 1, 'B', 2, 'Asiento general', NULL, 1),
(1, 1, 'B', 3, 'Asiento general', NULL, 1),
(1, 1, 'B', 4, 'Asiento general', NULL, 1),
(1, 1, 'B', 5, 'Asiento general', NULL, 1),

(1, 2, 'C', 1, 'Asiento VIP', NULL, 1),
(1, 2, 'C', 2, 'Asiento VIP', NULL, 1),
(1, 2, 'C', 3, 'Asiento VIP', NULL, 1),
(1, 2, 'C', 4, 'Asiento VIP', NULL, 1),
(1, 2, 'C', 5, 'Asiento VIP', NULL, 1),

-- Sala 2
(2, 1, 'A', 1, 'Asiento general', NULL, 1),
(2, 1, 'A', 2, 'Asiento general', NULL, 1),
(2, 1, 'A', 3, 'Asiento general', NULL, 1),
(2, 1, 'A', 4, 'Asiento general', NULL, 1),
(2, 1, 'A', 5, 'Asiento general', NULL, 1),

(2, 3, 'B', 1, 'Asiento premium', NULL, 1),
(2, 3, 'B', 2, 'Asiento premium', NULL, 1),
(2, 3, 'B', 3, 'Asiento premium', NULL, 1),
(2, 3, 'B', 4, 'Asiento premium', NULL, 1),
(2, 3, 'B', 5, 'Asiento premium', NULL, 1),

-- Sala VIP
(3, 2, 'A', 1, 'Asiento VIP', NULL, 1),
(3, 2, 'A', 2, 'Asiento VIP', NULL, 1),
(3, 2, 'A', 3, 'Asiento VIP', NULL, 1),
(3, 2, 'A', 4, 'Asiento VIP', NULL, 1),
(3, 2, 'A', 5, 'Asiento VIP', NULL, 1),

-- Sala 4
(4, 1, 'A', 1, 'Asiento general', NULL, 1),
(4, 1, 'A', 2, 'Asiento general', NULL, 1),
(4, 1, 'A', 3, 'Asiento general', NULL, 1),
(4, 1, 'A', 4, 'Asiento general', NULL, 1),
(4, 1, 'A', 5, 'Asiento general', NULL, 1),

-- Sala 5
(5, 1, 'A', 1, 'Asiento general', NULL, 1),
(5, 1, 'A', 2, 'Asiento general', NULL, 1),
(5, 1, 'A', 3, 'Asiento general', NULL, 1),
(5, 1, 'A', 4, 'Asiento general', NULL, 1),
(5, 1, 'A', 5, 'Asiento general', NULL, 1);
GO


-- ============================================================
-- 10. FUNCIONES
-- ============================================================

INSERT INTO Funciones
(
    IdPelicula,
    IdSala,
    FechaFuncion,
    Hora,
    Precio,
    Descripcion,
    Observacion,
    IdEstado
)
VALUES
(1, 1, '20260922', '14:00', 18000,
 'Función de Misión Extrema', NULL, 1),

(1, 1, '20260922', '18:00', 22000,
 'Función de Misión Extrema', NULL, 1),

(1, 3, '20260922', '20:30', 30000,
 'Función VIP', NULL, 1),

(2, 1, '20260922', '16:00', 18000,
 'Función de comedia', NULL, 1),

(3, 4, '20260922', '15:00', 19000,
 'Función de drama', NULL, 1),

(4, 5, '20260922', '21:00', 22000,
 'Función de terror', NULL, 1),

(5, 6, '20260923', '17:00', 24000,
 'Función de ciencia ficción', NULL, 1),

(6, 7, '20260923', '13:00', 18000,
 'Función infantil', NULL, 1),

(7, 8, '20260923', '19:00', 28000,
 'Función romántica', NULL, 1),

(8, 9, '20260923', '20:00', 35000,
 'Función IMAX', NULL, 1);
GO


-- ============================================================
-- 11. CLIENTES
-- ============================================================

INSERT INTO Clientes
(
    Tipo,
    Documento,
    Nombre,
    Apellido,
    EsExtranjero,
    Telefono,
    Correo,
    Descripcion,
    Observacion,
    IdEstado
)
VALUES
('CC', '1001001001', 'Carlos', 'Rodríguez', 0,
 '3001234567', 'carlos@email.com',
 'Cliente frecuente', NULL, 1),

('CC', '1001001002', 'María', 'Gómez', 0,
 '3012345678', 'maria@email.com',
 NULL, NULL, 1),

('CC', '1001001003', 'Juan', 'Martínez', 0,
 '3023456789', 'juan@email.com',
 NULL, NULL, 1),

('CC', '1001001004', 'Laura', 'Hernández', 0,
 '3034567890', 'laura@email.com',
 NULL, NULL, 1),

('CC', '1001001005', 'Andrés', 'López', 0,
 '3045678901', 'andres@email.com',
 NULL, NULL, 1),

('CE', 'AB123456', 'Michael', 'Smith', 1,
 '3056789012', 'michael@email.com',
 'Cliente extranjero', NULL, 1),

('CE', 'CD234567', 'Sofia', 'Rossi', 1,
 '3067890123', 'sofia@email.com',
 'Cliente extranjera', NULL, 1),

('CC', '1001001006', 'Daniela', 'Torres', 0,
 '3078901234', 'daniela@email.com',
 NULL, NULL, 1),

('CC', '1001001007', 'Sebastián', 'Ramírez', 0,
 '3089012345', 'sebastian@email.com',
 NULL, NULL, 1),

('CC', '1001001008', 'Valentina', 'Castro', 0,
 '3090123456', 'valentina@email.com',
 NULL, NULL, 1);
GO


-- ============================================================
-- 12. USUARIOS ROLES
-- ============================================================

INSERT INTO UsuariosRoles
(
    IdUsuario,
    IdRol,
    Descripcion,
    Observacion,
    IdEstado
)
VALUES
(1, 1, 'Administrador del sistema', NULL, 1),
(2, 2, 'Gerente general', NULL, 1),
(3, 3, 'Empleado operativo', NULL, 1),
(4, 4, 'Cajero principal', NULL, 1),
(5, 4, 'Cajero auxiliar', NULL, 1),
(6, 5, 'Supervisor de operaciones', NULL, 1);
GO


-- ============================================================
-- 13. BOLETAS
-- ============================================================

INSERT INTO Boletas
(
    IdCliente,
    IdFuncion,
    IdTipoPago,
    FechaCompra,
    Cantidad,
    Total,
    Descripcion,
    Observacion,
    IdEstado
)
VALUES
(1, 1, 2, '2026-09-21T10:00:00',
 2, 36000, 'Compra de dos boletas', NULL, 1),

(2, 2, 3, '2026-09-21T10:15:00',
 1, 22000, 'Compra individual', NULL, 1),

(3, 3, 1, '2026-09-21T10:30:00',
 2, 60000, 'Compra de dos boletas VIP', NULL, 1),

(4, 4, 4, '2026-09-21T11:00:00',
 3, 54000, 'Compra grupal', NULL, 1),

(5, 5, 2, '2026-09-21T11:20:00',
 2, 38000, 'Compra de dos boletas', NULL, 1),

(6, 6, 5, '2026-09-21T11:30:00',
 1, 22000, 'Compra individual', NULL, 1),

(7, 7, 3, '2026-09-21T12:00:00',
 2, 48000, 'Compra de dos boletas', NULL, 1),

(8, 8, 6, '2026-09-21T12:30:00',
 3, 54000, 'Compra familiar', NULL, 1),

(9, 9, 2, '2026-09-21T13:00:00',
 2, 56000, 'Compra de dos boletas', NULL, 1),

(10, 10, 1, '2026-09-21T13:30:00',
 1, 35000, 'Compra individual IMAX', NULL, 1);
GO


-- ============================================================
-- 14. DETALLES DE BOLETA
-- ============================================================

INSERT INTO DetallesBoleta
(
    IdBoleta,
    IdAsiento,
    Precio,
    Descripcion,
    Observacion,
    IdEstado
)
VALUES
(1, 1, 18000, 'Asiento A1', NULL, 1),
(1, 2, 18000, 'Asiento A2', NULL, 1),

(2, 3, 22000, 'Asiento A3', NULL, 1),

(3, 26, 30000, 'Asiento VIP A1', NULL, 1),
(3, 27, 30000, 'Asiento VIP A2', NULL, 1),

(4, 16, 18000, 'Asiento A1', NULL, 1),
(4, 17, 18000, 'Asiento A2', NULL, 1),
(4, 18, 18000, 'Asiento A3', NULL, 1),

(5, 31, 19000, 'Asiento A1', NULL, 1),
(5, 32, 19000, 'Asiento A2', NULL, 1),

(6, 36, 22000, 'Asiento A1', NULL, 1),

(7, 21, 24000, 'Asiento B1', NULL, 1),
(7, 22, 24000, 'Asiento B2', NULL, 1),

(8, 31, 18000, 'Asiento A1', NULL, 1),
(8, 32, 18000, 'Asiento A2', NULL, 1),
(8, 33, 18000, 'Asiento A3', NULL, 1),

(9, 34, 28000, 'Asiento A4', NULL, 1),
(9, 35, 28000, 'Asiento A5', NULL, 1),

(10, 36, 35000, 'Asiento A1', NULL, 1);
GO



/* =====================================================================
   SEMANA 7 - VALIDACIONES DE INTEGRIDAD
   ===================================================================== */

ALTER TABLE dbo.Cines
ADD CONSTRAINT CK_Cines_Nombre_NoVacio
CHECK (LEN(LTRIM(RTRIM(Nombre))) > 0);
GO

ALTER TABLE dbo.Generos
ADD CONSTRAINT CK_Generos_Nombre_NoVacio
CHECK (LEN(LTRIM(RTRIM(Nombre))) > 0);
GO

ALTER TABLE dbo.Usuarios
ADD CONSTRAINT CK_Usuarios_NombreUsuario_NoVacio
CHECK (LEN(LTRIM(RTRIM(NombreUsuario))) > 0);
GO

ALTER TABLE dbo.Clientes
ADD CONSTRAINT CK_Clientes_Documento_NoVacio
CHECK (LEN(LTRIM(RTRIM(Documento))) > 0);
GO

/* Resumen de restricciones de la base de datos */
SELECT
    t.name AS Tabla,
    kc.name AS Restriccion,
    kc.type_desc AS Tipo
FROM sys.key_constraints kc
INNER JOIN sys.tables t ON t.object_id = kc.parent_object_id
ORDER BY t.name, kc.name;
GO

SELECT
    OBJECT_NAME(parent_object_id) AS Tabla,
    name AS Restriccion,
    definition AS Regla
FROM sys.check_constraints
ORDER BY OBJECT_NAME(parent_object_id), name;
GO

/* Validación referencial: debe devolver cero filas para cada consulta.
   WITH CHECK CHECK fuerza la comprobación de las FK existentes. */
DBCC CHECKCONSTRAINTS WITH ALL_CONSTRAINTS;
GO

/* Comprobación estructural y de asignación de páginas */
DBCC CHECKDB (N'CineDB') WITH NO_INFOMSGS;
GO


/* =====================================================================
   SEMANAS 8 Y 9 - SEGURIDAD DE SQL SERVER
   REQUISITO: CUATRO CUENTAS
       1. Super Admin (sysadmin del servidor)
       2. Propietario de CineDB (db_owner)
       3. Solo miembro del rol db_datareader
       4. Solo miembro del rol db_datawriter

   Las contraseñas son académicas/de laboratorio. Cámbialas antes de
   cualquier uso real. Ejecutar conectado con permisos de administrador.
   ===================================================================== */

USE master;
GO

/* 1. SUPER ADMIN */
IF SUSER_ID(N'CineDB_SuperAdmin') IS NULL
BEGIN
    CREATE LOGIN CineDB_SuperAdmin
    WITH PASSWORD = 'NU#$har3p0in7',
         CHECK_POLICY = ON,
         CHECK_EXPIRATION = OFF;
END
ELSE
BEGIN
    ALTER LOGIN CineDB_SuperAdmin
    WITH PASSWORD = 'NU#$har3p0in7',
         CHECK_POLICY = ON,
         CHECK_EXPIRATION = OFF;
END;
GO

IF NOT EXISTS
(
    SELECT 1
    FROM sys.server_role_members rm
    INNER JOIN sys.server_principals rolep
        ON rm.role_principal_id = rolep.principal_id
    INNER JOIN sys.server_principals memberp
        ON rm.member_principal_id = memberp.principal_id
    WHERE rolep.name = N'sysadmin'
      AND memberp.name = N'CineDB_SuperAdmin'
)
    ALTER SERVER ROLE sysadmin ADD MEMBER CineDB_SuperAdmin;
GO

/* 2. LOGIN PARA EL PROPIETARIO DE LA BASE */
IF SUSER_ID(N'CineDB_Owner') IS NULL
BEGIN
    CREATE LOGIN CineDB_Owner
    WITH PASSWORD = 'NU#$har3p0in71',
         CHECK_POLICY = ON,
         CHECK_EXPIRATION = OFF;
END
ELSE
BEGIN
    ALTER LOGIN CineDB_Owner
    WITH PASSWORD = 'NU#$har3p0in71',
         CHECK_POLICY = ON,
         CHECK_EXPIRATION = OFF;
END;
GO

/* 3. LOGIN PARA DATAREADER */
IF SUSER_ID(N'CineDB_Reader') IS NULL
BEGIN
    CREATE LOGIN CineDB_Reader
    WITH PASSWORD = 'NU#$har3p0in72',
         CHECK_POLICY = ON,
         CHECK_EXPIRATION = OFF;
END
ELSE
BEGIN
    ALTER LOGIN CineDB_Reader
    WITH PASSWORD = 'NU#$har3p0in72',
         CHECK_POLICY = ON,
         CHECK_EXPIRATION = OFF;
END;
GO

/* 4. LOGIN PARA DATAWRITER */
IF SUSER_ID(N'CineDB_Writer') IS NULL
BEGIN
    CREATE LOGIN CineDB_Writer
    WITH PASSWORD = 'NU#$har3p0in73',
         CHECK_POLICY = ON,
         CHECK_EXPIRATION = OFF;
END
ELSE
BEGIN
    ALTER LOGIN CineDB_Writer
    WITH PASSWORD = 'NU#$har3p0in73',
         CHECK_POLICY = ON,
         CHECK_EXPIRATION = OFF;
END;
GO

USE CineDB;
GO

/* Crear usuarios de base de datos vinculados a los logins */
IF DATABASE_PRINCIPAL_ID(N'CineDB_SuperAdmin') IS NULL
    CREATE USER CineDB_SuperAdmin FOR LOGIN CineDB_SuperAdmin;
GO

IF DATABASE_PRINCIPAL_ID(N'CineDB_Owner') IS NULL
    CREATE USER CineDB_Owner FOR LOGIN CineDB_Owner;
GO

IF DATABASE_PRINCIPAL_ID(N'CineDB_Reader') IS NULL
    CREATE USER CineDB_Reader FOR LOGIN CineDB_Reader;
GO

IF DATABASE_PRINCIPAL_ID(N'CineDB_Writer') IS NULL
    CREATE USER CineDB_Writer FOR LOGIN CineDB_Writer;
GO

/* Asignar exactamente el rol solicitado a cada usuario de base de datos. */
ALTER ROLE db_owner ADD MEMBER CineDB_Owner;
GO

ALTER ROLE db_datareader ADD MEMBER CineDB_Reader;
GO

ALTER ROLE db_datawriter ADD MEMBER CineDB_Writer;
GO

/* Confirmación visual de usuarios y roles de base de datos */
SELECT
    memberp.name AS Usuario,
    rolep.name AS RolBD
FROM sys.database_role_members rm
INNER JOIN sys.database_principals rolep
    ON rm.role_principal_id = rolep.principal_id
INNER JOIN sys.database_principals memberp
    ON rm.member_principal_id = memberp.principal_id
WHERE memberp.name IN
(
    N'CineDB_SuperAdmin',
    N'CineDB_Owner',
    N'CineDB_Reader',
    N'CineDB_Writer'
)
ORDER BY memberp.name, rolep.name;
GO

/* Comprobar autenticación SQL y política de contraseña */
USE master;
GO
SELECT
    name AS LoginSQL,
    is_disabled AS Deshabilitado,
    is_policy_checked AS PoliticaContraseña,
    is_expiration_checked AS ExpiracionContraseña
FROM sys.sql_logins
WHERE name IN
(
    N'CineDB_SuperAdmin',
    N'CineDB_Owner',
    N'CineDB_Reader',
    N'CineDB_Writer'
)
ORDER BY name;
GO

/* =====================================================================
   PRUEBAS DE PERMISOS
   ===================================================================== */

USE CineDB;
GO

EXECUTE AS USER = N'CineDB_Reader';
SELECT
    USER_NAME() AS UsuarioProbado,
    HAS_PERMS_BY_NAME(N'dbo.Peliculas', N'OBJECT', N'SELECT') AS PuedeLeerPeliculas,
    HAS_PERMS_BY_NAME(N'dbo.Peliculas', N'OBJECT', N'INSERT') AS PuedeInsertarPeliculas,
    HAS_PERMS_BY_NAME(N'dbo.Peliculas', N'OBJECT', N'UPDATE') AS PuedeActualizarPeliculas,
    HAS_PERMS_BY_NAME(N'dbo.Peliculas', N'OBJECT', N'DELETE') AS PuedeEliminarPeliculas;
REVERT;
GO

EXECUTE AS USER = N'CineDB_Writer';
SELECT
    USER_NAME() AS UsuarioProbado,
    HAS_PERMS_BY_NAME(N'dbo.Peliculas', N'OBJECT', N'SELECT') AS PuedeLeerPeliculas,
    HAS_PERMS_BY_NAME(N'dbo.Peliculas', N'OBJECT', N'INSERT') AS PuedeInsertarPeliculas,
    HAS_PERMS_BY_NAME(N'dbo.Peliculas', N'OBJECT', N'UPDATE') AS PuedeActualizarPeliculas,
    HAS_PERMS_BY_NAME(N'dbo.Peliculas', N'OBJECT', N'DELETE') AS PuedeEliminarPeliculas;
REVERT;
GO


/* =====================================================================
   SEMANAS 10 Y 11 - DISPONIBILIDAD, BACKUP Y RESTORE
   ===================================================================== */

USE master;
GO

-- ==========================================
-- BACKUP COMPLETO DE CineDB
-- ==========================================

BACKUP DATABASE [CineDB]
TO DISK = N'C:\DATOS\BACKUP\CineDB_Full.bak'
WITH
    INIT,
    COMPRESSION,
    CHECKSUM,
    STATS = 10;
GO

-- ==========================================
-- VERIFICAR EL ARCHIVO DE BACKUP
-- ==========================================

RESTORE VERIFYONLY
FROM DISK = N'C:\DATOS\BACKUP\CineDB_Full.bak'
WITH CHECKSUM;
GO


