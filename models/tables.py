"""
Модель стола для системы бронирования.

Описывает структуру данных стола в ресторане.
Не содержит логики работы с базой данных.
"""

from typing import Optional, Dict, Any
from datetime import datetime


class Table:
    """
    Простая модель стола в ресторане.

    Атрибуты:
        id: Уникальный идентификатор
        table_number: Номер стола
        capacity: Вместимость (количество мест)
        location: Расположение стола
        is_available: Доступен ли стол для бронирования
        description: Описание стола
        created_at: Дата создания
        updated_at: Дата обновления
    """

    def __init__(
        self,
        table_number: str,
        capacity: int,
        location: Optional[str] = None,
        is_available: bool = True,
        description: Optional[str] = None,
        table_id: Optional[int] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = table_id
        self.table_number = table_number
        self.capacity = capacity
        self.location = location
        self.is_available = is_available
        self.description = description
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразует стол в словарь.
        """
        return {
            "id": self.id,
            "table_number": self.table_number,
            "capacity": self.capacity,
            "location": self.location,
            "is_available": self.is_available,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

