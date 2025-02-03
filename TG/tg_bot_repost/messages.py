import asyncio
import random
from datetime import datetime, timezone

from config import API_HASH, API_ID, TIME_A, TIME_B, logger
from database import RepostMessage, async_session
from sqlalchemy.future import select
from telethon.sync import TelegramClient


async def fetch_pending_messages(category: str, limit: int):
    async with async_session() as session:
        result = await session.execute(
            select(RepostMessage.message_id)
            .where(RepostMessage.category == category, RepostMessage.repost == False)
            .limit(limit)
        )
        return result.scalars().all()


async def update_reposted_messages(message_ids):
    async with async_session() as session:
        await session.execute(
            update(RepostMessage)
            .where(RepostMessage.message_id.in_(message_ids))
            .values(repost=True, reposted_at=datetime.now(timezone.utc))
        )
        await session.commit()


async def get_and_forward_messages(category: str, limit: int):
    phone_number, session_name = get_session_name()
    async with TelegramClient(session_name, API_ID, API_HASH) as client:
        await client.start(phone_number)
        success_ids = []
        message_ids = await fetch_pending_messages(category, limit)

        for msg_id in message_ids:
            await client.forward_messages(
                "TO_CHANNEL", msg_id, from_peer="FROM_CHANNEL"
            )
            success_ids.append(msg_id)
            await asyncio.sleep(random.uniform(TIME_A, TIME_B))

        if success_ids:
            await update_reposted_messages(success_ids)
