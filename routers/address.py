import sys
sys.path.append('..')

from typing import Optional
from fastapi import Depends, APIRouter
import models as models
from database import sessionLocal, engine
from sqlalchemy.orm import Session
from pydantic import BaseModel
from routers.auth import get_user_exception, get_current_user


router = APIRouter(
    prefix='/address',
    tags=['address'],
    responses={404: {'description': "Not found"}}
)


def get_db():
    try:
        db = sessionLocal()
        yield db
    finally:
        db.close()


class AddressModel(BaseModel):

    address1: str
    address2: Optional[str]
    country: str
    city: str
    state: str
    zipcode: str
    apt_num: Optional[int]


@router.post('/')
async def add_address(address: AddressModel,
                    user: dict=Depends(get_current_user),
                    db: Session = Depends(get_db)):
    
    if user is None:
        raise get_user_exception()
    
    address_model = models.Address()
    address_model.address1 = address.address1
    address_model.address2 = address.address2
    address_model.city = address.city
    address_model.country = address.country
    address_model.state = address.state
    address_model.zipcode = address.zipcode
    address_model.apt_num = address.apt_num

    db.add(address_model)
    db.flush()

    # this is how Foreign Key is filled up
    user_model = db.query(models.Users).filter(models.Users.id == user.get('id')).first()
    user_model.address_id = address_model.id

    db.add(user_model)
    db.commit()