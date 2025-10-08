-- Kompakte Tabellen-Übersicht
SELECT table_name, (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = t.table_name) as columns FROM information_schema.tables t WHERE table_schema = 'public' ORDER BY table_name;

