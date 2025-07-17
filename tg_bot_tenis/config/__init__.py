# config/__init__.py
from .logger import logger
from .config import (
    BOT_TOKEN,
    ADMIN_IDS,
    MAX_PARTICIPANTS,
    PRICE,
    CURRENCY,
    CANCEL_HOURS_LIMIT,
    GROUP_ID,
    WEEKDAY_TOPICS,
    SPECIAL_TOPICS,
    WEEKDAY_NAMES,
    LOCATIONS,
    CONDITIONS_TEXT,
    get_weekday_from_date,
    get_topic_id_for_date,
    get_weekday_name
)