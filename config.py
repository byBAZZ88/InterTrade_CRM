"""
InterTrade CRM — конфигурация по умолчанию
Версия: 1.0.0
"""

# ─── СТАТУСЫ ──────────────────────────────────────────────────────────
# Активная воронка
STATUS_NEW = "New"
STATUS_VERIFICATION = "Verification"
STATUS_NEGOTIATION = "Negotiation"
STATUS_PROPOSAL = "Proposal"
STATUS_AWAITING_PAYMENT = "Awaiting Payment"
STATUS_PAID = "Paid"
STATUS_DEAL_CLOSED = "Deal Closed"

# Долгосрочные состояния
STATUS_REGULAR = "Regular"
STATUS_RARE = "Rare"
STATUS_SLEEPING = "Sleeping"
STATUS_ON_HOLD = "On Hold"
STATUS_CONTACT_BY_DATE = "Contact by Date"
STATUS_BLOCKED = "Blocked"

DEFAULT_STATUSES = [
    STATUS_NEW,
    STATUS_VERIFICATION,
    STATUS_NEGOTIATION,
    STATUS_PROPOSAL,
    STATUS_AWAITING_PAYMENT,
    STATUS_PAID,
    STATUS_DEAL_CLOSED,
    STATUS_REGULAR,
    STATUS_RARE,
    STATUS_SLEEPING,
    STATUS_ON_HOLD,
    STATUS_CONTACT_BY_DATE,
    STATUS_BLOCKED,
]

# ─── СПРАВОЧНИКИ ──────────────────────────────────────────────────────
DEFAULT_ACTIVITY_TYPES = [
    "Manufacturing",
    "Construction & Engineering",
    "Retail & Wholesale",
    "IT & Technology",
    "Logistics & Transportation",
    "Financial Services",
    "Healthcare & Pharma",
    "Energy & Utilities",
    "Agriculture & Food",
    "Professional Services",
]

DEFAULT_LEAD_SOURCES = [
    "Website",
    "Cold Search",
    "Referral",
    "Social Media",
    "Exhibition",
    "Returning Client",
]

# ─── SLA ───────────────────────────────────────────────────────────────
DEFAULT_SLA_CONFIG = {
    "alerts": {
        "New": {"days": 0},
        "Verification": {"days": 3},
        "Negotiation": {"days": 7},
        "Proposal": {"days": 5},
        "Awaiting Payment": {"days": 3},
        "Paid": {"days": 14},
        "Deal Closed": {"days": 7},
        "Regular": {"days": 30},
        "Rare": {"days": 45},
        "Sleeping": {"days": 90},
        "On Hold": {"days": 60},
        "Contact by Date": {"days": 0},
        "Blocked": {"days": 0},
    },
    "reanimation": {"days": 90},
}

# ─── ВАЛЮТЫ (ISO 4217) ────────────────────────────────────────────────
ALL_CURRENCIES = [
    "USD", "EUR", "GBP", "JPY", "CNY", "RUB", "CHF", "CAD", "AUD", "NZD",
    "SEK", "NOK", "DKK", "PLN", "CZK", "HUF", "RON", "BGN", "TRY", "INR",
    "BRL", "MXN", "ZAR", "KRW", "SGD", "HKD", "AED", "SAR", "THB", "MYR",
    "IDR", "PHP", "VND", "EGP", "NGN", "KES", "ARS", "CLP", "COP", "PEN",
    "UAH", "KZT", "BYN", "GEL", "AMD", "AZN", "MDL", "UZS", "KGS", "TJS",
]

DEFAULT_CURRENCY = "USD"

# ─── СТРАНЫ (ISO 3166-1 alpha-2) ──────────────────────────────────────
ALL_COUNTRIES = {
    "US": "United States", "DE": "Germany", "GB": "United Kingdom",
    "FR": "France", "IT": "Italy", "ES": "Spain", "NL": "Netherlands",
    "BE": "Belgium", "AT": "Austria", "CH": "Switzerland",
    "CN": "China", "JP": "Japan", "KR": "South Korea", "IN": "India",
    "BR": "Brazil", "MX": "Mexico", "CA": "Canada", "AU": "Australia",
    "AE": "United Arab Emirates", "SA": "Saudi Arabia", "TR": "Turkey",
    "RU": "Russia", "BY": "Belarus", "KZ": "Kazakhstan", "UA": "Ukraine",
    "PL": "Poland", "CZ": "Czech Republic", "RO": "Romania", "BG": "Bulgaria",
    "ZA": "South Africa", "EG": "Egypt", "NG": "Nigeria", "KE": "Kenya",
    "SG": "Singapore", "HK": "Hong Kong", "TH": "Thailand", "VN": "Vietnam",
    "MY": "Malaysia", "ID": "Indonesia", "PH": "Philippines",
    "AR": "Argentina", "CL": "Chile", "CO": "Colombia", "PE": "Peru",
    "SE": "Sweden", "NO": "Norway", "DK": "Denmark", "FI": "Finland",
}

DEFAULT_COUNTRY = "US"

# ─── ПРОЧЕЕ ────────────────────────────────────────────────────────────
APP_NAME = "InterTrade CRM"
APP_VERSION = "1.0.0"
APP_ID = "intertrade_crm"
CRYPTO_SALT = "InterTradeCRM_2026"

DEFAULT_LOCALE = "en"

# Роли пользователей
ROLE_ADMIN = "admin"
ROLE_SUPERVISOR = "supervisor"
ROLE_USER = "user"
ROLES = [ROLE_ADMIN, ROLE_SUPERVISOR, ROLE_USER]