# app/services/olx_message_service.py

from sqlalchemy.ext.asyncio import AsyncSession
import httpx
from typing import Optional, List, Dict, Any
from loguru import logger
from app.schemas.olx_messages import Thread, Message, MessageCreate

from app.services.olx_service import OLXService

class OLXMessageService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.olx_service = OLXService(db)
        self.base_url = "https://www.olx.ua/api/partner"

    async def _get_headers(self) -> Dict[str, str]:
        """Получить заголовки для запроса с актуальным токеном"""
        access_token = await self.olx_service.get_valid_token()
        if not access_token:
            raise Exception("No valid token found")
        
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Version": "2.0",
            "Host": "www.olx.ua"
        }

    async def get_threads(self, advert_id: Optional[int] = None, 
                         interlocutor_id: Optional[int] = None,
                         offset: Optional[int] = None,
                         limit: Optional[int] = None) -> List[Thread]:
        """Получить список диалогов"""
        try:
            headers = await self._get_headers()
            params = {}
            if advert_id:
                params['advert_id'] = advert_id
            if interlocutor_id:
                params['interlocutor_id'] = interlocutor_id
            if offset:
                params['offset'] = offset
            if limit:
                params['limit'] = limit

            logger.debug(f"Sending request to {self.base_url}/threads with headers: {headers}")

            async with httpx.AsyncClient(verify=False) as client:
                response = await client.get(
                    f"{self.base_url}/threads",
                    headers=headers,
                    params=params,
                    timeout=30.0
                )
                
                logger.debug(f"Response status: {response.status_code}")
                logger.debug(f"Response headers: {response.headers}")
                logger.debug(f"Response content: {response.text}")

                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict) and 'data' in data:
                        threads_data = data['data']
                    else:
                        threads_data = data
                    return [Thread(**thread) for thread in threads_data]
                else:
                    logger.error(f"Error getting threads: {response.text}")
                    return []

        except Exception as e:
            logger.error(f"Error in get_threads: {str(e)}", exc_info=True)
            raise

    async def get_thread(self, thread_id: int) -> Optional[Thread]:
        """Получить информацию о конкретном диалоге"""
        try:
            headers = await self._get_headers()
            
            logger.debug(f"Getting thread {thread_id}")
            
            async with httpx.AsyncClient(verify=False) as client:
                response = await client.get(
                    f"{self.base_url}/threads/{thread_id}",
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict) and 'data' in data:
                        return Thread(**data['data'])
                    return Thread(**data)
                else:
                    logger.error(f"Error getting thread: {response.text}")
                    return None

        except Exception as e:
            logger.error(f"Error in get_thread: {str(e)}", exc_info=True)
            raise

    async def get_messages(self, thread_id: int, 
                          offset: Optional[int] = None,
                          limit: Optional[int] = None) -> List[Message]:
        """Получить сообщения из диалога"""
        try:
            headers = await self._get_headers()
            params = {}
            if offset:
                params['offset'] = offset
            if limit:
                params['limit'] = limit

            logger.debug(f"Getting messages for thread {thread_id}")

            async with httpx.AsyncClient(verify=False) as client:
                response = await client.get(
                    f"{self.base_url}/threads/{thread_id}/messages",
                    headers=headers,
                    params=params,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict) and 'data' in data:
                        messages_data = data['data']
                    else:
                        messages_data = data
                    return [Message(**msg) for msg in messages_data]
                else:
                    logger.error(f"Error getting messages: {response.text}")
                    return []

        except Exception as e:
            logger.error(f"Error in get_messages: {str(e)}", exc_info=True)
            raise

    async def send_message(self, thread_id: int, message: MessageCreate) -> Optional[Message]:
        """Отправить сообщение в диалог"""
        try:
            headers = await self._get_headers()
            
            logger.debug(f"Sending message to thread {thread_id}: {message.model_dump()}")

            async with httpx.AsyncClient(verify=False) as client:
                response = await client.post(
                    f"{self.base_url}/threads/{thread_id}/messages",
                    headers=headers,
                    json=message.model_dump(exclude_none=True),
                    timeout=30.0
                )
                
                logger.debug(f"Send message response status: {response.status_code}")
                logger.debug(f"Send message response body: {response.text}")
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict) and 'data' in data:
                        return Message(**data['data'])
                    return Message(**data)
                else:
                    logger.error(f"Error sending message: {response.text}")
                    return None

        except Exception as e:
            logger.error(f"Error in send_message: {str(e)}", exc_info=True)
            raise

    async def thread_action(self, thread_id: int, command: str, is_favourite: Optional[bool] = None) -> bool:
        """Выполнить действие с диалогом (пометить как прочитанное или избранное)"""
        try:
            headers = await self._get_headers()
            data = {"command": command}
            if is_favourite is not None:
                data["is_favourite"] = is_favourite

            logger.debug(f"Executing action {command} on thread {thread_id}")

            async with httpx.AsyncClient(verify=False) as client:
                response = await client.post(
                    f"{self.base_url}/threads/{thread_id}/commands",
                    headers=headers,
                    json=data,
                    timeout=30.0
                )
                
                return response.status_code == 204

        except Exception as e:
            logger.error(f"Error in thread_action: {str(e)}", exc_info=True)
            raise