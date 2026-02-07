"""
Модель бронирования для системы бронирования.

Описывает структуру данных бронирования стола в ресторане.
Не содержит логики работы с базой данных.
"""

from typing import Optional, Dict, Any
from datetime import datetime, date, time


class Booking:
    """
    Простая модель бронирования стола.

    Атрибуты:
        id: Уникальный идентификатор
        user_id: ID пользователя, который делает бронирование (внешний ключ)
        table_id: ID стола, который бронируется (внешний ключ)
        booking_date: Дата бронирования
        booking_time: Время бронирования
        guests_count: Количество гостей
        status: Статус бронирования
        notes: Дополнительные заметки
        created_at: Дата создания
        updated_at: Дата обновления
    """

    def __init__(
        self,
        user_id: int,
        table_id: int,
        booking_date: date,
        booking_time: time,
        guests_count: int,
        status: str = "pending",
        notes: Optional[str] = None,
        booking_id: Optional[int] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = booking_id
        self.user_id = user_id
        self.table_id = table_id
        self.booking_date = booking_date
        self.booking_time = booking_time
        self.guests_count = guests_count
        self.status = status
        self.notes = notes
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразует бронирование в словарь.
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "table_id": self.table_id,
            "booking_date": self.booking_date,
            "booking_time": self.booking_time,
            "guests_count": self.guests_count,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

