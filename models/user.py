"""
Модель пользователя для системы бронирования.

Описывает структуру данных пользователя.
Не содержит логики работы с базой данных.
"""

from typing import Optional, Dict, Any
from datetime import datetime


class User:
    """
    Простая модель пользователя.

    Атрибуты:
        id: Уникальный идентификатор
        username: Имя пользователя
        email: Email адрес
        full_name: Полное имя
        phone: Номер телефона
        role: Роль пользователя
        is_active: Активен ли пользователь
        created_at: Дата создания
        updated_at: Дата обновления
    """

    def __init__(
        self,
        username: str,
        email: str,
        full_name: Optional[str] = None,
        phone: Optional[str] = None,
        role: str = "client",
        is_active: bool = True,
        user_id: Optional[int] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = user_id
        self.username = username
        self.email = email
        self.full_name = full_name
        self.phone = phone
        self.role = role
        self.is_active = is_active
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразует пользователя в словарь.
        """
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "phone": self.phone,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


