"""
Графический интерфейс для системы бронирования ресторана.
Использует tkinter для создания GUI с вкладками для разных операций.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from datetime import date, time, datetime
from typing import Optional, List
import backend


def init_database():
    """Инициализирует базу данных - применяет миграции и создает таблицы, если их нет."""
    try:
        # Сначала применяем миграции для исправления существующей схемы
        backend.apply_migrations()
        # Затем создаем таблицы, если их нет
        backend.create_tables()
        return True
    except Exception as e:
        messagebox.showerror(
            "Ошибка подключения к БД",
            f"Не удалось подключиться к базе данных:\n{str(e)}\n\n"
            "Проверьте:\n"
            "1. Файл .env существует и содержит правильные данные\n"
            "2. PostgreSQL запущен\n"
            "3. База данных создана\n"
            "4. Параметры подключения корректны"
        )
        return False


class BookingApp:
    """Главное окно приложения с вкладками."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Система бронирования ресторана")
        self.root.geometry("900x700")
        
        # Создаем notebook для вкладок
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Создаем вкладки
        self.users_tab = UsersTab(self.notebook)
        self.tables_tab = TablesTab(self.notebook)
        self.bookings_tab = BookingsTab(self.notebook)
        
        self.notebook.add(self.users_tab.frame, text="Пользователи")
        self.notebook.add(self.tables_tab.frame, text="Столы")
        self.notebook.add(self.bookings_tab.frame, text="Бронирования")


