-- ============================================================================
-- Caja Clara — Roles y Permisos de Mínimo Privilegio (PostgreSQL / Neon)
-- Tarea 21: Configurar respaldos y accesos
-- Ejecutar conectado como el rol propietario/administrador de Neon (ej. neondb_owner)
-- IMPORTANTE: Reemplazar las contraseñas de ejemplo antes de ejecutar en producción.
-- ============================================================================

-- 1. Rol de solo lectura para BI (Power BI / Looker Studio / equipo de analítica)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'cajaclara_lectura_bi') THEN
        CREATE ROLE cajaclara_lectura_bi LOGIN PASSWORD 'SuperPowerBi.1';
    END IF;
END
$$;

-- 2. Rol de lectura y escritura operativa para la API Django (sin permisos DDL destructivos)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'cajaclara_app_rw') THEN
        CREATE ROLE cajaclara_app_rw LOGIN PASSWORD 'SuperDjango.1';
    END IF;
END
$$;

-- Revocar permisos amplios por defecto en schema public
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO cajaclara_lectura_bi, cajaclara_app_rw;

-- Permisos para BI / Analítica (solo SELECT sobre tablas y futuras vistas)
GRANT SELECT ON ALL TABLES IN SCHEMA public TO cajaclara_lectura_bi;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO cajaclara_lectura_bi;

-- Permisos para Backend Python/Django (SELECT, INSERT, UPDATE sobre tablas operativas; sin TRUNCATE/DROP)
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO cajaclara_app_rw;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO cajaclara_app_rw;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE ON TABLES TO cajaclara_app_rw;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO cajaclara_app_rw;

-- Verificación de privilegios asignados
SELECT grantee, table_name, privilege_type
FROM information_schema.role_table_grants
WHERE table_schema = 'public'
  AND grantee IN ('cajaclara_lectura_bi', 'cajaclara_app_rw')
ORDER BY grantee, table_name, privilege_type;
