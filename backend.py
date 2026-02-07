from db_driver import PostgreSQLDriver
from models.user import User
from models.tables import Table
from models.booking import Booking
from typing import Optional, List
from datetime import datetime, date, time, timedelta


def apply_migrations():
    """Применяет SQL-миграции для исправления схемы БД."""
    db = PostgreSQLDriver()
    db.connect()
    
    try:
        # Читаем файл миграций
        with open('migrations.sql', 'r', encoding='utf-8') as f:
            migrations = f.read()
        
        # Выполняем миграции
        db.execute_sql(migrations, commit=True)
        
    except FileNotFoundError:
        # Если файл миграций не найден, выполняем миграции напрямую
        # 1.1. Таблица users - удаление user_id, если существует
        db.execute_sql("""
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
        """, commit=True)
        
        # Установка DEFAULT для created_at и updated_at в users
        db.execute_sql("""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'created_at') THEN
                    ALTER TABLE users ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
                END IF;
                IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'updated_at') THEN
                    ALTER TABLE users ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;
                END IF;
            END $$;
        """, commit=True)
        
        # Заполнение NULL значений в users
        db.execute_sql("UPDATE users SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;", commit=True)
        db.execute_sql("UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;", commit=True)
        
        # Таблицы tables и bookings - установка DEFAULT
        for table_name in ['tables', 'bookings']:
            db.execute_sql(f"""
                DO $$
                BEGIN
                    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = '{table_name}' AND column_name = 'created_at') THEN
                        ALTER TABLE {table_name} ALTER COLUMN created_at SET DEFAULT CURRENT_TIMESTAMP;
                    END IF;
                    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = '{table_name}' AND column_name = 'updated_at') THEN
                        ALTER TABLE {table_name} ALTER COLUMN updated_at SET DEFAULT CURRENT_TIMESTAMP;
                    END IF;
                END $$;
            """, commit=True)
            
            db.execute_sql(f"UPDATE {table_name} SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL;", commit=True)
            db.execute_sql(f"UPDATE {table_name} SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL;", commit=True)
        
        # Миграция для bookings.notes - установка DEFAULT '' и заполнение NULL
        db.execute_sql("""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'bookings' AND column_name = 'notes') THEN
                    ALTER TABLE bookings ALTER COLUMN notes SET DEFAULT '';
                END IF;
            END $$;
        """, commit=True)
        
        db.execute_sql("UPDATE bookings SET notes = '' WHERE notes IS NULL;", commit=True)
        
    finally:
        db.disconnect()


