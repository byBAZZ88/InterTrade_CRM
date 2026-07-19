"""
InterTrade CRM — ядро системы
Версия: 2.0.0
"""

import os
import sqlite3
import hashlib
import json
import re
from datetime import datetime, timedelta
import base64
from cryptography.fernet import Fernet

from config import (
    DEFAULT_STATUSES, DEFAULT_ACTIVITY_TYPES, DEFAULT_LEAD_SOURCES,
    DEFAULT_SLA_CONFIG, DEFAULT_CURRENCY, DEFAULT_COUNTRY,
    STATUS_NEW, STATUS_SLEEPING, STATUS_BLOCKED,
    ROLE_ADMIN, ROLE_SUPERVISOR, ROLE_USER, ROLES,
    APP_NAME, APP_VERSION, CRYPTO_SALT,
)


class CRMCore:
    """Ядро InterTrade CRM"""

    def __init__(self, db_name="intertrade_crm.db"):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.cursor = self.conn.cursor()
        self.current_user = None
        self.current_role = None
        self._init_database()

        if not self.is_first_run():
            self._load_crypto_key()

    # ═══════════════════════════════════════════════════════════════════
    #  ШИФРОВАНИЕ
    # ═══════════════════════════════════════════════════════════════════

    def _load_crypto_key(self):
        try:
            self.cursor.execute("SELECT enc_data FROM sys_config WHERE id = 1")
            res = self.cursor.fetchone()
            if res:
                config = json.loads(self._simple_decrypt(res[0]))
                self.crypto_key = config.get("crypto_key", "").encode()
                self.fernet = Fernet(self.crypto_key)
                return True
        except Exception:
            pass
        return False

    def _simple_decrypt(self, val):
        if val is None or val == "":
            return ""
        try:
            return base64.urlsafe_b64decode(val.encode()).decode()
        except Exception:
            return ""

    def _simple_encrypt(self, val):
        if val is None or val == "":
            return ""
        return base64.urlsafe_b64encode(val.encode()).decode()

    def _encrypt_val(self, val):
        if val is None or val == "":
            return ""
        return self.fernet.encrypt(str(val).encode()).decode()

    def _decrypt_val(self, val):
        if val is None or val == "":
            return ""
        try:
            return self.fernet.decrypt(val.encode()).decode()
        except Exception:
            return "[DECRYPT ERROR]"

    # ═══════════════════════════════════════════════════════════════════
    #  БАЗА ДАННЫХ
    # ═══════════════════════════════════════════════════════════════════

    def _init_database(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS sys_config (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                enc_data TEXT NOT NULL
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('admin', 'supervisor', 'user')),
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS counterparties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                trade_name TEXT,
                tax_id TEXT,
                vat_id TEXT,
                country TEXT NOT NULL DEFAULT 'US',
                phone TEXT,
                email TEXT,
                contact_person TEXT,
                activity_type TEXT,
                lead_source TEXT,
                currency TEXT NOT NULL DEFAULT 'USD',
                assigned_to TEXT,
                status TEXT NOT NULL DEFAULT 'New',
                sales_amount REAL DEFAULT 0.0,
                last_sale_date TEXT,
                created_at TEXT,
                next_contact_date TEXT,
                last_comment TEXT,
                description TEXT,
                created_by TEXT
            )
        """)

        self.cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_tax_id_country
            ON counterparties(tax_id, country)
            WHERE tax_id IS NOT NULL AND tax_id != ''
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                counterparty_id INTEGER NOT NULL,
                status_name TEXT NOT NULL,
                changed_at TEXT NOT NULL,
                changed_by TEXT,
                FOREIGN KEY (counterparty_id) REFERENCES counterparties(id)
            )
        """)

        self.conn.commit()

    # ═══════════════════════════════════════════════════════════════════
    #  ПЕРВЫЙ ЗАПУСК
    # ═══════════════════════════════════════════════════════════════════

    def is_first_run(self):
        self.cursor.execute("SELECT COUNT(*) FROM sys_config")
        return self.cursor.fetchone()[0] == 0

    def setup_system(self, organization_name, admin_password, base_currency="USD"):
        raw_key = f"{admin_password}:{organization_name}:{CRYPTO_SALT}"
        self.crypto_key = base64.urlsafe_b64encode(
            hashlib.sha256(raw_key.encode()).digest()
        )
        self.fernet = Fernet(self.crypto_key)

        admin_hash = hashlib.sha256(admin_password.encode()).hexdigest()

        config_dict = {
            "organization_name": organization_name,
            "master_password_hash": admin_hash,
            "lock_until": None,
            "crypto_key": self.crypto_key.decode(),
            "base_currency": base_currency,
            "exchange_rates": {},
            "rates_updated_at": None,
            "locale": "en",
            "statuses": DEFAULT_STATUSES,
            "activity_types": DEFAULT_ACTIVITY_TYPES,
            "lead_sources": DEFAULT_LEAD_SOURCES,
            "sla_config": DEFAULT_SLA_CONFIG,
        }

        self.cursor.execute(
            "INSERT OR REPLACE INTO sys_config (id, enc_data) VALUES (1, ?)",
            (self._simple_encrypt(json.dumps(config_dict)),),
        )

        # Создаём учётку admin
        self.cursor.execute(
            "INSERT INTO users (username, password_hash, role, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
            ("admin", admin_hash, ROLE_ADMIN, datetime.now().strftime("%Y-%m-%d")),
        )

        self.conn.commit()

    # ═══════════════════════════════════════════════════════════════════
    #  РАБОТА С КОНФИГОМ
    # ═══════════════════════════════════════════════════════════════════

    def _load_config(self):
        self.cursor.execute("SELECT enc_data FROM sys_config WHERE id = 1")
        res = self.cursor.fetchone()
        return json.loads(self._simple_decrypt(res[0])) if res else {}

    def _save_config(self, config_dict):
        self.cursor.execute(
            "UPDATE sys_config SET enc_data = ? WHERE id = 1",
            (self._simple_encrypt(json.dumps(config_dict)),),
        )
        self.conn.commit()

    def get_organization_name(self):
        return self._load_config().get("organization_name", APP_NAME)

    def get_base_currency(self):
        return self._load_config().get("base_currency", DEFAULT_CURRENCY)

    def get_sla_config(self):
        return self._load_config().get("sla_config", DEFAULT_SLA_CONFIG)

    def get_activity_types(self):
        return self._load_config().get("activity_types", DEFAULT_ACTIVITY_TYPES)

    def get_lead_sources(self):
        return self._load_config().get("lead_sources", DEFAULT_LEAD_SOURCES)

    def get_statuses(self):
        return self._load_config().get("statuses", DEFAULT_STATUSES)

    def get_exchange_rates(self):
        config = self._load_config()
        return config.get("exchange_rates", {}), config.get("rates_updated_at")
    # ═══════════════════════════════════════════════════════════════════
    #  АВТОРИЗАЦИЯ И ПОЛЬЗОВАТЕЛИ
    # ═══════════════════════════════════════════════════════════════════

    def verify_password(self, username, password):
        """Проверка пароля. Возвращает (success, message, role)."""
        config = self._load_config()
        lock_until_str = config.get("lock_until")

        if lock_until_str:
            try:
                lock_until = datetime.strptime(lock_until_str, "%Y-%m-%d %H:%M:%S")
                if datetime.now() < lock_until:
                    minutes_left = int((lock_until - datetime.now()).total_seconds() / 60) + 1
                    return False, f"Access blocked. Try again in {minutes_left} min.", None
                else:
                    config["lock_until"] = None
                    self._save_config(config)
            except (ValueError, TypeError):
                pass

        self.cursor.execute(
            "SELECT password_hash, role, is_active FROM users WHERE username = ?",
            (username,),
        )
        user = self.cursor.fetchone()

        if not user:
            return False, "Invalid username or password.", None

        if not user[2]:
            return False, "Account is deactivated. Contact administrator.", None

        input_hash = hashlib.sha256(password.encode()).hexdigest()
        if input_hash == user[0]:
            self.current_user = username
            self.current_role = user[1]
            return True, "Login successful.", user[1]
        else:
            self._increment_failed_attempts(config)
            return False, "Invalid username or password.", None

    _failed_attempts = 0

    def _increment_failed_attempts(self, config):
        self._failed_attempts += 1
        if self._failed_attempts >= 5:
            lock_time = (datetime.now() + timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
            config["lock_until"] = lock_time
            self._save_config(config)
            self._failed_attempts = 0

    def add_user(self, username, password, role):
        """Добавить пользователя (admin/supervisor)."""
        if role not in ROLES:
            return False, f"Invalid role. Use: {', '.join(ROLES)}"
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        try:
            self.cursor.execute(
                "INSERT INTO users (username, password_hash, role, is_active, created_at) VALUES (?, ?, ?, 1, ?)",
                (username.lower(), password_hash, role, datetime.now().strftime("%Y-%m-%d")),
            )
            self.conn.commit()
            return True, f"User '{username}' created."
        except sqlite3.IntegrityError:
            return False, f"Username '{username}' already exists."

    def get_users(self):
        """Список всех пользователей."""
        self.cursor.execute("SELECT id, username, role, is_active, created_at FROM users")
        return [
            {"id": r[0], "username": r[1], "role": r[2], "is_active": r[3], "created_at": r[4]}
            for r in self.cursor.fetchall()
        ]

    def toggle_user_active(self, user_id):
        """Включить/выключить пользователя."""
        self.cursor.execute("SELECT is_active FROM users WHERE id = ?", (user_id,))
        row = self.cursor.fetchone()
        if not row:
            return False
        new_state = 0 if row[0] else 1
        self.cursor.execute("UPDATE users SET is_active = ? WHERE id = ?", (new_state, user_id))
        self.conn.commit()
        return True

    def is_settings_locked(self):
        config = self._load_config()
        lock_until_str = config.get("lock_until")
        if not lock_until_str:
            return False, ""
        try:
            lock_until = datetime.strptime(lock_until_str, "%Y-%m-%d %H:%M:%S")
            if datetime.now() < lock_until:
                minutes_left = int((lock_until - datetime.now()).total_seconds() / 60) + 1
                return True, f"Access blocked. {minutes_left} min remaining."
            else:
                config["lock_until"] = None
                self._save_config(config)
                return False, ""
        except (ValueError, TypeError):
            return False, ""

    # ═══════════════════════════════════════════════════════════════════
    #  ПРОВЕРКА ДУБЛИКАТА TAX ID
    # ═══════════════════════════════════════════════════════════════════

    def _is_tax_id_duplicate(self, tax_id, country, exclude_id=None):
        if not tax_id or not tax_id.strip():
            return False
        tid = tax_id.strip()
        self.cursor.execute("SELECT id, tax_id, country FROM counterparties")
        for row in self.cursor.fetchall():
            if exclude_id and row[0] == exclude_id:
                continue
            existing_tax = self._decrypt_val(row[1]) if row[1] else ""
            existing_country = row[2] if row[2] else ""
            if existing_tax == tid and existing_country == country:
                return True
        return False

    # ═══════════════════════════════════════════════════════════════════
    #  CRUD: КОНТРАГЕНТЫ
    # ═══════════════════════════════════════════════════════════════════

    def add_counterparty(
        self, name, tax_id="", vat_id="", country="US",
        phone="", email="", contact_person="",
        activity_type="", lead_source="Website",
        currency=None, assigned_to="",
        comment="", description="", trade_name="",
        custom_date=None,
    ):
        if not name or not name.strip():
            return False, "Company name is required."

        tax_id = str(tax_id).strip() if tax_id else ""
        country = str(country).strip()[:2].upper() if country else "US"

        if tax_id and self._is_tax_id_duplicate(tax_id, country):
            return False, f"Counterparty with Tax ID '{tax_id}' and country '{country}' already exists."

        if currency is None:
            currency = self.get_base_currency()

        current_date = custom_date if custom_date else datetime.now().strftime("%Y-%m-%d")

        self.cursor.execute("""
            INSERT INTO counterparties (
                name, trade_name, tax_id, vat_id, country,
                phone, email, contact_person,
                activity_type, lead_source, currency, assigned_to,
                status, sales_amount, last_sale_date,
                created_at, next_contact_date, last_comment, description, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            self._encrypt_val(name),
            self._encrypt_val(trade_name) if trade_name else None,
            self._encrypt_val(tax_id) if tax_id else None,
            self._encrypt_val(vat_id) if vat_id else None,
            country,
            self._encrypt_val(phone) if phone else None,
            self._encrypt_val(email) if email else None,
            self._encrypt_val(contact_person) if contact_person else None,
            self._encrypt_val(activity_type) if activity_type else None,
            self._encrypt_val(lead_source) if lead_source else None,
            currency,
            self._encrypt_val(assigned_to) if assigned_to else None,
            STATUS_NEW,
            0.0,
            None,
            self._encrypt_val(current_date),
            None,
            self._encrypt_val(comment) if comment else None,
            self._encrypt_val(description) if description else None,
            self.current_user,
        ))

        cp_id = self.cursor.lastrowid
        self.cursor.execute(
            "INSERT INTO status_history (counterparty_id, status_name, changed_at, changed_by) VALUES (?, ?, ?, ?)",
            (cp_id, STATUS_NEW, current_date, self.current_user),
        )
        self.conn.commit()
        return True, cp_id

    def update_counterparty_status(self, cp_id, new_status, comment="", custom_date=None, next_contact_date=None):
        current_date = custom_date if custom_date else datetime.now().strftime("%Y-%m-%d")

        self.cursor.execute(
            "UPDATE counterparties SET status = ?, last_comment = ?, next_contact_date = ? WHERE id = ?",
            (
                new_status,
                self._encrypt_val(comment) if comment else None,
                self._encrypt_val(next_contact_date) if next_contact_date else None,
                cp_id,
            ),
        )
        self.cursor.execute(
            "INSERT INTO status_history (counterparty_id, status_name, changed_at, changed_by) VALUES (?, ?, ?, ?)",
            (cp_id, new_status, current_date, self.current_user),
        )
        self.conn.commit()
        return True, "Status updated."

    def update_counterparty_fields(self, cp_id, **kwargs):
        """Обновление произвольных полей контрагента."""
        allowed = ["phone", "email", "contact_person", "activity_type",
                    "lead_source", "currency", "assigned_to", "description",
                    "trade_name", "tax_id", "vat_id", "country", "sales_amount",
                    "last_sale_date"]
        updates = {}
        for key, value in kwargs.items():
            if key in allowed:
                if key in ("currency", "country", "sales_amount"):
                    updates[key] = value
                else:
                    updates[key] = self._encrypt_val(value) if value else None

        if not updates:
            return False, "No valid fields to update."

        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [cp_id]
        self.cursor.execute(f"UPDATE counterparties SET {set_clause} WHERE id = ?", values)
        self.conn.commit()
        return True, "Updated."

    def get_all_counterparties(self):
        self.cursor.execute("""
            SELECT id, name, trade_name, tax_id, vat_id, country,
                   phone, email, contact_person,
                   activity_type, lead_source, currency, assigned_to,
                   status, sales_amount, last_sale_date,
                   created_at, next_contact_date, last_comment, description, created_by
            FROM counterparties
        """)
        result = []
        for row in self.cursor.fetchall():
            result.append({
                "id": row[0],
                "name": self._decrypt_val(row[1]),
                "trade_name": self._decrypt_val(row[2]) if row[2] else "",
                "tax_id": self._decrypt_val(row[3]) if row[3] else "",
                "vat_id": self._decrypt_val(row[4]) if row[4] else "",
                "country": row[5],
                "phone": self._decrypt_val(row[6]) if row[6] else "",
                "email": self._decrypt_val(row[7]) if row[7] else "",
                "contact_person": self._decrypt_val(row[8]) if row[8] else "",
                "activity_type": self._decrypt_val(row[9]) if row[9] else "",
                "lead_source": self._decrypt_val(row[10]) if row[10] else "",
                "currency": row[11],
                "assigned_to": self._decrypt_val(row[12]) if row[12] else "",
                "status": row[13],
                "sales_amount": row[14] or 0.0,
                "last_sale_date": self._decrypt_val(row[15]) if row[15] else "",
                "created_at": self._decrypt_val(row[16]) if row[16] else "",
                "next_contact_date": self._decrypt_val(row[17]) if row[17] else "",
                "last_comment": self._decrypt_val(row[18]) if row[18] else "",
                "description": self._decrypt_val(row[19]) if row[19] else "",
                "created_by": row[20],
            })
        return result

    def refresh_connection(self):
        self.conn.commit()