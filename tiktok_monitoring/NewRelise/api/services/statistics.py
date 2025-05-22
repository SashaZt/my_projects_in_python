# # # app/services/statistics.py
# # import logging
# # import time
# # from datetime import datetime, timedelta, timezone

# # from database import db

# # logger = logging.getLogger(__name__)

# # # Кэш для статистики
# # stats_cache = {"data": None, "timestamp": 0, "ttl": 10}  # время жизни кэша в секундах


# # def calculate_percentage_change(current, previous):
# #     """Расчет процентного изменения между двумя значениями"""
# #     if not previous or previous == 0:
# #         return None

# #     change = ((current - previous) / previous) * 100

# #     if change > 0:
# #         return f"↑ {change:.2f}%"
# #     elif change < 0:
# #         return f"↓ {abs(change):.2f}%"
# #     else:
# #         return "0%"


# # async def get_dashboard_statistics():
# #     """Получение статистики для дашборда с кэшированием"""
# #     current_time = time.time()

# #     # Проверяем кэш
# #     if (
# #         stats_cache["data"]
# #         and (current_time - stats_cache["timestamp"]) < stats_cache["ttl"]
# #     ):
# #         return stats_cache["data"]

# #     try:
# #         stats = await fetch_dashboard_statistics()
# #         stats_cache["data"] = stats
# #         stats_cache["timestamp"] = current_time
# #         return stats
# #     except Exception as e:
# #         logger.error(f"Error fetching dashboard statistics: {e}")
# #         return {"error": str(e)}


# # async def fetch_dashboard_statistics():
# #     """Получение статистики для дашборда из базы данных"""
# #     now = datetime.now(timezone.utc)
# #     today = now.replace(hour=0, minute=0, second=0, microsecond=0)
# #     yesterday = today - timedelta(days=1)
# #     week_start = today - timedelta(days=today.weekday())
# #     prev_week_start = week_start - timedelta(days=7)
# #     month_start = today.replace(day=1)
# #     prev_month_start = (month_start - timedelta(days=1)).replace(day=1)

# #     # Получаем список стримеров из кластера AGENCY
# #     agency_streamers = await db.fetch(
# #         """
# #         SELECT s.id FROM streamers s
# #         JOIN clusters c ON s.cluster_id = c.id
# #         WHERE c.name = 'AGENCY'
# #         """
# #     )

# #     agency_streamer_ids = [s["id"] for s in agency_streamers]

# #     if not agency_streamer_ids:
# #         return {"error": "No AGENCY streamers found"}

# #     # Запускаем параллельные запросы
# #     gifts_today_task = db.fetchrow(
# #         """
# #         SELECT
# #             COUNT(*) as gift_count,
# #             COALESCE(SUM(total_diamonds), 0) as diamond_total
# #         FROM gifts
# #         WHERE streamer_id = ANY($1)
# #         AND event_time >= $2
# #         """,
# #         agency_streamer_ids,
# #         today,
# #     )

# #     gifts_yesterday_task = db.fetchrow(
# #         """
# #         SELECT
# #             COUNT(*) as gift_count,
# #             COALESCE(SUM(total_diamonds), 0) as diamond_total
# #         FROM gifts
# #         WHERE streamer_id = ANY($1)
# #         AND event_time >= $2 AND event_time < $3
# #         """,
# #         agency_streamer_ids,
# #         yesterday,
# #         today,
# #     )

# #     gifts_week_task = db.fetchrow(
# #         """
# #         SELECT
# #             COUNT(*) as gift_count,
# #             COALESCE(SUM(total_diamonds), 0) as diamond_total
# #         FROM gifts
# #         WHERE streamer_id = ANY($1)
# #         AND event_time >= $2
# #         """,
# #         agency_streamer_ids,
# #         week_start,
# #     )

