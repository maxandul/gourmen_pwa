-- Prüfe ob push_subscriptions Tabelle existiert
SELECT table_name 
FROM information_schema.tables 
WHERE table_name = 'push_subscriptions';

-- Falls sie existiert, zeige Struktur
\d push_subscriptions;

-- Falls sie nicht existiert, erstelle sie:
-- (Führe dann create_push_subscriptions_table.sql aus)
