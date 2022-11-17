
import sys
sys.path.append("..")

from starlette.responses import RedirectResponse
from typing import Optional
from fastapi import Depends, Form, HTTPException, Response, status, APIRouter, Request
from pydantic import BaseModel
import models as models
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from database import sessionLocal, engine
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import datetime, timedelta
from jose import jwt, JWTError

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


SECRET_KEY = 'ridwanulhoquejr@2866'
ALGORITHM = 'HS256'


templates = Jinja2Templates(directory="templates")


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

models.Base.metadata.create_all(bind=engine)

oauth2_bearer = OAuth2PasswordBearer(tokenUrl='token')


router = APIRouter(
    prefix="/auth",
    tags=['auth'],
    responses={401: {'user': 'Not authorized'}}
)


# login form for HTML form
class LoginForm:

    def __init__(self, request: Request):
        self.request: Request = request
        self.username: Optional[str] = None
        self.password: Optional[str] = None


    async def create_oauth_form(self):
        form = await self.request.form()
        self.username = form.get('email')
        self.password = form.get('password')


def get_db():
    try:
        db = sessionLocal()
        yield db
    finally:
        db.close()

def get_hashed_password(password):
    return bcrypt_context.hash(password)

def verify_password(plain_password, hashed_password):
    return bcrypt_context.verify(plain_password, hashed_password)


# Authenticate user
def authenticate_user(username: str, password: str, db):
    user = db.query(models.Users).filter(models.Users.username == username).first()

    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


# JWT access token
def create_access_token(username: str,
                        user_id: int,
                        expires_delta: Optional[timedelta] = None):

    encode = {'sub': username, 'id': user_id }

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    encode.update({'exp': expire})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)



# --------- HTML API's ------------- #

@router.get('/', response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse('login.html', {'request': request})


# LoginForm handleling
@router.post('/', response_class=HTMLResponse)
async def login(request: Request, db: Session = Depends(get_db)):

    try:
        print('im in try block of login_func')
        form = LoginForm(request)
        await form.create_oauth_form()
        response = RedirectResponse(url='/todos', status_code=status.HTTP_302_FOUND)
        validate_user_cookie = await login_for_access_token(response=response, form_data=form, db=db)

        if not validate_user_cookie:
            print('im in try block of not validate')
            msg = ' Incorrect username or password'
            return templates.TemplateResponse('login.html', {'request': request, 'msg': msg})

        print('todos_page response is returned succesfully')
        return response

    except HTTPException:
        print('im in except block of login_func')
        msg = 'Unkown error'
        return templates.TemplateResponse('login.hotml', {'request': request, 'msg': msg})


# Logout
@router.get('/logout', response_class=HTMLResponse)
async def logout(request: Request):

    msg = 'User logged out'
    response = templates.TemplateResponse('login.html', {'request': request, 'msg': msg})
    response.delete_cookie(key='access_token')
    return response


# Register an account
@router.get('/register', response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse('register.html', {'request': request})


@router.post('/register', response_class=HTMLResponse)
async def create_an_account(request: Request, email: str = Form(...), username: str = Form(...),
                            firstname: str = Form(...), lastname: str = Form(...),
                            password: str = Form(...), password2: str = Form(...),
                            db: Session = Depends(get_db)):
    
    validation1 = db.query(models.Users).filter(models.Users.username == username).first()

    validation2 = db.query(models.Users).filter(models.Users.email == email).first()

    if password != password2 or validation1 is not None or validation2 is not None:
        msg = 'Invalid registration request'
        return templates.TemplateResponse('/register.html', {'request': request, 'msg': msg})

    user_object = models.Users()     # instance of models.Users, which is DB table of users
    user_object.username = username
    user_object.email = email
    user_object.firstname = firstname
    user_object.lastname = lastname
    #user_object.phone_number = phone
    user_object.is_active = True

    encrypted_password = get_hashed_password(password)
    user_object.hashed_password = encrypted_password

    db.add(user_object)
    db.commit()
    msg = 'User succesfully created'

    return templates.TemplateResponse('/login.html', {'request': request, 'msg': msg})


# Current user
async def get_current_user(request: Request):

    """
    This function will decode the JWT token, i:e, jwt header, payload
    then it will check the DB and return the username and ID
    """

    try:
        token = request.cookies.get('access_token')
        if token is None:
            return None
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: str = payload.get('id')

        if username is None or user_id is None:
            logout(request)

        return {'username': username, 'id': user_id}

    except JWTError:
        raise get_user_exception()


# Access token, POST request
@router.post('/token')
async def login_for_access_token(response: Response, form_data: OAuth2PasswordRequestForm = Depends(),
                                 db: Session = Depends(get_db)):
    print('im in login_for_acces_token block')
    user = authenticate_user(form_data.username, form_data.password, db)
    print('im in login_for_acces_token and user is authenticated')

    if not user:
        return False
    token_expires = timedelta(minutes=60)
    token = create_access_token(user.username,
                                user.id,
                                expires_delta=token_expires)

    response.set_cookie(key='access_token', value=token, httponly=True)
    return True


# Exceptions_handling
def get_user_exception():

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'}
    )
    return credentials_exception


def token_exception():

    token_exception_response = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Incorrect username or password',
        headers={'WWW-Authenticate': 'Bearer'}
    )
    return token_exception_response