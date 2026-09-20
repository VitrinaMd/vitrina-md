import os
import re
import html
import time
import hashlib
import logging
import sqlite3
import threading
import calendar
from datetime import datetime, timezone

import feedparser
from telebot import types

logger = logging.getLogger(__name__)

NEWS_ENABLED = os.getenv("NEWS_ENABLED", "true").strip().lower() in {"1", "true", "yes", "on"}
NEWS_AFTER_LISTINGS = max(1, int(os.getenv("NEWS_AFTER_LISTINGS", "3")))
NEWS_CHECK_INTERVAL = max(300, int(os.getenv("NEWS_CHECK_INTERVAL", "1800")))
NEWS_MAX_AGE_HOURS = max(1, int(os.getenv("NEWS_MAX_AGE_HOURS", "48")))

# Официальная русская RSS-лента Moldpres.
NEWS_FEEDS = [
    ("Moldpres", "https://moldpres.md/config/rss.php?lang=rus"),
]

# Фильтр намеренно строгий: Vitrina не превращается в общий новостной канал.
KEYWORDS = {
    "💰 Налоги и деньги": [
        "налог", "налогов", "налогооблож", "ндс", "акциз", "пошлин",
        "тамож", "фискаль", "бюджет", "банк", "банков", "платеж",
        "перевод средств", "валют", "кредит", "финанс",
    ],
    "💼 Работа и бизнес": [
        "работодател", "работник", "занятост", "трудов", "зарплат",
        "заработн", "ваканси", "предприним", "бизнес", "компани",
        "малый бизнес", "самозанят", "индивидуальн", "ип ",
        "экономическ", "экономик", "экспорт", "импорт",
    ],
    "💻 IT и цифровизация": [
        "информационн", "технолог", "цифров", "digital", "it ",
        "айти", "искусственн", "интеллект", "кибер", "онлайн",
        "электронн", "программ", "стартап", "инновац", "фриланс",
        "удален", "удалён", "платформ",
    ],
    "🇪🇺 Европа": [
        "евросоюз", "европейск", "ес ", "германи", "румын",
        "трансгранич", "единый рынок",
    ],
}

NEGATIVE_KEYWORDS = [
    "футбол", "баскетбол", "теннис", "чемпионат", "матч",
    "дтп", "авария", "пожар", "убийств", "ограблен",
    "погода", "гороскоп", "концерт", "фестиваль",
]


def _db(db_path):
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


