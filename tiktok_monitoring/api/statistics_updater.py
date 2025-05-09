# # statistics_updater.py
# import asyncio
# from datetime import datetime, timedelta, timezone

# from database import db
# from logger import logger


# async def update_statistics_table():
#     """
#     Updates the dashboard_statistics table with the latest metrics.
#     This function should be called periodically (e.g., every 5 minutes)
#     """
#     try:
#         now = datetime.now(timezone.utc)
#         # Round to the nearest hour for storage
#         current_hour = now.replace(minute=0, second=0, microsecond=0)
#         today = now.replace(hour=0, minute=0, second=0, microsecond=0)
#         yesterday = today - timedelta(days=1)
#         week_start = today - timedelta(days=today.weekday())
#         prev_week_start = week_start - timedelta(days=7)
#         month_start = today.replace(day=1)
#         prev_month_start = (month_start - timedelta(days=1)).replace(day=1)

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
#             logger.warning("No AGENCY streamers found for statistics update")
#             return

#         # Run parallel queries for efficiency
#         gifts_today_task = db.fetchrow(
#             """
#             SELECT
#                 COUNT(*) as gift_count,
#                 COALESCE(SUM(total_diamonds), 0) as diamond_total
#             FROM gifts
#             WHERE streamer_id = ANY($1)
#             AND event_time >= $2
#             """,
#             agency_streamer_ids,
#             today,
#         )

#         gifts_yesterday_task = db.fetchrow(
#             """
#             SELECT
#                 COUNT(*) as gift_count,
#                 COALESCE(SUM(total_diamonds), 0) as diamond_total
#             FROM gifts
#             WHERE streamer_id = ANY($1)
#             AND event_time >= $2 AND event_time < $3
#             """,
#             agency_streamer_ids,
#             yesterday,
#             today,
#         )

#         gifts_week_task = db.fetchrow(
#             """
#             SELECT
#                 COUNT(*) as gift_count,
#                 COALESCE(SUM(total_diamonds), 0) as diamond_total
#             FROM gifts
#             WHERE streamer_id = ANY($1)
#             AND event_time >= $2
#             """,
#             agency_streamer_ids,
#             week_start,
#         )

#         gifts_prev_week_task = db.fetchrow(
#             """
#             SELECT
#                 COUNT(*) as gift_count,
#                 COALESCE(SUM(total_diamonds), 0) as diamond_total
#             FROM gifts
#             WHERE streamer_id = ANY($1)
#             AND event_time >= $2 AND event_time < $3
#             """,
#             agency_streamer_ids,
#             prev_week_start,
#             week_start,
#         )

#         gifts_month_task = db.fetchrow(
#             """
#             SELECT
#                 COUNT(*) as gift_count,
#                 COALESCE(SUM(total_diamonds), 0) as diamond_total
#             FROM gifts
#             WHERE streamer_id = ANY($1)
#             AND event_time >= $2
#             """,
#             agency_streamer_ids,
#             month_start,
#         )

#         gifts_prev_month_task = db.fetchrow(
#             """
#             SELECT
#                 COUNT(*) as gift_count,
#                 COALESCE(SUM(total_diamonds), 0) as diamond_total
#             FROM gifts
#             WHERE streamer_id = ANY($1)
#             AND event_time >= $2 AND event_time < $3
#             """,
#             agency_streamer_ids,
#             prev_month_start,
#             month_start,
#         )

#         unique_donators_task = db.fetchval(
#             """
#             SELECT COUNT(DISTINCT unique_id)
#             FROM gifts
#             WHERE streamer_id = ANY($1)
#             """,
#             agency_streamer_ids,
#         )

#         unique_donators_week_task = db.fetchval(
#             """
#             SELECT COUNT(DISTINCT unique_id)
#             FROM gifts
#             WHERE streamer_id = ANY($1)
#             AND event_time >= $2
#             """,
#             agency_streamer_ids,
#             week_start,
#         )

#         unique_donators_prev_week_task = db.fetchval(
#             """
#             SELECT COUNT(DISTINCT unique_id)
#             FROM gifts
#             WHERE streamer_id = ANY($1)
#             AND event_time >= $2 AND event_time < $3
#             """,
#             agency_streamer_ids,
#             prev_week_start,
#             week_start,
#         )

#         total_streamers_task = db.fetchval("SELECT COUNT(*) FROM streamers")
#         active_streamers_task = db.fetchval(
#             "SELECT COUNT(*) FROM streamers WHERE status = 'Запущен'"
#         )

