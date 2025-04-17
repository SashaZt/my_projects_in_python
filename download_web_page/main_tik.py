import httpx
from bs4 import BeautifulSoup


async def get_user_id_from_mediamister(unique_id):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"https://www.mediamister.com/find-tiktok-user-id?username={unique_id.lstrip('@')}"
            )
            soup = BeautifulSoup(response.text, "html.parser")
            user_id_element = soup.select_one(
                ".user-id-selector"
            )  # Замените на реальный CSS-селектор
            if user_id_element:
                return user_id_element.text.strip()
            return None
        except Exception as e:
            logger.error(
                f"Error fetching user_id from MediaMister for {unique_id}: {e}"
            )
            return None