def init_news_db(db_path):
    conn = _db(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS news (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            source_url TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            summary TEXT,
            category TEXT,
            published_at TEXT,
            discovered_at TEXT NOT NULL,
            telegram_message_id INTEGER,
            status TEXT NOT NULL DEFAULT 'queued',
            content_hash TEXT NOT NULL UNIQUE
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS app_state (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    conn.execute("""
        INSERT OR IGNORE INTO app_state(key, value)
        VALUES ('listings_since_news', '0')
    """)
    conn.commit()
    conn.close()


def _clean(value):
    value = value or ""
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _entry_timestamp(entry):
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return None
    try:
        return datetime.fromtimestamp(calendar.timegm(parsed), tz=timezone.utc)
    except Exception:
        return None


def _classify(title, summary):
    text = f"{title} {summary}".lower()

    if any(word in text for word in NEGATIVE_KEYWORDS):
        return None

    best_category = None
    best_score = 0

    for category, words in KEYWORDS.items():
        score = sum(1 for word in words if word in text)
        if score > best_score:
            best_category = category
            best_score = score

    return best_category if best_score >= 1 else None


def _short_summary(value, limit=420):
    value = _clean(value)
    if not value:
        return ""
    if len(value) <= limit:
        return value
    cut = value[:limit].rsplit(" ", 1)[0].rstrip(" ,;:-")
    return cut + "…"


def collect_news(db_path):
    now = datetime.now(timezone.utc)
    inserted = 0

    for source, feed_url in NEWS_FEEDS:
        try:
            feed = feedparser.parse(
                feed_url,
                request_headers={"User-Agent": "VitrinaFreelanceMD/1.0"}
            )

            if getattr(feed, "bozo", False) and not getattr(feed, "entries", None):
                logger.warning("News RSS error (%s): %s", source, getattr(feed, "bozo_exception", "unknown"))
                continue

            for entry in feed.entries[:60]:
                title = _clean(entry.get("title", ""))
                url = (entry.get("link") or "").strip()
                raw_summary = entry.get("summary") or entry.get("description") or ""
                summary = _short_summary(raw_summary)

                if not title or not url:
                    continue

                published_dt = _entry_timestamp(entry)
                if published_dt is None:
                    # Не публикуем запись без проверяемой даты: свежесть неизвестна.
                    continue

                age_hours = (now - published_dt).total_seconds() / 3600
                if age_hours < -1 or age_hours > NEWS_MAX_AGE_HOURS:
                    continue

                category = _classify(title, summary)
                if not category:
                    continue

                content_hash = hashlib.sha256(
                    f"{source}|{url}|{title}".encode("utf-8")
                ).hexdigest()

                conn = _db(db_path)
                try:
                    cur = conn.execute("""
                        INSERT OR IGNORE INTO news (
                            source, source_url, title, summary, category,
                            published_at, discovered_at, status, content_hash
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, 'queued', ?)
                    """, (
                        source,
                        url,
                        title,
                        summary,
                        category,
                        published_dt.isoformat(),
                        now.isoformat(),
                        content_hash,
                    ))
                    conn.commit()
                    if cur.rowcount:
                        inserted += 1
                finally:
                    conn.close()

        except Exception:
            logger.exception("News collection failed for %s", source)

    if inserted:
        logger.info("News collector: %s new relevant item(s)", inserted)

    return inserted


def register_listing_published(db_path):
    """Вызывать ТОЛЬКО после успешной публикации нового объявления."""
    conn = _db(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT value FROM app_state WHERE key='listings_since_news'"
        ).fetchone()
        value = int(row["value"]) if row else 0
        value += 1
        conn.execute("""
            INSERT INTO app_state(key, value)
            VALUES ('listings_since_news', ?)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value
        """, (str(value),))
        conn.commit()
        logger.info("Listings since last news: %s", value)
        return value
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _news_keyboard(bot_username):
    if not bot_username:
        return None
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(
        "➕ Подать объявление",
        url=f"https://t.me/{bot_username.lstrip('@')}?start=post"
    ))
    return markup


def _format_news(row):
    title = html.escape(row["title"])
    category = html.escape(row["category"] or "Новости")
    source = html.escape(row["source"])
    url = html.escape(row["source_url"], quote=True)

    # RSS-текст не выдаём за собственную аналитику.
    # Берём только короткий фрагмент описания источника.
    summary = _short_summary(row["summary"] or "", 420)

    lines = [
        "📰 <b>НОВОСТИ VFM_D</b>",
        "",
        f"{category}",
        f"<b>{title}</b>",
    ]

    if summary:
        lines.extend(["", html.escape(summary)])

    lines.extend([
        "",
        f'🔗 <b>Источник:</b> <a href="{url}">{source}</a>',
    ])

    return "\n".join(lines)


def publish_one_if_due(bot, db_path, channel_target, bot_username):
    if not NEWS_ENABLED or not channel_target:
        return False

    conn = _db(db_path)
    claimed_id = None

    try:
        conn.execute("BEGIN IMMEDIATE")

        state = conn.execute(
            "SELECT value FROM app_state WHERE key='listings_since_news'"
        ).fetchone()
        count = int(state["value"]) if state else 0

        if count < NEWS_AFTER_LISTINGS:
            conn.rollback()
            return False

        row = conn.execute("""
            SELECT *
            FROM news
            WHERE status='queued'
            ORDER BY published_at DESC, id DESC
            LIMIT 1
        """).fetchone()

        if not row:
            logger.info(
                "News is due (listings_since_news=%s) but no fresh relevant queued item is available; counter is preserved",
                count
            )
            conn.rollback()
            return False

        claimed_id = row["id"]
        updated = conn.execute("""
            UPDATE news
            SET status='publishing'
            WHERE id=? AND status='queued'
        """, (claimed_id,)).rowcount

        if updated != 1:
            conn.rollback()
            return False

        conn.commit()

        # Сеть вызываем вне SQLite-транзакции.
        message = bot.send_message(
            channel_target,
            _format_news(row),
            reply_markup=_news_keyboard(bot_username),
            disable_web_page_preview=True
        )

        conn.execute("BEGIN IMMEDIATE")
        conn.execute("""
            UPDATE news
            SET status='published', telegram_message_id=?
            WHERE id=?
        """, (message.message_id, claimed_id))
        conn.execute("""
            INSERT INTO app_state(key, value)
            VALUES ('listings_since_news', '0')
            ON CONFLICT(key) DO UPDATE SET value='0'
        """)
        conn.commit()

        logger.info("News %s published, message_id=%s", claimed_id, message.message_id)
        return True

    except Exception:
        logger.exception("News publication failed")
        try:
            conn.rollback()
        except Exception:
            pass

        if claimed_id is not None:
            try:
                conn.execute(
                    "UPDATE news SET status='queued' WHERE id=? AND status='publishing'",
                    (claimed_id,)
                )
                conn.commit()
            except Exception:
                logger.exception("Could not return news %s to queue", claimed_id)
        return False

    finally:
        conn.close()


def handle_listing_published(bot, db_path, channel_target, bot_username):
    """Count a successful NEW listing and publish one relevant news item when due.

    If the queue is empty at the threshold, refresh RSS immediately and retry once.
    The counter is reset only by publish_one_if_due after Telegram confirms publication.
    """
    count = register_listing_published(db_path)
    if count < NEWS_AFTER_LISTINGS:
        return False

    if publish_one_if_due(bot, db_path, channel_target, bot_username):
        return True

    # Threshold reached but queue may be empty/stale. Refresh now instead of waiting
    # for the background interval, then make one more safe attempt.
    collect_news(db_path)
    return publish_one_if_due(
        bot=bot, db_path=db_path, channel_target=channel_target, bot_username=bot_username
    )



def recover_interrupted_news(db_path):
    conn = _db(db_path)
    try:
        conn.execute("UPDATE news SET status='queued' WHERE status='publishing'")
        conn.commit()
    finally:
        conn.close()


def start_news_worker(bot, db_path, channel_target_getter, bot_username_getter):
    if not NEWS_ENABLED:
        logger.info("News module disabled")
        return None

    init_news_db(db_path)
    recover_interrupted_news(db_path)

    def worker():
        logger.info(
            "News worker started: interval=%ss, after_listings=%s, max_age=%sh",
            NEWS_CHECK_INTERVAL, NEWS_AFTER_LISTINGS, NEWS_MAX_AGE_HOURS
        )

        while True:
            try:
                collect_news(db_path)
                publish_one_if_due(
                    bot,
                    db_path,
                    channel_target_getter(),
                    bot_username_getter()
                )
            except Exception:
                logger.exception("Unexpected news worker error")

            time.sleep(NEWS_CHECK_INTERVAL)

    thread = threading.Thread(
        target=worker,
        name="vitrina-news-worker",
        daemon=True
    )
    thread.start()
    return thread
