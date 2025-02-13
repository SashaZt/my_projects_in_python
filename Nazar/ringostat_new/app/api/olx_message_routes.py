# app/api/olx_message_routes.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db
from app.services.olx_message_service import OLXMessageService
from app.schemas.olx_messages import MessageCreate, Thread, Message
from typing import List, Optional
from loguru import logger

router = APIRouter(prefix="/olx/messages", tags=["olx-messages"])

@router.get("/threads", response_model=List[Thread])
async def get_threads(
    advert_id: Optional[int] = None,
    interlocutor_id: Optional[int] = None,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Получить список диалогов"""
    try:
        service = OLXMessageService(db)
        threads = await service.get_threads(
            advert_id=advert_id,
            interlocutor_id=interlocutor_id,
            offset=offset,
            limit=limit
        )
        return threads
    except Exception as e:
        logger.error(f"Error getting threads: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/threads/{thread_id}", response_model=Thread)
async def get_thread(thread_id: int, db: AsyncSession = Depends(get_db)):
    """Получить информацию о конкретном диалоге"""
    try:
        service = OLXMessageService(db)
        thread = await service.get_thread(thread_id)
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        return thread
    except Exception as e:
        logger.error(f"Error getting thread: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/threads/{thread_id}/messages", response_model=List[Message])
async def get_messages(
    thread_id: int,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """Получить сообщения из диалога"""
    try:
        service = OLXMessageService(db)
        messages = await service.get_messages(
            thread_id=thread_id,
            offset=offset,
            limit=limit
        )
        return messages
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/threads/{thread_id}/messages", response_model=Message)
async def send_message(
    thread_id: int,
    message: MessageCreate,
    db: AsyncSession = Depends(get_db)
):
    """Отправить сообщение в диалог"""
    try:
        service = OLXMessageService(db)
        sent_message = await service.send_message(thread_id, message)
        if not sent_message:
            raise HTTPException(status_code=400, detail="Failed to send message")
        return sent_message
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/threads/{thread_id}/action")
async def thread_action(
    thread_id: int,
    command: str,
    is_favourite: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """Выполнить действие с диалогом"""
    try:
        if command not in ["mark-as-read", "set-favourite"]:
            raise HTTPException(status_code=400, detail="Invalid command")
        
        service = OLXMessageService(db)
        success = await service.thread_action(thread_id, command, is_favourite)
        if not success:
            raise HTTPException(status_code=400, detail="Failed to execute action")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error executing thread action: {e}")
        raise HTTPException(status_code=500, detail=str(e))