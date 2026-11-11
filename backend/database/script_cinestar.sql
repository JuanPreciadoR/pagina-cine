-- ============================================================
-- BASE DE DATOS: CineDB
-- ============================================================

USE master;
GO
IF DB_ID(N'CineDB') IS NOT NULL
BEGIN
    THROW 50000, 'CineDB ya existe. El esquema no se ejecuta sobre una base existente.', 1;
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
    Ciudad VARCHAR(100) NULL,
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

CREATE UNIQUE INDEX UX_Usuarios_Correo
    ON Usuarios(Correo)
    WHERE Correo IS NOT NULL;
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
    Poster VARCHAR(150) NULL,
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
    Formato VARCHAR(20) NOT NULL
        CONSTRAINT DF_Funciones_Formato DEFAULT '2D',
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