def create_tables():
    """Создает таблицы в базе данных, если их нет."""
    db = PostgreSQLDriver()
    db.connect()
    
    try:
        # Создание таблицы users
        query_users = """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            full_name VARCHAR(100),
            phone VARCHAR(20),
            role VARCHAR(20) DEFAULT 'client',
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        db.execute_sql(query_users, commit=True)
        
        # Индексы для users
        db.execute_sql("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);", commit=True)
        db.execute_sql("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);", commit=True)
        
        # Создание таблицы tables
        query_tables = """
        CREATE TABLE IF NOT EXISTS tables (
            id SERIAL PRIMARY KEY,
            table_number VARCHAR(50) UNIQUE NOT NULL,
            capacity INTEGER NOT NULL,
            location VARCHAR(100),
            is_available BOOLEAN DEFAULT TRUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        db.execute_sql(query_tables, commit=True)
        
        # Индексы для tables
        db.execute_sql("CREATE INDEX IF NOT EXISTS idx_tables_table_number ON tables(table_number);", commit=True)
        
        # Создание таблицы bookings
        query_bookings = """
        CREATE TABLE IF NOT EXISTS bookings (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            table_id INTEGER NOT NULL,
            booking_date DATE NOT NULL,
            booking_time TIME NOT NULL,
            guests_count INTEGER NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (table_id) REFERENCES tables(id)
        );
        """
        db.execute_sql(query_bookings, commit=True)
        
        # Установка DEFAULT '' для notes, если таблица уже существовала
        db.execute_sql("""
            DO $$
            BEGIN
                IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'bookings' AND column_name = 'notes') THEN
                    ALTER TABLE bookings ALTER COLUMN notes SET DEFAULT '';
                END IF;
            END $$;
        """, commit=True)
        
        # Индексы для bookings
        db.execute_sql("CREATE INDEX IF NOT EXISTS idx_bookings_user_id ON bookings(user_id);", commit=True)
        db.execute_sql("CREATE INDEX IF NOT EXISTS idx_bookings_table_id ON bookings(table_id);", commit=True)
        db.execute_sql("CREATE INDEX IF NOT EXISTS idx_bookings_status ON bookings(status);", commit=True)
        db.execute_sql("CREATE INDEX IF NOT EXISTS idx_bookings_date ON bookings(booking_date);", commit=True)
        
    finally:
        db.disconnect()


# ==================== USERS CRUD ====================

def create_user(
    username: str,
    email: str,
    full_name: Optional[str] = None,
    phone: Optional[str] = None,
    role: str = "client",
    is_active: bool = True
) -> User:
    """Создает нового пользователя."""
    db = PostgreSQLDriver()
    db.connect()
    
    try:
        query = """
        INSERT INTO users (username, email, full_name, phone, role, is_active)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, created_at, updated_at
        """
        with db.get_cursor(commit=True) as cursor:
            cursor.execute(query, (username, email, full_name, phone, role, is_active))
            result = cursor.fetchone()
            user_id = result['id']
            created_at = result['created_at']
            updated_at = result['updated_at']
        
        return User(
            user_id=user_id,
            username=username,
            email=email,
            full_name=full_name,
            phone=phone,
            role=role,
            is_active=is_active,
            created_at=created_at,
            updated_at=updated_at
        )
    finally:
        db.disconnect()


def get_user_by_id(user_id: int) -> Optional[User]:
    """Получает пользователя по ID."""
    db = PostgreSQLDriver()
    db.connect()
    
    try:
        query = "SELECT * FROM users WHERE id = %s"
        with db.get_cursor() as cursor:
            cursor.execute(query, (user_id,))
            data = cursor.fetchone()
        
        if data:
            return User(
                user_id=data['id'],
                username=data['username'],
                email=data['email'],
                full_name=data.get('full_name'),
                phone=data.get('phone'),
                role=data.get('role', 'client'),
                is_active=data.get('is_active', True),
                created_at=data.get('created_at'),
                updated_at=data.get('updated_at')
            )
        return None
    finally:
        db.disconnect()


def get_user_by_email(email: str) -> Optional[User]:
    """Получает пользователя по email."""
    db = PostgreSQLDriver()
    db.connect()
    
    try:
        query = "SELECT * FROM users WHERE email = %s"
        with db.get_cursor() as cursor:
            cursor.execute(query, (email,))
            data = cursor.fetchone()
        
        if data:
            return User(
                user_id=data['id'],
                username=data['username'],
                email=data['email'],
                full_name=data.get('full_name'),
                phone=data.get('phone'),
                role=data.get('role', 'client'),
                is_active=data.get('is_active', True),
                created_at=data.get('created_at'),
                updated_at=data.get('updated_at')
            )
        return None
    finally:
        db.disconnect()


def get_user_by_username(username: str) -> Optional[User]:
    """Получает пользователя по имени пользователя."""
    db = PostgreSQLDriver()
    db.connect()
    
    try:
        query = "SELECT * FROM users WHERE username = %s"
        with db.get_cursor() as cursor:
            cursor.execute(query, (username,))
            data = cursor.fetchone()
        
        if data:
            return User(
                user_id=data['id'],
                username=data['username'],
                email=data['email'],
                full_name=data.get('full_name'),
                phone=data.get('phone'),
                role=data.get('role', 'client'),
                is_active=data.get('is_active', True),
                created_at=data.get('created_at'),
                updated_at=data.get('updated_at')
            )
        return None
    finally:
        db.disconnect()


def get_all_users(
    active_only: bool = False,
    role: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> List[User]:
    """Получает список всех пользователей."""
    db = PostgreSQLDriver()
    db.connect()
    
    try:
        query = "SELECT * FROM users WHERE 1=1"
        params = []
        
        if active_only:
            query += " AND is_active = %s"
            params.append(True)
        if role:
            query += " AND role = %s"
            params.append(role)
        
        query += " ORDER BY created_at DESC"
        
        if limit:
            query += " LIMIT %s"
            params.append(limit)
        if offset:
            query += " OFFSET %s"
            params.append(offset)
        
        with db.get_cursor() as cursor:
            cursor.execute(query, tuple(params))
            data_list = cursor.fetchall()
        
        users = []
        for data in data_list:
            users.append(User(
                user_id=data['id'],
                username=data['username'],
                email=data['email'],
                full_name=data.get('full_name'),
                phone=data.get('phone'),
                role=data.get('role', 'client'),
                is_active=data.get('is_active', True),
                created_at=data.get('created_at'),
                updated_at=data.get('updated_at')
            ))
        return users
    finally:
        db.disconnect()


def update_user(user_id: int, **kwargs) -> bool:
    """Обновляет данные пользователя."""
    db = PostgreSQLDriver()
    db.connect()
    
    try:
        # Удаляем поля, которые нельзя обновлять
        update_data = {k: v for k, v in kwargs.items() 
                      if k not in ['id', 'created_at', 'updated_at']}
        
        if not update_data:
            return False
        
        update_data['updated_at'] = datetime.now()
        
        set_clause = ', '.join([f"{key} = %s" for key in update_data.keys()])
        query = f"UPDATE users SET {set_clause} WHERE id = %s"
        params = list(update_data.values()) + [user_id]
        
        with db.get_cursor(commit=True) as cursor:
            cursor.execute(query, tuple(params))
            return cursor.rowcount > 0
    finally:
        db.disconnect()


def delete_user(user_id: int) -> bool:
    """Удаляет пользователя."""
    db = PostgreSQLDriver()
    db.connect()
    
    try:
        query = "DELETE FROM users WHERE id = %s"
        with db.get_cursor(commit=True) as cursor:
            cursor.execute(query, (user_id,))
            return cursor.rowcount > 0
    finally:
        db.disconnect()


# ==================== TABLES CRUD ====================

def create_table(
    table_number: str,
    capacity: int,
    location: Optional[str] = None,
    is_available: bool = True,
    description: Optional[str] = None
) -> Table:
    """Создает новый стол."""
    db = PostgreSQLDriver()
    db.connect()
    
    try:
        query = """
        INSERT INTO tables (table_number, capacity, location, is_available, description)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, created_at, updated_at
        """
        with db.get_cursor(commit=True) as cursor:
            cursor.execute(query, (table_number, capacity, location, is_available, description))
            result = cursor.fetchone()
            table_id = result['id']
            created_at = result['created_at']
            updated_at = result['updated_at']
        
        return Table(
            table_id=table_id,
            table_number=table_number,
            capacity=capacity,
            location=location,
            is_available=is_available,
            description=description,
            created_at=created_at,
            updated_at=updated_at
        )
    finally:
        db.disconnect()


def get_table_by_id(table_id: int) -> Optional[Table]:
    """Получает стол по ID."""
    db = PostgreSQLDriver()
    db.connect()
    
    try:
        query = "SELECT * FROM tables WHERE id = %s"
        with db.get_cursor() as cursor:
            cursor.execute(query, (table_id,))
            data = cursor.fetchone()
        
        if data:
            return Table(
                table_id=data['id'],
                table_number=data['table_number'],
                capacity=data['capacity'],
                location=data.get('location'),
                is_available=data.get('is_available', True),
                description=data.get('description'),
                created_at=data.get('created_at'),
                updated_at=data.get('updated_at')
            )
        return None
    finally:
        db.disconnect()


def get_table_by_number(table_number: str) -> Optional[Table]:
    """Получает стол по номеру."""
    db = PostgreSQLDriver()
    db.connect()
    
    try:
        query = "SELECT * FROM tables WHERE table_number = %s"
        with db.get_cursor() as cursor:
            cursor.execute(query, (table_number,))
            data = cursor.fetchone()
        
        if data:
            return Table(
                table_id=data['id'],
                table_number=data['table_number'],
                capacity=data['capacity'],
                location=data.get('location'),
                is_available=data.get('is_available', True),
                description=data.get('description'),
                created_at=data.get('created_at'),
                updated_at=data.get('updated_at')
            )
        return None
    finally:
        db.disconnect()


def get_all_tables(
    available_only: bool = False,
    location: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> List[Table]:
    """Получает список всех столов."""
    db = PostgreSQLDriver()
    db.connect()
    
    try:
        query = "SELECT * FROM tables WHERE 1=1"
        params = []
        
        if available_only:
            query += " AND is_available = %s"
            params.append(True)
        if location:
            query += " AND location = %s"
            params.append(location)
        
        query += " ORDER BY table_number ASC"
        
        if limit:
            query += " LIMIT %s"
            params.append(limit)
        if offset:
            query += " OFFSET %s"
            params.append(offset)
        
        with db.get_cursor() as cursor:
            cursor.execute(query, tuple(params))
            data_list = cursor.fetchall()
        
        tables = []
        for data in data_list:
            tables.append(Table(
                table_id=data['id'],
                table_number=data['table_number'],
                capacity=data['capacity'],
                location=data.get('location'),
                is_available=data.get('is_available', True),
                description=data.get('description'),
                created_at=data.get('created_at'),
                updated_at=data.get('updated_at')
            ))
        return tables
    finally:
        db.disconnect()


def update_table(table_id: int, **kwargs) -> bool:
    """Обновляет данные стола."""
    db = PostgreSQLDriver()
    db.connect()
    
    try:
        update_data = {k: v for k, v in kwargs.items() 
                      if k not in ['id', 'created_at', 'updated_at']}
        
        if not update_data:
            return False
        
        update_data['updated_at'] = datetime.now()
        
        set_clause = ', '.join([f"{key} = %s" for key in update_data.keys()])
        query = f"UPDATE tables SET {set_clause} WHERE id = %s"
        params = list(update_data.values()) + [table_id]
        
        with db.get_cursor(commit=True) as cursor:
            cursor.execute(query, tuple(params))
            return cursor.rowcount > 0
    finally:
        db.disconnect()


def delete_table(table_id: int) -> bool:
    """Удаляет стол."""
    db = PostgreSQLDriver()
    db.connect()
    
    try:
        query = "DELETE FROM tables WHERE id = %s"
        with db.get_cursor(commit=True) as cursor:
            cursor.execute(query, (table_id,))
            return cursor.rowcount > 0
    finally:
        db.disconnect()


# ==================== BOOKINGS CRUD ====================

def check_table_availability(
    table_id: int,
    booking_date: date,
    booking_time: time,
    duration_hours: int = 2
) -> bool:
    """
    Проверяет доступность стола для бронирования.
    
    Бронирование пересекается, если:
    existing.start < new_end AND existing.end > new_start
    """
    db = PostgreSQLDriver()
    db.connect()
    
    try:
        # Проверяем, существует ли стол и доступен ли он
        table = get_table_by_id(table_id)
        if not table:
            raise ValueError(f"Стол с ID {table_id} не найден")
        if not table.is_available:
            raise ValueError(f"Стол {table.table_number} недоступен для бронирования")
        
        # Вычисляем start_datetime и end_datetime
        start_datetime = datetime.combine(booking_date, booking_time)
        end_datetime = start_datetime + timedelta(hours=duration_hours)
        
        # SQL запрос для проверки пересечений
        # Бронирование пересекается, если:
        # existing.start < new_end AND existing.end > new_start
        query = """
        SELECT COUNT(*) as count
        FROM bookings
        WHERE table_id = %s
          AND booking_date = %s
          AND status != 'cancelled'
          AND (
              (booking_date || ' ' || booking_time::text)::timestamp < %s
              AND
              (booking_date || ' ' || booking_time::text)::timestamp + INTERVAL '2 hours' > %s
          )
        """
        
        with db.get_cursor() as cursor:
            cursor.execute(query, (table_id, booking_date, end_datetime, start_datetime))
            result = cursor.fetchone()
            count = result['count'] if result else 0
        
        return count == 0
    finally:
        db.disconnect()


def create_booking(
    user_id: int,
    table_id: int,
    booking_date: date,
    booking_time: time,
    guests_count: int,
    status: str = "pending",
    notes: Optional[str] = None,
    duration_hours: int = 2
) -> Booking:
    """Создает новое бронирование."""
    # Проверяем доступность стола перед созданием
    if not check_table_availability(table_id, booking_date, booking_time, duration_hours):
        table = get_table_by_id(table_id)
        table_number = table.table_number if table else f"ID {table_id}"
        raise ValueError(
            f"Стол {table_number} уже забронирован на {booking_date} в {booking_time}. "
            "Выберите другое время или стол."
        )
    
    # Гарантируем, что notes всегда строка (не None)
    if notes is None:
        notes = ''
    else:
        notes = notes.strip() if isinstance(notes, str) else ''
    
    db = PostgreSQLDriver()
    db.connect()
    
    try:
        query = """
        INSERT INTO bookings (user_id, table_id, booking_date, booking_time, guests_count, status, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id, created_at, updated_at
        """
        with db.get_cursor(commit=True) as cursor:
            cursor.execute(query, (user_id, table_id, booking_date, booking_time, guests_count, status, notes))
            result = cursor.fetchone()
            booking_id = result['id']
            created_at = result['created_at']
            updated_at = result['updated_at']
        
        return Booking(
            booking_id=booking_id,
            user_id=user_id,
            table_id=table_id,
            booking_date=booking_date,
            booking_time=booking_time,
            guests_count=guests_count,
            status=status,
            notes=notes,
            created_at=created_at,
            updated_at=updated_at
        )
    finally:
        db.disconnect()


def get_booking_by_id(booking_id: int) -> Optional[Booking]:
    """Получает бронирование по ID."""
    db = PostgreSQLDriver()
    db.connect()
    
    try:
        query = "SELECT * FROM bookings WHERE id = %s"
        with db.get_cursor() as cursor:
            cursor.execute(query, (booking_id,))
            data = cursor.fetchone()
        
        if data:
            return Booking(
                booking_id=data['id'],
                user_id=data['user_id'],
                table_id=data['table_id'],
                booking_date=data['booking_date'],
                booking_time=data['booking_time'],
                guests_count=data['guests_count'],
                status=data.get('status', 'pending'),
                notes=data.get('notes'),
                created_at=data.get('created_at'),
                updated_at=data.get('updated_at')
            )
        return None
    finally:
        db.disconnect()


def get_bookings_by_user(user_id: int) -> List[Booking]:
    """Получает все бронирования пользователя."""
    db = PostgreSQLDriver()
    db.connect()
    
    try:
        query = """
        SELECT * FROM bookings 
        WHERE user_id = %s 
        ORDER BY booking_date DESC, booking_time DESC
        """
        with db.get_cursor() as cursor:
            cursor.execute(query, (user_id,))
            data_list = cursor.fetchall()
        
        bookings = []
        for data in data_list:
            bookings.append(Booking(
                booking_id=data['id'],
                user_id=data['user_id'],
                table_id=data['table_id'],
                booking_date=data['booking_date'],
                booking_time=data['booking_time'],
                guests_count=data['guests_count'],
                status=data.get('status', 'pending'),
                notes=data.get('notes'),
                created_at=data.get('created_at'),
                updated_at=data.get('updated_at')
            ))
        return bookings
    finally:
        db.disconnect()


def get_bookings_by_table(table_id: int) -> List[Booking]:
    """Получает все бронирования стола."""
    db = PostgreSQLDriver()
    db.connect()
    
    try:
        query = """
        SELECT * FROM bookings 
        WHERE table_id = %s 
        ORDER BY booking_date DESC, booking_time DESC
        """
        with db.get_cursor() as cursor:
            cursor.execute(query, (table_id,))
            data_list = cursor.fetchall()
        
        bookings = []
        for data in data_list:
            bookings.append(Booking(
                booking_id=data['id'],
                user_id=data['user_id'],
                table_id=data['table_id'],
                booking_date=data['booking_date'],
                booking_time=data['booking_time'],
                guests_count=data['guests_count'],
                status=data.get('status', 'pending'),
                notes=data.get('notes'),
                created_at=data.get('created_at'),
                updated_at=data.get('updated_at')
            ))
        return bookings
    finally:
        db.disconnect()


def get_all_bookings(
    status: Optional[str] = None,
    booking_date: Optional[date] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None
) -> List[Booking]:
    """Получает список всех бронирований."""
    db = PostgreSQLDriver()
    db.connect()
    
    try:
        query = "SELECT * FROM bookings WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = %s"
            params.append(status)
        if booking_date:
            query += " AND booking_date = %s"
            params.append(booking_date)
        
        query += " ORDER BY booking_date DESC, booking_time DESC"
        
        if limit:
            query += " LIMIT %s"
            params.append(limit)
        if offset:
            query += " OFFSET %s"
            params.append(offset)
        
        with db.get_cursor() as cursor:
            cursor.execute(query, tuple(params))
            data_list = cursor.fetchall()
        
        bookings = []
        for data in data_list:
            bookings.append(Booking(
                booking_id=data['id'],
                user_id=data['user_id'],
                table_id=data['table_id'],
                booking_date=data['booking_date'],
                booking_time=data['booking_time'],
                guests_count=data['guests_count'],
                status=data.get('status', 'pending'),
                notes=data.get('notes'),
                created_at=data.get('created_at'),
                updated_at=data.get('updated_at')
            ))
        return bookings
    finally:
        db.disconnect()


def update_booking(booking_id: int, **kwargs) -> bool:
    """Обновляет данные бронирования."""
    db = PostgreSQLDriver()
    db.connect()
    
    try:
        update_data = {k: v for k, v in kwargs.items() 
                      if k not in ['id', 'created_at', 'updated_at']}
        
        if not update_data:
            return False
        
        # Гарантируем, что notes всегда строка (не None)
        if 'notes' in update_data:
            if update_data['notes'] is None:
                update_data['notes'] = ''
            else:
                update_data['notes'] = update_data['notes'].strip() if isinstance(update_data['notes'], str) else ''
        
        update_data['updated_at'] = datetime.now()
        
        set_clause = ', '.join([f"{key} = %s" for key in update_data.keys()])
        query = f"UPDATE bookings SET {set_clause} WHERE id = %s"
        params = list(update_data.values()) + [booking_id]
        
        with db.get_cursor(commit=True) as cursor:
            cursor.execute(query, tuple(params))
            return cursor.rowcount > 0
    finally:
        db.disconnect()


def delete_booking(booking_id: int) -> bool:
    """Удаляет бронирование."""
    db = PostgreSQLDriver()
    db.connect()
    
    try:
        query = "DELETE FROM bookings WHERE id = %s"
        with db.get_cursor(commit=True) as cursor:
            cursor.execute(query, (booking_id,))
            return cursor.rowcount > 0
    finally:
        db.disconnect()


if __name__ == "__main__":
    print("▶ backend.py started")
    create_tables()