# #     gifts_prev_week_task = db.fetchrow(
# #         """
# #         SELECT
# #             COUNT(*) as gift_count,
# #             COALESCE(SUM(total_diamonds), 0) as diamond_total
# #         FROM gifts
# #         WHERE streamer_id = ANY($1)
# #         AND event_time >= $2 AND event_time < $3
# #         """,
# #         agency_streamer_ids,
# #         prev_week_start,
# #         week_start,
# #     )

# #     gifts_month_task = db.fetchrow(
# #         """
# #         SELECT
# #             COUNT(*) as gift_count,
# #             COALESCE(SUM(total_diamonds), 0) as diamond_total
# #         FROM gifts
# #         WHERE streamer_id = ANY($1)
# #         AND event_time >= $2
# #         """,
# #         agency_streamer_ids,
# #         month_start,
# #     )

# #     gifts_prev_month_task = db.fetchrow(
# #         """
# #         SELECT
# #             COUNT(*) as gift_count,
# #             COALESCE(SUM(total_diamonds), 0) as diamond_total
# #         FROM gifts
# #         WHERE streamer_id = ANY($1)
# #         AND event_time >= $2 AND event_time < $3
# #         """,
# #         agency_streamer_ids,
# #         prev_month_start,
# #         month_start,
# #     )

# #     unique_donators_task = db.fetchval(
# #         """
# #         SELECT COUNT(DISTINCT unique_id)
# #         FROM gifts
# #         WHERE streamer_id = ANY($1)
# #         """,
# #         agency_streamer_ids,
# #     )

# #     unique_donators_week_task = db.fetchval(
# #         """
# #         SELECT COUNT(DISTINCT unique_id)
# #         FROM gifts
# #         WHERE streamer_id = ANY($1)
# #         AND event_time >= $2
# #         """,
# #         agency_streamer_ids,
# #         week_start,
# #     )

# #     unique_donators_prev_week_task = db.fetchval(
# #         """
# #         SELECT COUNT(DISTINCT unique_id)
# #         FROM gifts
# #         WHERE streamer_id = ANY($1)
# #         AND event_time >= $2 AND event_time < $3
# #         """,
# #         agency_streamer_ids,
# #         prev_week_start,
# #         week_start,
# #     )

# #     recent_gifts_task = db.fetch(
# #         """
# #         SELECT g.*, ttu.name as streamer_name, c.name as cluster_name
# #         FROM gifts g
# #         JOIN streamers s ON g.streamer_id = s.id
# #         JOIN tik_tok_users ttu ON s.tik_tok_user_id = ttu.id
# #         JOIN clusters c ON s.cluster_id = c.id
# #         WHERE g.streamer_id = ANY($1)
# #         ORDER BY g.event_time DESC
# #         LIMIT 20
# #         """,
# #         agency_streamer_ids,
# #     )

# #     total_streamers_task = db.fetchval("SELECT COUNT(*) FROM streamers")
# #     active_streamers_task = db.fetchval(
# #         "SELECT COUNT(*) FROM streamers WHERE status = 'Запущен'"
# #     )

# #     # Ждем выполнения всех запросов
# #     gifts_today = await gifts_today_task
# #     gifts_yesterday = await gifts_yesterday_task
# #     gifts_week = await gifts_week_task
# #     gifts_prev_week = await gifts_prev_week_task
# #     gifts_month = await gifts_month_task
# #     gifts_prev_month = await gifts_prev_month_task
# #     unique_donators = await unique_donators_task
# #     unique_donators_week = await unique_donators_week_task
# #     unique_donators_prev_week = await unique_donators_prev_week_task
# #     recent_gifts = await recent_gifts_task
# #     total_streamers = await total_streamers_task
# #     active_streamers = await active_streamers_task

# #     # Рассчитываем процентные изменения
# #     total_gifts_change = calculate_percentage_change(
# #         gifts_today["gift_count"], gifts_yesterday["gift_count"]
# #     )

# #     total_diamonds_change = calculate_percentage_change(
# #         gifts_today["diamond_total"], gifts_yesterday["diamond_total"]
# #     )

# #     total_dollars_today = gifts_today["diamond_total"] / 200
# #     total_dollars_yesterday = gifts_yesterday["diamond_total"] / 200

