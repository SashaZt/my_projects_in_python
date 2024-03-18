# database_operations.py
import csv
from datetime import date

from sqlalchemy.orm import Session

from models import ColdCall


def get_all_data(db: Session):
    return db.query(ColdCall).all()


async def upload_data_from_file(db: Session, file):
    content = await file.read()
    content = content.decode()
    lines = content.split('\n')
    reader = csv.reader(lines)
    added_count = 0
    invalid_numbers = []
    for row in reader:
        nomer = row[0]
        if not (nomer.isdigit() and len(nomer) == 10):
            invalid_numbers.append(nomer)
            continue
        existing_call = db.query(ColdCall).filter(ColdCall.nomer == nomer).first()
        if not existing_call:
            new_call = ColdCall(nomer=nomer, date_of_creation=date.today())
            db.add(new_call)
            added_count += 1
    db.commit()
    await file.close()
    return added_count, invalid_numbers


def create_new_cold_call(db: Session, cold_call_data):
    new_cold_call = ColdCall(**cold_call_data.dict())
    db.add(new_cold_call)
    db.commit()
    db.refresh(new_cold_call)
    return new_cold_call