class UsersTab:
    """Вкладка для работы с пользователями."""
    
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.setup_ui()
        self.refresh_list()
    
    def setup_ui(self):
        # Левая панель - форма создания/редактирования
        left_panel = ttk.Frame(self.frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(left_panel, text="Управление пользователями", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Форма
        form_frame = ttk.LabelFrame(left_panel, text="Данные пользователя", padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        ttk.Label(form_frame, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.username_entry = ttk.Entry(form_frame, width=30)
        self.username_entry.grid(row=0, column=1, pady=5, padx=5)
        
        ttk.Label(form_frame, text="Email:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.email_entry = ttk.Entry(form_frame, width=30)
        self.email_entry.grid(row=1, column=1, pady=5, padx=5)
        
        ttk.Label(form_frame, text="Полное имя:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.full_name_entry = ttk.Entry(form_frame, width=30)
        self.full_name_entry.grid(row=2, column=1, pady=5, padx=5)
        
        ttk.Label(form_frame, text="Телефон:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.phone_entry = ttk.Entry(form_frame, width=30)
        self.phone_entry.grid(row=3, column=1, pady=5, padx=5)
        
        ttk.Label(form_frame, text="Роль:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.role_combo = ttk.Combobox(form_frame, values=["client", "admin", "manager"], width=27)
        self.role_combo.set("client")
        self.role_combo.grid(row=4, column=1, pady=5, padx=5)
        
        self.is_active_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(form_frame, text="Активен", variable=self.is_active_var).grid(row=5, column=1, sticky=tk.W, pady=5)
        
        # Кнопки
        buttons_frame = ttk.Frame(left_panel)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(buttons_frame, text="Создать", command=self.create_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Обновить", command=self.update_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Очистить", command=self.clear_form).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Удалить", command=self.delete_user).pack(side=tk.LEFT, padx=5)
        
        # Правая панель - список пользователей
        right_panel = ttk.Frame(self.frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(right_panel, text="Список пользователей", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Поиск
        search_frame = ttk.Frame(right_panel)
        search_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT, padx=5)
        self.search_entry = ttk.Entry(search_frame, width=20)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Найти", command=self.search_user).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Обновить", command=self.refresh_list).pack(side=tk.LEFT, padx=5)
        
        # Таблица
        tree_frame = ttk.Frame(right_panel)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        columns = ("ID", "Username", "Email", "Полное имя", "Телефон", "Роль", "Активен")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind("<Double-1>", self.on_user_select)
        self.tree.bind("<<TreeviewSelect>>", self.on_user_click)
    
    def clear_form(self):
        """Очищает форму."""
        self.username_entry.delete(0, tk.END)
        self.email_entry.delete(0, tk.END)
        self.full_name_entry.delete(0, tk.END)
        self.phone_entry.delete(0, tk.END)
        self.role_combo.set("client")
        self.is_active_var.set(True)
        self.current_user_id = None
    
    def create_user(self):
        """Создает нового пользователя."""
        try:
            username = self.username_entry.get().strip()
            email = self.email_entry.get().strip()
            
            if not username or not email:
                messagebox.showerror("Ошибка", "Username и Email обязательны!")
                return
            
            user = backend.create_user(
                username=username,
                email=email,
                full_name=self.full_name_entry.get().strip() or None,
                phone=self.phone_entry.get().strip() or None,
                role=self.role_combo.get(),
                is_active=self.is_active_var.get()
            )
            
            messagebox.showinfo("Успех", f"Пользователь {user.username} создан!")
            self.clear_form()
            self.refresh_list()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def update_user(self):
        """Обновляет пользователя."""
        if not hasattr(self, 'current_user_id') or not self.current_user_id:
            messagebox.showerror("Ошибка", "Выберите пользователя для обновления!")
            return
        
        try:
            backend.update_user(
                self.current_user_id,
                username=self.username_entry.get().strip(),
                email=self.email_entry.get().strip(),
                full_name=self.full_name_entry.get().strip() or None,
                phone=self.phone_entry.get().strip() or None,
                role=self.role_combo.get(),
                is_active=self.is_active_var.get()
            )
            
            messagebox.showinfo("Успех", "Пользователь обновлен!")
            self.clear_form()
            self.refresh_list()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def delete_user(self):
        """Удаляет пользователя."""
        if not hasattr(self, 'current_user_id') or not self.current_user_id:
            messagebox.showerror("Ошибка", "Выберите пользователя для удаления!")
            return
        
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить этого пользователя?"):
            try:
                backend.delete_user(self.current_user_id)
                messagebox.showinfo("Успех", "Пользователь удален!")
                self.clear_form()
                self.refresh_list()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))
    
    def search_user(self):
        """Поиск пользователя по email или username."""
        search_term = self.search_entry.get().strip()
        if not search_term:
            self.refresh_list()
            return
        
        try:
            # Пробуем найти по email
            user = backend.get_user_by_email(search_term)
            if not user:
                # Пробуем найти по username
                user = backend.get_user_by_username(search_term)
            
            if user:
                self.tree.delete(*self.tree.get_children())
                self.tree.insert("", tk.END, values=(
                    user.id,
                    user.username,
                    user.email,
                    user.full_name or "",
                    user.phone or "",
                    user.role,
                    "Да" if user.is_active else "Нет"
                ))
            else:
                messagebox.showinfo("Результат", "Пользователь не найден")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def refresh_list(self):
        """Обновляет список пользователей."""
        try:
            self.tree.delete(*self.tree.get_children())
            users = backend.get_all_users()
            
            for user in users:
                self.tree.insert("", tk.END, values=(
                    user.id,
                    user.username,
                    user.email,
                    user.full_name or "",
                    user.phone or "",
                    user.role,
                    "Да" if user.is_active else "Нет"
                ))
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def on_user_click(self, event):
        """Обработчик одинарного клика - устанавливает current_user_id для удаления."""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            user_id = item['values'][0]
            self.current_user_id = user_id
    
    def on_user_select(self, event):
        """Обработчик двойного клика на пользователе."""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            user_id = item['values'][0]
            
            try:
                user = backend.get_user_by_id(user_id)
                if user:
                    self.current_user_id = user.id
                    self.username_entry.delete(0, tk.END)
                    self.username_entry.insert(0, user.username)
                    self.email_entry.delete(0, tk.END)
                    self.email_entry.insert(0, user.email)
                    self.full_name_entry.delete(0, tk.END)
                    if user.full_name:
                        self.full_name_entry.insert(0, user.full_name)
                    self.phone_entry.delete(0, tk.END)
                    if user.phone:
                        self.phone_entry.insert(0, user.phone)
                    self.role_combo.set(user.role)
                    self.is_active_var.set(user.is_active)
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))


class TablesTab:
    """Вкладка для работы со столами."""
    
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.setup_ui()
        self.refresh_list()
    
    def setup_ui(self):
        # Левая панель - форма
        left_panel = ttk.Frame(self.frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(left_panel, text="Управление столами", font=("Arial", 14, "bold")).pack(pady=10)
        
        form_frame = ttk.LabelFrame(left_panel, text="Данные стола", padding=10)
        form_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        ttk.Label(form_frame, text="Номер стола:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.table_number_entry = ttk.Entry(form_frame, width=30)
        self.table_number_entry.grid(row=0, column=1, pady=5, padx=5)
        
        ttk.Label(form_frame, text="Вместимость:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.capacity_entry = ttk.Entry(form_frame, width=30)
        self.capacity_entry.grid(row=1, column=1, pady=5, padx=5)
        
        ttk.Label(form_frame, text="Расположение:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.location_entry = ttk.Entry(form_frame, width=30)
        self.location_entry.grid(row=2, column=1, pady=5, padx=5)
        
        ttk.Label(form_frame, text="Описание:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.description_text = scrolledtext.ScrolledText(form_frame, width=25, height=3)
        self.description_text.grid(row=3, column=1, pady=5, padx=5)
        
        self.is_available_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(form_frame, text="Доступен", variable=self.is_available_var).grid(row=4, column=1, sticky=tk.W, pady=5)
        
        buttons_frame = ttk.Frame(left_panel)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(buttons_frame, text="Создать", command=self.create_table).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Обновить", command=self.update_table).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Очистить", command=self.clear_form).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Удалить", command=self.delete_table).pack(side=tk.LEFT, padx=5)
        
        # Правая панель - список
        right_panel = ttk.Frame(self.frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(right_panel, text="Список столов", font=("Arial", 14, "bold")).pack(pady=10)
        
        search_frame = ttk.Frame(right_panel)
        search_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT, padx=5)
        self.search_entry = ttk.Entry(search_frame, width=20)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Найти", command=self.search_table).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="Обновить", command=self.refresh_list).pack(side=tk.LEFT, padx=5)
        
        tree_frame = ttk.Frame(right_panel)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        columns = ("ID", "Номер", "Вместимость", "Расположение", "Доступен", "Описание")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind("<Double-1>", self.on_table_select)
    
    def clear_form(self):
        """Очищает форму."""
        self.table_number_entry.delete(0, tk.END)
        self.capacity_entry.delete(0, tk.END)
        self.location_entry.delete(0, tk.END)
        self.description_text.delete(1.0, tk.END)
        self.is_available_var.set(True)
        self.current_table_id = None
    
    def create_table(self):
        """Создает новый стол."""
        try:
            table_number = self.table_number_entry.get().strip()
            capacity = self.capacity_entry.get().strip()
            
            if not table_number or not capacity:
                messagebox.showerror("Ошибка", "Номер стола и вместимость обязательны!")
                return
            
            table = backend.create_table(
                table_number=table_number,
                capacity=int(capacity),
                location=self.location_entry.get().strip() or None,
                is_available=self.is_available_var.get(),
                description=self.description_text.get(1.0, tk.END).strip() or None
            )
            
            messagebox.showinfo("Успех", f"Стол {table.table_number} создан!")
            self.clear_form()
            self.refresh_list()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def update_table(self):
        """Обновляет стол."""
        if not hasattr(self, 'current_table_id') or not self.current_table_id:
            messagebox.showerror("Ошибка", "Выберите стол для обновления!")
            return
        
        try:
            backend.update_table(
                self.current_table_id,
                table_number=self.table_number_entry.get().strip(),
                capacity=int(self.capacity_entry.get().strip()),
                location=self.location_entry.get().strip() or None,
                is_available=self.is_available_var.get(),
                description=self.description_text.get(1.0, tk.END).strip() or None
            )
            
            messagebox.showinfo("Успех", "Стол обновлен!")
            self.clear_form()
            self.refresh_list()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def delete_table(self):
        """Удаляет стол."""
        if not hasattr(self, 'current_table_id') or not self.current_table_id:
            messagebox.showerror("Ошибка", "Выберите стол для удаления!")
            return
        
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить этот стол?"):
            try:
                backend.delete_table(self.current_table_id)
                messagebox.showinfo("Успех", "Стол удален!")
                self.clear_form()
                self.refresh_list()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))
    
    def search_table(self):
        """Поиск стола по номеру."""
        search_term = self.search_entry.get().strip()
        if not search_term:
            self.refresh_list()
            return
        
        try:
            table = backend.get_table_by_number(search_term)
            if table:
                self.tree.delete(*self.tree.get_children())
                self.tree.insert("", tk.END, values=(
                    table.id,
                    table.table_number,
                    table.capacity,
                    table.location or "",
                    "Да" if table.is_available else "Нет",
                    table.description or ""
                ))
            else:
                messagebox.showinfo("Результат", "Стол не найден")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def refresh_list(self):
        """Обновляет список столов."""
        try:
            self.tree.delete(*self.tree.get_children())
            tables = backend.get_all_tables()
            
            for table in tables:
                self.tree.insert("", tk.END, values=(
                    table.id,
                    table.table_number,
                    table.capacity,
                    table.location or "",
                    "Да" if table.is_available else "Нет",
                    (table.description or "")[:50]  # Обрезаем длинные описания
                ))
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def on_table_select(self, event):
        """Обработчик двойного клика на столе."""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            table_id = item['values'][0]
            
            try:
                table = backend.get_table_by_id(table_id)
                if table:
                    self.current_table_id = table.id
                    self.table_number_entry.delete(0, tk.END)
                    self.table_number_entry.insert(0, table.table_number)
                    self.capacity_entry.delete(0, tk.END)
                    self.capacity_entry.insert(0, str(table.capacity))
                    self.location_entry.delete(0, tk.END)
                    if table.location:
                        self.location_entry.insert(0, table.location)
                    self.description_text.delete(1.0, tk.END)
                    if table.description:
                        self.description_text.insert(1.0, table.description)
                    self.is_available_var.set(table.is_available)
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))


class BookingsTab:
    """Вкладка для работы с бронированиями."""
    
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.setup_ui()
        self.refresh_lists()
    
    def setup_ui(self):
        # Верхняя панель - форма
        top_panel = ttk.Frame(self.frame)
        top_panel.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(top_panel, text="Управление бронированиями", font=("Arial", 14, "bold")).pack(pady=10)
        
        form_frame = ttk.LabelFrame(top_panel, text="Данные бронирования", padding=10)
        form_frame.pack(fill=tk.X, pady=5)
        
        # Первая строка
        row1 = ttk.Frame(form_frame)
        row1.pack(fill=tk.X, pady=5)
        
        ttk.Label(row1, text="Пользователь ID:").pack(side=tk.LEFT, padx=5)
        self.user_id_entry = ttk.Entry(row1, width=15)
        self.user_id_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row1, text="Стол ID:").pack(side=tk.LEFT, padx=5)
        self.table_id_entry = ttk.Entry(row1, width=15)
        self.table_id_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row1, text="Количество гостей:").pack(side=tk.LEFT, padx=5)
        self.guests_entry = ttk.Entry(row1, width=15)
        self.guests_entry.pack(side=tk.LEFT, padx=5)
        
        # Вторая строка
        row2 = ttk.Frame(form_frame)
        row2.pack(fill=tk.X, pady=5)
        
        ttk.Label(row2, text="Дата (YYYY-MM-DD):").pack(side=tk.LEFT, padx=5)
        self.date_entry = ttk.Entry(row2, width=15)
        self.date_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row2, text="Время (HH:MM):").pack(side=tk.LEFT, padx=5)
        self.time_entry = ttk.Entry(row2, width=15)
        self.time_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row2, text="Длительность (часы):").pack(side=tk.LEFT, padx=5)
        self.duration_entry = ttk.Entry(row2, width=15)
        self.duration_entry.insert(0, "2")
        self.duration_entry.pack(side=tk.LEFT, padx=5)
        
        # Третья строка
        row3 = ttk.Frame(form_frame)
        row3.pack(fill=tk.X, pady=5)
        
        ttk.Label(row3, text="Статус:").pack(side=tk.LEFT, padx=5)
        self.status_combo = ttk.Combobox(row3, values=["pending", "confirmed", "cancelled", "completed"], width=12)
        self.status_combo.set("pending")
        self.status_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(row3, text="Заметки:").pack(side=tk.LEFT, padx=5)
        self.notes_entry = ttk.Entry(row3, width=30)
        self.notes_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(row3, text="Проверить доступность", command=self.check_availability).pack(side=tk.LEFT, padx=5)
        
        # Кнопки
        buttons_frame = ttk.Frame(top_panel)
        buttons_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(buttons_frame, text="Создать", command=self.create_booking).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Обновить", command=self.update_booking).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Очистить", command=self.clear_form).pack(side=tk.LEFT, padx=5)
        ttk.Button(buttons_frame, text="Удалить", command=self.delete_booking).pack(side=tk.LEFT, padx=5)
        
        # Нижняя панель - список бронирований
        bottom_panel = ttk.Frame(self.frame)
        bottom_panel.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(bottom_panel, text="Список бронирований", font=("Arial", 14, "bold")).pack(pady=10)
        
        # Фильтры
        filter_frame = ttk.Frame(bottom_panel)
        filter_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(filter_frame, text="Фильтр по статусу:").pack(side=tk.LEFT, padx=5)
        self.status_filter = ttk.Combobox(filter_frame, values=["", "pending", "confirmed", "cancelled", "completed"], width=15)
        self.status_filter.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(filter_frame, text="Применить фильтр", command=self.refresh_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_frame, text="Обновить", command=self.refresh_lists).pack(side=tk.LEFT, padx=5)
        
        # Таблица
        tree_frame = ttk.Frame(bottom_panel)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        columns = ("ID", "User ID", "Table ID", "Дата", "Время", "Гостей", "Статус", "Заметки")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=12)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind("<Double-1>", self.on_booking_select)
    
    def clear_form(self):
        """Очищает форму."""
        self.user_id_entry.delete(0, tk.END)
        self.table_id_entry.delete(0, tk.END)
        self.guests_entry.delete(0, tk.END)
        self.date_entry.delete(0, tk.END)
        self.time_entry.delete(0, tk.END)
        self.duration_entry.delete(0, tk.END)
        self.duration_entry.insert(0, "2")
        self.status_combo.set("pending")
        self.notes_entry.delete(0, tk.END)
        self.current_booking_id = None
    
    def check_availability(self):
        """Проверяет доступность стола."""
        try:
            table_id = int(self.table_id_entry.get().strip())
            date_str = self.date_entry.get().strip()
            time_str = self.time_entry.get().strip()
            duration = int(self.duration_entry.get().strip() or "2")
            
            if not date_str or not time_str:
                messagebox.showerror("Ошибка", "Укажите дату и время!")
                return
            
            booking_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            booking_time = datetime.strptime(time_str, "%H:%M").time()
            
            is_available = backend.check_table_availability(
                table_id=table_id,
                booking_date=booking_date,
                booking_time=booking_time,
                duration_hours=duration
            )
            
            if is_available:
                messagebox.showinfo("Результат", "Стол доступен для бронирования!")
            else:
                messagebox.showwarning("Результат", "Стол занят в это время!")
        except ValueError as e:
            messagebox.showerror("Ошибка", f"Неверный формат данных: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def create_booking(self):
        """Создает новое бронирование."""
        try:
            user_id = int(self.user_id_entry.get().strip())
            table_id = int(self.table_id_entry.get().strip())
            guests_count = int(self.guests_entry.get().strip())
            date_str = self.date_entry.get().strip()
            time_str = self.time_entry.get().strip()
            duration = int(self.duration_entry.get().strip() or "2")
            
            if not date_str or not time_str:
                messagebox.showerror("Ошибка", "Укажите дату и время!")
                return
            
            booking_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            booking_time = datetime.strptime(time_str, "%H:%M").time()
            
            booking = backend.create_booking(
                user_id=user_id,
                table_id=table_id,
                booking_date=booking_date,
                booking_time=booking_time,
                guests_count=guests_count,
                status=self.status_combo.get(),
                notes=self.notes_entry.get().strip() or None,
                duration_hours=duration
            )
            
            messagebox.showinfo("Успех", f"Бронирование создано! ID: {booking.id}")
            self.clear_form()
            self.refresh_lists()
        except ValueError as e:
            messagebox.showerror("Ошибка", f"Неверный формат данных: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def update_booking(self):
        """Обновляет бронирование."""
        if not hasattr(self, 'current_booking_id') or not self.current_booking_id:
            messagebox.showerror("Ошибка", "Выберите бронирование для обновления!")
            return
        
        try:
            update_data = {}
            
            if self.user_id_entry.get().strip():
                update_data['user_id'] = int(self.user_id_entry.get().strip())
            if self.table_id_entry.get().strip():
                update_data['table_id'] = int(self.table_id_entry.get().strip())
            if self.guests_entry.get().strip():
                update_data['guests_count'] = int(self.guests_entry.get().strip())
            if self.date_entry.get().strip():
                update_data['booking_date'] = datetime.strptime(self.date_entry.get().strip(), "%Y-%m-%d").date()
            if self.time_entry.get().strip():
                update_data['booking_time'] = datetime.strptime(self.time_entry.get().strip(), "%H:%M").time()
            if self.notes_entry.get().strip():
                update_data['notes'] = self.notes_entry.get().strip()
            
            update_data['status'] = self.status_combo.get()
            
            backend.update_booking(self.current_booking_id, **update_data)
            
            messagebox.showinfo("Успех", "Бронирование обновлено!")
            self.clear_form()
            self.refresh_lists()
        except ValueError as e:
            messagebox.showerror("Ошибка", f"Неверный формат данных: {e}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def delete_booking(self):
        """Удаляет бронирование."""
        if not hasattr(self, 'current_booking_id') or not self.current_booking_id:
            messagebox.showerror("Ошибка", "Выберите бронирование для удаления!")
            return
        
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить это бронирование?"):
            try:
                backend.delete_booking(self.current_booking_id)
                messagebox.showinfo("Успех", "Бронирование удалено!")
                self.clear_form()
                self.refresh_lists()
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))
    
    def refresh_list(self):
        """Обновляет список бронирований с фильтром."""
        try:
            self.tree.delete(*self.tree.get_children())
            
            status_filter = self.status_filter.get().strip()
            bookings = backend.get_all_bookings(status=status_filter if status_filter else None)
            
            for booking in bookings:
                self.tree.insert("", tk.END, values=(
                    booking.id,
                    booking.user_id,
                    booking.table_id,
                    str(booking.booking_date),
                    str(booking.booking_time),
                    booking.guests_count,
                    booking.status,
                    (booking.notes or "")[:30]  # Обрезаем длинные заметки
                ))
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
    def refresh_lists(self):
        """Обновляет все списки."""
        self.refresh_list()
    
    def on_booking_select(self, event):
        """Обработчик двойного клика на бронировании."""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            booking_id = item['values'][0]
            
            try:
                booking = backend.get_booking_by_id(booking_id)
                if booking:
                    self.current_booking_id = booking.id
                    self.user_id_entry.delete(0, tk.END)
                    self.user_id_entry.insert(0, str(booking.user_id))
                    self.table_id_entry.delete(0, tk.END)
                    self.table_id_entry.insert(0, str(booking.table_id))
                    self.guests_entry.delete(0, tk.END)
                    self.guests_entry.insert(0, str(booking.guests_count))
                    self.date_entry.delete(0, tk.END)
                    self.date_entry.insert(0, str(booking.booking_date))
                    self.time_entry.delete(0, tk.END)
                    self.time_entry.insert(0, str(booking.booking_time))
                    self.status_combo.set(booking.status)
                    self.notes_entry.delete(0, tk.END)
                    if booking.notes:
                        self.notes_entry.insert(0, booking.notes)
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))


def main():
    """Запуск приложения."""
    root = tk.Tk()
    
    # Инициализируем базу данных перед запуском GUI
    if not init_database():
        root.destroy()
        return
    
    app = BookingApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

