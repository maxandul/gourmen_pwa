-- ==============================================================================
-- DETAILLIERTE SPALTEN-PRÜFUNG FÜR ALLE TABELLEN
-- ==============================================================================
-- Kopieren Sie diese Befehle nacheinander in die Railway PostgreSQL-Shell
-- ==============================================================================

-- 1. MEMBERS Tabelle
-- ==============================================================================
\d members

-- 2. MEMBER_SENSITIVE Tabelle
-- ==============================================================================
\d member_sensitive

-- 3. MEMBER_MFA Tabelle
-- ==============================================================================
\d member_mfa

-- 4. MFA_BACKUP_CODES Tabelle
-- ==============================================================================
\d mfa_backup_codes

-- 5. EVENTS Tabelle
-- ==============================================================================
\d events

-- 6. PARTICIPATIONS Tabelle
-- ==============================================================================
\d participations

-- 7. DOCUMENTS Tabelle
-- ==============================================================================
\d documents

-- 8. AUDIT_EVENTS Tabelle
-- ==============================================================================
\d audit_events

-- 9. EVENT_RATINGS Tabelle
-- ==============================================================================
\d event_ratings

-- 10. PUSH_SUBSCRIPTIONS Tabelle
-- ==============================================================================
\d push_subscriptions

-- 11. MERCH_ARTICLES Tabelle (NEU)
-- ==============================================================================
\d merch_articles

-- 12. MERCH_VARIANTS Tabelle (NEU)
-- ==============================================================================
\d merch_variants

-- 13. MERCH_ORDERS Tabelle (NEU)
-- ==============================================================================
\d merch_orders

-- 14. MERCH_ORDER_ITEMS Tabelle (NEU)
-- ==============================================================================
\d merch_order_items

-- ==============================================================================
-- ALTERNATIVE: Kompakte Übersicht aller Spalten
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
  AND table_name IN (
    'members', 'member_sensitive', 'member_mfa', 'mfa_backup_codes',
    'events', 'participations', 'documents', 'audit_events',
    'event_ratings', 'push_subscriptions',
    'merch_articles', 'merch_variants', 'merch_orders', 'merch_order_items'
  )
ORDER BY table_name, ordinal_position;

