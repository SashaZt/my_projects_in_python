import pytest
import pytest_asyncio
from database import DatabaseInitializer


@pytest_asyncio.fixture
async def db_initializer():
    db = DatabaseInitializer()
    await db.create_database()
    await db.create_pool()
    yield db
    await db.close_pool()


@pytest.mark.asyncio
async def test_create_database(db_initializer):
    # Проверяем, что база данных была создана
    assert db_initializer.pool is not None


@pytest.mark.asyncio
async def test_insert_contact(db_initializer):
    # Пример данных для вставки
    contact_data = {"name": "John", "surname": "Doe", "formal_title": "Mr."}
    success = await db_initializer.insert_contact(contact_data)
    assert success is True


@pytest.mark.asyncio
async def test_get_all_contact_data(db_initializer):
    # Тестируем получение данных из базы
    result = await db_initializer.get_all_contact_data()
    assert isinstance(result, list)


# Дополнительные тесты для других функций
