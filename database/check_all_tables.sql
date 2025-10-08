-- ==============================================================================
-- Vollständige Datenbank-Überprüfung für Railway PostgreSQL
-- ==============================================================================

-- 1. Liste aller Tabellen mit Anzahl Zeilen und Spalten
-- ==============================================================================
SELECT 
    t.table_name,
    (SELECT COUNT(*) 
     FROM information_schema.columns 
     WHERE table_name = t.table_name) as column_count,
    pg_class.reltuples::bigint AS row_count
FROM information_schema.tables t
LEFT JOIN pg_class ON pg_class.relname = t.table_name
WHERE t.table_schema = 'public'
ORDER BY t.table_name;

-- 2. Detaillierte Spalten-Information für alle Tabellen
-- ==============================================================================
SELECT 
    table_name,
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
ORDER BY table_name, ordinal_position;

-- 3. Alle Foreign Key Constraints
-- ==============================================================================
SELECT
    tc.table_name, 
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    rc.delete_rule
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
JOIN information_schema.referential_constraints AS rc
    ON rc.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
ORDER BY tc.table_name, kcu.column_name;

-- 4. Alle Indizes
-- ==============================================================================
SELECT
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

