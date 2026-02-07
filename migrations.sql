-- ============================================================
-- SQL-миграции для приведения схемы БД в корректное состояние
-- ============================================================

-- 1.1. Таблица users
-- Удаление столбца user_id, если он существует
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'users' 
        AND column_name = 'user_id'
    ) THEN
        ALTER TABLE users DROP COLUMN user_id;
    END IF;
END $$;

-- Убедиться, что created_at имеет DEFAULT CURRENT_TIMESTAMP
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'users' 
        AND column_name = 'created_at'
        AND column_default = 'CURRENT_TIMESTAMP'
    ) THEN
        ALTER TABLE users 
        ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

-- Убедиться, что updated_at имеет DEFAULT CURRENT_TIMESTAMP
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'users' 
        AND column_name = 'updated_at'
        AND column_default = 'CURRENT_TIMESTAMP'
    ) THEN
        ALTER TABLE users 
        ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

-- Заполнить NULL значения в created_at текущим временем
UPDATE users 
SET created_at = CURRENT_TIMESTAMP 
WHERE created_at IS NULL;

-- Заполнить NULL значения в updated_at текущим временем
UPDATE users 
SET updated_at = CURRENT_TIMESTAMP 
WHERE updated_at IS NULL;

-- 1.2. Таблица tables
-- Убедиться, что created_at имеет DEFAULT CURRENT_TIMESTAMP
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'tables' 
        AND column_name = 'created_at'
        AND column_default = 'CURRENT_TIMESTAMP'
    ) THEN
        ALTER TABLE tables 
        ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

-- Убедиться, что updated_at имеет DEFAULT CURRENT_TIMESTAMP
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'tables' 
        AND column_name = 'updated_at'
        AND column_default = 'CURRENT_TIMESTAMP'
    ) THEN
        ALTER TABLE tables 
        ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

-- Заполнить NULL значения в created_at текущим временем
UPDATE tables 
SET created_at = CURRENT_TIMESTAMP 
WHERE created_at IS NULL;

-- Заполнить NULL значения в updated_at текущим временем
UPDATE tables 
SET updated_at = CURRENT_TIMESTAMP 
WHERE updated_at IS NULL;

-- 1.3. Таблица bookings
-- Убедиться, что created_at имеет DEFAULT CURRENT_TIMESTAMP
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'bookings' 
        AND column_name = 'created_at'
        AND column_default = 'CURRENT_TIMESTAMP'
    ) THEN
        ALTER TABLE bookings 
        ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

-- Убедиться, что updated_at имеет DEFAULT CURRENT_TIMESTAMP
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'bookings' 
        AND column_name = 'updated_at'
        AND column_default = 'CURRENT_TIMESTAMP'
    ) THEN
        ALTER TABLE bookings 
        ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;
    END IF;
END $$;

-- Заполнить NULL значения в created_at текущим временем
UPDATE bookings 
SET created_at = CURRENT_TIMESTAMP 
WHERE created_at IS NULL;

-- Заполнить NULL значения в updated_at текущим временем
UPDATE bookings 
SET updated_at = CURRENT_TIMESTAMP 
WHERE updated_at IS NULL;

