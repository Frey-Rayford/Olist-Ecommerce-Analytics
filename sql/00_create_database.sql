/*
Purpose: Create the project database and staging schema.
Target: SQL Server 2019
Run this file first while connected to the local SQL Server instance.
*/

USE master;
GO

IF DB_ID(N'olist_analytics') IS NULL
BEGIN
    CREATE DATABASE olist_analytics;
END;
GO

USE olist_analytics;
GO

IF SCHEMA_ID(N'stg') IS NULL
BEGIN
    EXEC(N'CREATE SCHEMA stg AUTHORIZATION dbo;');
END;
GO