#         # Wait for all queries to complete
#         gifts_today = await gifts_today_task
#         gifts_yesterday = await gifts_yesterday_task
#         gifts_week = await gifts_week_task
#         gifts_prev_week = await gifts_prev_week_task
#         gifts_month = await gifts_month_task
#         gifts_prev_month = await gifts_prev_month_task
#         unique_donators = await unique_donators_task
#         unique_donators_week = await unique_donators_week_task
#         unique_donators_prev_week = await unique_donators_prev_week_task
#         total_streamers = await total_streamers_task
#         active_streamers = await active_streamers_task

#         # Calculate dollar values
#         total_dollars_today = gifts_today["diamond_total"] / 200
#         total_dollars_yesterday = gifts_yesterday["diamond_total"] / 200

#         # Insert or update statistics in the dashboard_statistics table
#         await db.execute(
#             """
#             INSERT INTO dashboard_statistics (
#                 date_hour,
#                 total_gifts_today,
#                 total_diamonds_today,
#                 total_dollars_today,
#                 total_gifts_yesterday,
#                 total_diamonds_yesterday,
#                 total_dollars_yesterday,
#                 last_week_gifts,
#                 last_week_prev_gifts,
#                 last_month_gifts,
#                 last_month_prev_gifts,
#                 unique_donators_total,
#                 unique_donators_week,
#                 unique_donators_prev_week,
#                 tracked_streamers,
#                 total_streamers
#             ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
#             ON CONFLICT (date_hour)
#             DO UPDATE SET
#                 total_gifts_today = $2,
#                 total_diamonds_today = $3,
#                 total_dollars_today = $4,
#                 total_gifts_yesterday = $5,
#                 total_diamonds_yesterday = $6,
#                 total_dollars_yesterday = $7,
#                 last_week_gifts = $8,
#                 last_week_prev_gifts = $9,
#                 last_month_gifts = $10,
#                 last_month_prev_gifts = $11,
#                 unique_donators_total = $12,
#                 unique_donators_week = $13,
#                 unique_donators_prev_week = $14,
#                 tracked_streamers = $15,
#                 total_streamers = $16
#             """,
#             current_hour,
#             gifts_today["gift_count"],
#             gifts_today["diamond_total"],
#             total_dollars_today,
#             gifts_yesterday["gift_count"],
#             gifts_yesterday["diamond_total"],
#             total_dollars_yesterday,
#             gifts_week["gift_count"],
#             gifts_prev_week["gift_count"],
#             gifts_month["gift_count"],
#             gifts_prev_month["gift_count"],
#             unique_donators,
#             unique_donators_week,
#             unique_donators_prev_week,
#             active_streamers,
#             total_streamers,
#         )

#         logger.info(f"Dashboard statistics updated for {current_hour}")
#     except Exception as e:
#         logger.error(f"Error updating dashboard statistics: {e}")


# async def run_statistics_updater():
#     """
#     Main function to run the statistics updater at regular intervals
#     """
#     while True:
#         try:
#             await update_statistics_table()
#             # Run every 5 minutes
#             await asyncio.sleep(300)
#         except Exception as e:
#             logger.error(f"Error in statistics updater: {e}")
#             # Still wait before trying again
#             await asyncio.sleep(60)

# app/statistics_updater.py
import asyncio

import asyncpg
from config import settings
from logger import logger


async def refresh_stats():
    try:
        conn = await asyncpg.connect(
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB,
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
        )
        await conn.execute("SELECT refresh_dashboard_statistics();")
        await conn.close()
        logger.info("Statistics refreshed")
    except Exception as e:
        logger.error(f"Error refreshing statistics: {e}")


async def listen_for_stats_updates():
    try:
        conn = await asyncpg.connect(
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB,
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
        )

        async def handle_notification(*args):
            logger.info("Received pg_notify for statistics update")
            await refresh_stats()

        await conn.add_listener("refresh_statistics", handle_notification)
        logger.info("Started listening for PostgreSQL notifications")
        while True:
            await asyncio.sleep(3600)  # Держим соединение открытым
    except Exception as e:
        logger.error(f"Error in listener: {e}")
        await conn.close()


async def run_statistics_updater():
    # Запускаем слушатель уведомлений
    listener_task = asyncio.create_task(listen_for_stats_updates())

    # Периодическое обновление каждые 5 секунд
    while True:
        await refresh_stats()
        await asyncio.sleep(5)  # Интервал 5 секунд

    # Отменяем слушатель при завершении
    listener_task.cancel()