# #     total_dollars_change = calculate_percentage_change(
# #         total_dollars_today, total_dollars_yesterday
# #     )

# #     week_change = calculate_percentage_change(
# #         gifts_week["gift_count"], gifts_prev_week["gift_count"]
# #     )

# #     month_change = calculate_percentage_change(
# #         gifts_month["gift_count"], gifts_prev_month["gift_count"]
# #     )

# #     donators_change = calculate_percentage_change(
# #         unique_donators_week, unique_donators_prev_week
# #     )

# #     # Форматируем результаты для отправки на фронтенд
# #     result = {
# #         "total_gifts_today": gifts_today["gift_count"],
# #         "total_diamonds_today": gifts_today["diamond_total"],
# #         "total_dollars_today": total_dollars_today,
# #         "total_streamers": total_streamers,
# #         "tracked_streamers": active_streamers,
# #         "total_unique_donators": unique_donators,
# #         "last_week_gift": gifts_week["gift_count"],
# #         "last_month_gift": gifts_month["gift_count"],
# #         "donators_week": unique_donators_week,
# #         "donators_all": unique_donators,
# #         "count_all": total_streamers,
# #         "percent_total_gifts_today": total_gifts_change,
# #         "percent_total_diamonds": total_diamonds_change,
# #         "percent_total_dollars": total_dollars_change,
# #         "percent_week": week_change,
# #         "percent_month": month_change,
# #         "percent_donators": donators_change,
# #         "recent_gifts": [],
# #     }

# #     # Форматируем последние подарки
# #     for gift in recent_gifts:
# #         result["recent_gifts"].append(
# #             {
# #                 "id": gift["id"],
# #                 "uniqueId": gift["unique_id"],
# #                 "giftName": gift["gift_name"],
# #                 "diamondCount": gift["diamond_count"],
# #                 "event_time": gift["event_time"].isoformat(),
# #                 "giftCount": gift["gift_count"],
# #                 "receiverUniqueId": gift["streamer_name"],
# #                 "cluster": gift["cluster_name"],
# #             }
# #         )

# #     return result
# import logging
# from datetime import datetime, timedelta, timezone

# from database import db

# logger = logging.getLogger(__name__)


# def calculate_percentage_change(current, previous):
#     """Расчет процентного изменения между двумя значениями"""
#     if not previous or previous == 0:
#         return None

#     change = ((current - previous) / previous) * 100

#     if change > 0:
#         return f"↑ {change:.2f}%"
#     elif change < 0:
#         return f"↓ {abs(change):.2f}%"
#     else:
#         return "0%"


# async def get_dashboard_statistics():
#     """
#     Получение статистики для дашборда из предварительно рассчитанной таблицы
#     """
#     try:
#         # Get the most recent statistics entry
#         stats = await db.fetchrow(
#             """
#             SELECT * FROM dashboard_statistics
#             ORDER BY date_hour DESC
#             LIMIT 1
#             """
#         )

#         if not stats:
#             logger.warning("No statistics data available in dashboard_statistics table")
#             return {"error": "No statistics data available"}

#         # Calculate percentage changes
#         total_gifts_change = calculate_percentage_change(
#             stats["total_gifts_today"], stats["total_gifts_yesterday"]
#         )

#         total_diamonds_change = calculate_percentage_change(
#             stats["total_diamonds_today"], stats["total_diamonds_yesterday"]
#         )

#         total_dollars_change = calculate_percentage_change(
#             stats["total_dollars_today"], stats["total_dollars_yesterday"]
#         )

#         week_change = calculate_percentage_change(
#             stats["last_week_gifts"], stats["last_week_prev_gifts"]
#         )

#         month_change = calculate_percentage_change(
#             stats["last_month_gifts"], stats["last_month_prev_gifts"]
#         )

#         donators_change = calculate_percentage_change(
#             stats["unique_donators_week"], stats["unique_donators_prev_week"]
#         )

