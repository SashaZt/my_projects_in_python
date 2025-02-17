#app/api/endpoints/transfer.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from crud.transfer import (
    get_transfer,
    get_transfers,
    create_transfer,
    update_transfer,
    delete_transfer,
    get_transfer_by_transfer_id
)
from schemas.transfer import Transfer, TransferCreate
from core.dependencies import get_db
from core.logger import logger

router = APIRouter(prefix="/transfer", tags=["transfer"])


@router.get("/", response_model=list[Transfer])
async def read_transfers(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    logger.debug(f"Запрос списка трансферов: skip={skip}, limit={limit}")
    transfers = await get_transfers(db, skip=skip, limit=limit)
    logger.info(f"Получено {len(transfers)} трансферов")
    return transfers


@router.get("/{transfer_id}", response_model=Transfer)
async def read_transfer(transfer_id: int, db: AsyncSession = Depends(get_db)):
    logger.debug(f"Запрос трансфера с id={transfer_id}")
    transfer = await get_transfer(db, transfer_id)
    if transfer is None:
        logger.warning(f"Трансфер с id={transfer_id} не найден")
        raise HTTPException(status_code=404, detail="Трансфер не найден")
    logger.info(f"Трансфер с id={transfer_id} успешно найден")
    return transfer


@router.post("/", response_model=Transfer, status_code=status.HTTP_201_CREATED)
async def create_new_transfer(transfer: TransferCreate, db: AsyncSession = Depends(get_db)):
    logger.debug(f"Создание/обновление трансфера с данными: {transfer.dict()}")
    existing = await get_transfer_by_transfer_id(db, transfer.transfer_id)
    new_transfer = await create_transfer(db, transfer)
    
    # Возвращаем разные статус коды для создания и обновления
    if existing:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=jsonable_encoder(new_transfer)
        )
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=jsonable_encoder(new_transfer)
    )


@router.put("/{transfer_id}", response_model=Transfer)
async def update_existing_transfer(
    transfer_id: int, transfer: TransferCreate, db: AsyncSession = Depends(get_db)
):
    logger.debug(
        f"Обновление трансфера с id={transfer_id} с данными: {transfer.dict(exclude_unset=True)}"
    )
    updated_transfer = await update_transfer(db, transfer_id, transfer)
    if updated_transfer is None:
        logger.warning(f"Трансфер с id={transfer_id} для обновления не найден")
        raise HTTPException(status_code=404, detail="Трансфер не найден")
    logger.info(f"Трансфер с id={transfer_id} успешно обновлён")
    return updated_transfer


@router.delete("/{transfer_id}", response_model=dict)
async def delete_existing_transfer(
    transfer_id: int, db: AsyncSession = Depends(get_db)
):
    logger.debug(f"Удаление трансфера с id={transfer_id}")
    success = await delete_transfer(db, transfer_id)
    if not success:
        logger.warning(f"Трансфер с id={transfer_id} для удаления не найден")
        raise HTTPException(status_code=404, detail="Трансфер не найден")
    logger.info(f"Трансфер с id={transfer_id} успешно удалён")
    return {"detail": "Трансфер успешно удалён"}
