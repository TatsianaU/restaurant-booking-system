"""
Модуль-драйвер для работы с PostgreSQL
Используется для подключения и выполнения CRUD-операций с базой данных
"""
import psycopg2
import psycopg2.extras
import os
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Tuple
from dotenv import load_dotenv


class PostgreSQLDriver:
    """
    Драйвер для работы с PostgreSQL базой данных.
    Поддерживает CRUD-операции и управление транзакциями.
    """
    
    def __init__(self, env_file: Optional[str] = None):
        """
        Инициализация драйвера.
        
        Args:
            env_file: Путь к файлу .env (по умолчанию используется .env в текущей директории)
        """
        # Пытаемся загрузить .env с указанием кодировки (поддерживается в python-dotenv >= 0.19.0)
        try:
            load_dotenv(env_file, encoding='utf-8')
        except TypeError:
            # Если параметр encoding не поддерживается, загружаем без него
            load_dotenv(env_file)
        
        def safe_decode(value: Optional[str]) -> str:
            """Безопасно декодирует строку в UTF-8."""
            if value is None:
                return ''
            if isinstance(value, bytes):
                try:
                    return value.decode('utf-8')
                except UnicodeDecodeError:
                    # Заменяем невалидные символы
                    return value.decode('utf-8', errors='replace')
            # Убеждаемся, что строка правильно закодирована
            try:
                if isinstance(value, str):
                    # Проверяем, что строка валидна в UTF-8
                    value.encode('utf-8').decode('utf-8')
                return str(value)
            except (UnicodeEncodeError, UnicodeDecodeError):
                # Если есть проблемы, пытаемся исправить
                return str(value).encode('utf-8', errors='replace').decode('utf-8', errors='replace')
        
        port = os.getenv('DB_PORT')
        self.connection_params = {
            'host': safe_decode(os.getenv('DB_HOST', 'localhost')),
            'port': int(port) if port else 5432,
            'database': safe_decode(os.getenv('DB_NAME', 'postgres')),
            'user': safe_decode(os.getenv('DB_USER', 'postgres')),
            'password': safe_decode(os.getenv('DB_PASS', ''))
        }
        self._connection: Optional[psycopg2.extensions.connection] = None
    
    def connect(self) -> bool:
        """
        Устанавливает соединение с базой данных.
        
        Returns:
            True если подключение успешно, False в противном случае
        """
        try:
            self._connection = psycopg2.connect(**self.connection_params)
            # Устанавливаем autocommit=False для явного управления транзакциями
            self._connection.autocommit = False
            return True
        except UnicodeDecodeError as e:
            raise RuntimeError(
                f"Ошибка кодировки при подключении: {e}. "
                "Проверьте файл .env - он должен быть в кодировке UTF-8. "
                "Убедитесь, что пароль и другие параметры не содержат недопустимых символов."
            )
        except psycopg2.OperationalError as e:
            raise ConnectionError(f"Ошибка подключения к базе данных: {e}")
        except Exception as e:
            raise RuntimeError(f"Неожиданная ошибка при подключении: {e}")
    
    def disconnect(self):
        """Закрывает соединение с базой данных."""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def is_connected(self) -> bool:
        """Проверяет, установлено ли соединение."""
        return self._connection is not None and not self._connection.closed
    
    @contextmanager
    def get_cursor(self, commit: bool = True):
        """
        Контекстный менеджер для работы с курсором.
        
        Args:
            commit: Автоматически коммитить транзакцию при выходе
            
        Yields:
            Курсор для выполнения SQL-запросов
        """
        if not self.is_connected():
            self.connect()
        
        cursor = self._connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            yield cursor
            if commit:
                self._connection.commit()
        except Exception as e:
            self._connection.rollback()
            raise e
        finally:
            cursor.close()
    
    def __enter__(self):
        """Поддержка контекстного менеджера для самого драйвера."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Закрытие соединения при выходе из контекста."""
        self.disconnect()
    
    # ==================== CREATE OPERATIONS ====================
    
    def insert(self, table: str, data: Dict[str, Any]) -> Optional[int]:
        """
        Вставляет одну запись в таблицу.
        
        Args:
            table: Имя таблицы
            data: Словарь с данными для вставки (ключ - имя колонки, значение - значение)
            
        Returns:
            ID вставленной записи (если есть автоинкремент) или None
        """
        if not data:
            raise ValueError("Данные для вставки не могут быть пустыми")
        
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        values = list(data.values())
        
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) RETURNING id"
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, values)
                result = cursor.fetchone()
                return result['id'] if result and 'id' in result else None
        except psycopg2.Error as e:
            raise RuntimeError(f"Ошибка при вставке данных: {e}")
    
    def insert_many(self, table: str, data_list: List[Dict[str, Any]]) -> int:
        """
        Вставляет несколько записей в таблицу за один запрос.
        
        Args:
            table: Имя таблицы
            data_list: Список словарей с данными для вставки
            
        Returns:
            Количество вставленных записей
        """
        if not data_list:
            return 0
        
        # Проверяем, что все словари имеют одинаковые ключи
        first_keys = set(data_list[0].keys())
        if not all(set(d.keys()) == first_keys for d in data_list):
            raise ValueError("Все записи должны иметь одинаковые ключи")
        
        columns = ', '.join(data_list[0].keys())
        placeholders = ', '.join(['%s'] * len(data_list[0]))
        values = [tuple(d.values()) for d in data_list]
        
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        try:
            with self.get_cursor() as cursor:
                cursor.executemany(query, values)
                return cursor.rowcount
        except psycopg2.Error as e:
            raise RuntimeError(f"Ошибка при массовой вставке данных: {e}")
    
    # ==================== READ OPERATIONS ====================
    
    def select(self, table: str, 
               columns: Optional[List[str]] = None,
               where: Optional[Dict[str, Any]] = None,
               order_by: Optional[str] = None,
               limit: Optional[int] = None,
               offset: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Выполняет SELECT запрос.
        
        Args:
            table: Имя таблицы
            columns: Список колонок для выборки (None = все колонки)
            where: Словарь условий WHERE (ключ - колонка, значение - значение для сравнения)
            order_by: Строка для ORDER BY (например, "id DESC")
            limit: Максимальное количество записей
            offset: Смещение для пагинации
            
        Returns:
            Список словарей с результатами запроса
        """
        cols = ', '.join(columns) if columns else '*'
        query = f"SELECT {cols} FROM {table}"
        params = []
        
        if where:
            conditions = []
            for key, value in where.items():
                conditions.append(f"{key} = %s")
                params.append(value)
            query += " WHERE " + " AND ".join(conditions)
        
        if order_by:
            query += f" ORDER BY {order_by}"
        
        if limit:
            query += f" LIMIT {limit}"
        
        if offset:
            query += f" OFFSET {offset}"
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except psycopg2.Error as e:
            raise RuntimeError(f"Ошибка при выборке данных: {e}")
    
    def select_one(self, table: str,
                   columns: Optional[List[str]] = None,
                   where: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Выполняет SELECT запрос и возвращает одну запись.
        
        Args:
            table: Имя таблицы
            columns: Список колонок для выборки (None = все колонки)
            where: Словарь условий WHERE
            
        Returns:
            Словарь с результатом или None, если запись не найдена
        """
        results = self.select(table, columns, where, limit=1)
        return results[0] if results else None
    
    def select_by_id(self, table: str, record_id: int, 
                     columns: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
        """
        Выполняет SELECT запрос по ID.
        
        Args:
            table: Имя таблицы
            record_id: ID записи
            columns: Список колонок для выборки (None = все колонки)
            
        Returns:
            Словарь с результатом или None, если запись не найдена
        """
        return self.select_one(table, columns, where={'id': record_id})
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """
        Выполняет произвольный SQL-запрос SELECT.
        
        Args:
            query: SQL-запрос
            params: Параметры для запроса
            
        Returns:
            Список словарей с результатами
        """
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except psycopg2.Error as e:
            raise RuntimeError(f"Ошибка при выполнении запроса: {e}")
    
    # ==================== UPDATE OPERATIONS ====================
    
    def update(self, table: str, data: Dict[str, Any], 
               where: Dict[str, Any]) -> int:
        """
        Обновляет записи в таблице.
        
        Args:
            table: Имя таблицы
            data: Словарь с данными для обновления
            where: Словарь условий WHERE
            
        Returns:
            Количество обновленных записей
        """
        if not data:
            raise ValueError("Данные для обновления не могут быть пустыми")
        if not where:
            raise ValueError("Условие WHERE обязательно для безопасности")
        
        set_clause = ', '.join([f"{key} = %s" for key in data.keys()])
        where_clause = ' AND '.join([f"{key} = %s" for key in where.keys()])
        
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        params = list(data.values()) + list(where.values())
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, params)
                return cursor.rowcount
        except psycopg2.Error as e:
            raise RuntimeError(f"Ошибка при обновлении данных: {e}")
    
    def update_by_id(self, table: str, record_id: int, 
                     data: Dict[str, Any]) -> bool:
        """
        Обновляет запись по ID.
        
        Args:
            table: Имя таблицы
            record_id: ID записи
            data: Словарь с данными для обновления
            
        Returns:
            True если запись обновлена, False если не найдена
        """
        count = self.update(table, data, where={'id': record_id})
        return count > 0
    
    # ==================== DELETE OPERATIONS ====================
    
    def delete(self, table: str, where: Dict[str, Any]) -> int:
        """
        Удаляет записи из таблицы.
        
        Args:
            table: Имя таблицы
            where: Словарь условий WHERE (обязательно для безопасности)
            
        Returns:
            Количество удаленных записей
        """
        if not where:
            raise ValueError("Условие WHERE обязательно для безопасности")
        
        where_clause = ' AND '.join([f"{key} = %s" for key in where.keys()])
        query = f"DELETE FROM {table} WHERE {where_clause}"
        params = list(where.values())
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, params)
                return cursor.rowcount
        except psycopg2.Error as e:
            raise RuntimeError(f"Ошибка при удалении данных: {e}")
    
    def delete_by_id(self, table: str, record_id: int) -> bool:
        """
        Удаляет запись по ID.
        
        Args:
            table: Имя таблицы
            record_id: ID записи
            
        Returns:
            True если запись удалена, False если не найдена
        """
        count = self.delete(table, where={'id': record_id})
        return count > 0
    
    # ==================== UTILITY METHODS ====================
    
    def count(self, table: str, where: Optional[Dict[str, Any]] = None) -> int:
        """
        Подсчитывает количество записей в таблице.
        
        Args:
            table: Имя таблицы
            where: Опциональные условия WHERE
            
        Returns:
            Количество записей
        """
        query = f"SELECT COUNT(*) as count FROM {table}"
        params = []
        
        if where:
            conditions = []
            for key, value in where.items():
                conditions.append(f"{key} = %s")
                params.append(value)
            query += " WHERE " + " AND ".join(conditions)
        
        try:
            with self.get_cursor() as cursor:
                cursor.execute(query, params)
                result = cursor.fetchone()
                return result['count'] if result else 0
        except psycopg2.Error as e:
            raise RuntimeError(f"Ошибка при подсчете записей: {e}")
    
    def exists(self, table: str, where: Dict[str, Any]) -> bool:
        """
        Проверяет существование записи.
        
        Args:
            table: Имя таблицы
            where: Условия для проверки
            
        Returns:
            True если запись существует, False в противном случае
        """
        return self.count(table, where) > 0
    
    def begin_transaction(self):
        """Начинает транзакцию."""
        if not self.is_connected():
            self.connect()
        self._connection.autocommit = False
    
    def commit(self):
        """Коммитит текущую транзакцию."""
        if self._connection:
            self._connection.commit()
    
    def rollback(self):
        """Откатывает текущую транзакцию."""
        if self._connection:
            self._connection.rollback()
    
    def execute_sql(self, query: str, params: Optional[Tuple] = None, commit: bool = False) -> List[Dict[str, Any]]:
        """
        Выполняет произвольный SQL-запрос.
        
        Args:
            query: SQL-запрос
            params: Параметры для запроса
            commit: Коммитить транзакцию после выполнения
            
        Returns:
            Список словарей с результатами (для SELECT) или пустой список
        """
        try:
            with self.get_cursor(commit=commit) as cursor:
                cursor.execute(query, params)
                if query.strip().upper().startswith('SELECT'):
                    return [dict(row) for row in cursor.fetchall()]
                return []
        except psycopg2.Error as e:
            raise RuntimeError(f"Ошибка при выполнении SQL: {e}")