#         # Get recent gifts - this still needs to be fetched in real-time
#         recent_gifts = await get_recent_gifts()

#         # Format the results for the frontend
#         result = {
#             "total_gifts_today": stats["total_gifts_today"],
#             "total_diamonds_today": stats["total_diamonds_today"],
#             "total_dollars_today": stats["total_dollars_today"],
#             "total_streamers": stats["total_streamers"],
#             "tracked_streamers": stats["tracked_streamers"],
#             "total_unique_donators": stats["unique_donators_total"],
#             "last_week_gift": stats["last_week_gifts"],
#             "last_month_gift": stats["last_month_gifts"],
#             "donators_week": stats["unique_donators_week"],
#             "donators_all": stats["unique_donators_total"],
#             "count_all": stats["total_streamers"],
#             "percent_total_gifts_today": total_gifts_change,
#             "percent_total_diamonds": total_diamonds_change,
#             "percent_total_dollars": total_dollars_change,
#             "percent_week": week_change,
#             "percent_month": month_change,
#             "percent_donators": donators_change,
#             "recent_gifts": recent_gifts,
#         }

#         return result
#     except Exception as e:
#         logger.error(f"Error fetching dashboard statistics: {e}")
#         return {"error": str(e)}


# async def get_recent_gifts(limit=20):
#     """
#     Get recent gifts for real-time display
#     """
#     try:
#         # Get AGENCY cluster streamers
#         agency_streamers = await db.fetch(
#             """
#             SELECT s.id FROM streamers s
#             JOIN clusters c ON s.cluster_id = c.id
#             WHERE c.name = 'AGENCY'
#             """
#         )

#         agency_streamer_ids = [s["id"] for s in agency_streamers]

#         if not agency_streamer_ids:
#             return []

#         recent_gifts = await db.fetch(
#             """
#             SELECT g.*, ttu.name as streamer_name, c.name as cluster_name
#             FROM gifts g
#             JOIN streamers s ON g.streamer_id = s.id
#             JOIN tik_tok_users ttu ON s.tik_tok_user_id = ttu.id
#             JOIN clusters c ON s.cluster_id = c.id
#             WHERE g.streamer_id = ANY($1)
#             ORDER BY g.event_time DESC
#             LIMIT $2
#             """,
#             agency_streamer_ids,
#             limit,
#         )

#         # Format the gifts data
#         formatted_gifts = []
#         for gift in recent_gifts:
#             formatted_gifts.append(
#                 {
#                     "id": gift["id"],
#                     "uniqueId": gift["unique_id"],
#                     "giftName": gift["gift_name"],
#                     "diamondCount": gift["diamond_count"],
#                     "event_time": gift["event_time"].isoformat(),
#                     "giftCount": gift["gift_count"],
#                     "receiverUniqueId": gift["streamer_name"],
#                     "cluster": gift["cluster_name"],
#                 }
#             )

#         return formatted_gifts
#     except Exception as e:
#         logger.error(f"Error fetching recent gifts: {e}")
#         return []
# app/services/statistics.py
from datetime import datetime, timedelta, timezone

from database import db
from logger import logger


def calculate_percentage_change(current, previous):
    """Расчет процентного изменения между двумя значениями"""
    if not previous or previous == 0:
        return None

    change = ((current - previous) / previous) * 100

    if change > 0:
        return f"↑ {change:.2f}%"
    elif change < 0:
        return f"↓ {abs(change):.2f}%"
    else:
        return "0%"


async def get_dashboard_statistics():
    """
    Получение статистики для дашборда из предварительно рассчитанной таблицы
    """
    try:
        # Проверка подключения к базе данных
        if not db.pool:
            logger.error("Database connection not established")
            return get_default_statistics()

        # Получаем последнюю запись статистики
        stats = await db.fetchrow(
            """
            SELECT * FROM dashboard_statistics 
            ORDER BY date_hour DESC 
            LIMIT 1
            """
        )

        if not stats:
            logger.warning("No statistics found in dashboard_statistics table")
            return get_default_statistics()

        # Запрашиваем недавние подарки отдельным запросом
        recent_gifts = await get_recent_gifts()

        # Формируем результат
        result = {
            "total_gifts_today": stats["total_gifts_today"],
            "total_diamonds_today": stats["total_diamonds_today"],
            "total_dollars_today": float(stats["total_dollars_today"]),
            "total_gifts_yesterday": stats["total_gifts_yesterday"],
            "total_diamonds_yesterday": stats["total_diamonds_yesterday"],
            "total_dollars_yesterday": float(stats["total_dollars_yesterday"]),
            "last_week_gifts": stats["last_week_gifts"],
            "last_week_prev_gifts": stats["last_week_prev_gifts"],
            "last_month_gifts": stats["last_month_gifts"],
            "last_month_prev_gifts": stats["last_month_prev_gifts"],
            "unique_donators_total": stats["unique_donators_total"],
            "unique_donators_week": stats["unique_donators_week"],
            "unique_donators_prev_week": stats["unique_donators_prev_week"],
            "tracked_streamers": stats["tracked_streamers"],
            "total_streamers": stats["total_streamers"],
            "recent_gifts": recent_gifts,
            "last_updated": (
                stats["date_hour"].isoformat() if "date_hour" in stats else None
            ),
        }

        return result
    except Exception as e:
        logger.error(f"Error fetching dashboard statistics: {e}")
        return get_default_statistics()


def get_default_statistics():
    """Возвращает пустые значения статистики по умолчанию"""
    return {
        "total_gifts_today": 0,
        "total_diamonds_today": 0,
        "total_dollars_today": 0,
        "total_gifts_yesterday": 0,
        "total_diamonds_yesterday": 0,
        "total_dollars_yesterday": 0,
        "last_week_gifts": 0,
        "last_week_prev_gifts": 0,
        "last_month_gifts": 0,
        "last_month_prev_gifts": 0,
        "unique_donators_total": 0,
        "unique_donators_week": 0,
        "unique_donators_prev_week": 0,
        "tracked_streamers": 0,
        "total_streamers": 0,
        "recent_gifts": [],
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


async def get_recent_gifts(limit=20):
    """
    Получение списка последних подарков
    """
    try:
        if not db.pool:
            logger.error("Database connection not established")
            return []

        # Получаем стримеров из кластера AGENCY
        agency_streamers = await db.fetch(
            """
            SELECT s.id FROM streamers s
            JOIN clusters c ON s.cluster_id = c.id
            WHERE c.name = 'AGENCY'
            """
        )

        if not agency_streamers:
            logger.warning("No AGENCY streamers found")
            return []

        agency_streamer_ids = [s["id"] for s in agency_streamers]

        # Получаем последние подарки
        gifts = await db.fetch(
            """
            SELECT g.id, g.event_time, g.unique_id, g.user_id, g.gift_name, 
                g.gift_count, g.diamond_count, g.receiver_unique_id, 
                ttu.name as streamer_name, c.name as cluster_name
            FROM gifts g
            JOIN streamers s ON g.streamer_id = s.id
            JOIN tik_tok_users ttu ON s.tik_tok_user_id = ttu.id
            JOIN clusters c ON s.cluster_id = c.id
            WHERE g.streamer_id = ANY($1)
            ORDER BY g.event_time DESC
            LIMIT $2
            """,
            agency_streamer_ids,
            limit,
        )

        # Форматируем результат
        result = []
        for gift in gifts:
            result.append(
                {
                    "id": gift["id"],
                    "unique_id": gift["unique_id"],
                    "gift_name": gift["gift_name"],
                    "diamond_count": gift["diamond_count"],
                    "event_time": gift["event_time"].isoformat(),
                    "gift_count": gift["gift_count"],
                    "receiver_unique_id": gift["streamer_name"],
                    "cluster": gift["cluster_name"],
                }
            )

        return result
    except Exception as e:
        logger.error(f"Error fetching recent gifts: {e}")
        return []
