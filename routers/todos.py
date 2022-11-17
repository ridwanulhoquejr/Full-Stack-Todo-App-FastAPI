import sys
sys.path.append("..")

from starlette import status
from starlette.responses import RedirectResponse
from fastapi import Depends, APIRouter, Request, Form
import models
from database import engine, sessionLocal
from sqlalchemy.orm import Session
from routers.auth import get_current_user
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


router = APIRouter(
    prefix='/todos',
    tags=['todos'],
    responses={404:{'description':'Not found'}}
)

models.Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory='templates')


def get_db():
    try:
        db = sessionLocal()
        yield db
    finally:
        db.close()



# --------------------- HTML Response API's --------------------#

@router.get('/', response_class=HTMLResponse)
async def read_all_by_user(request: Request, db: Session = Depends(get_db)):

    # get the current_user
    user = await get_current_user(request)

    # if user is not logged in -> send back to login page
    if user is None:
        return RedirectResponse(url='/auth', status_code=status.HTTP_302_FOUND)

    # if user is looged in -> send back to the todos i:e Home page
    todos = db.query(models.Todo).filter(models.Todo.owner_id == user.get('id')).all()
    
    print('im in read_all_by_user and user todos is returned')
    return templates.TemplateResponse("home.html", {'request': request, 'todos': todos, 'user': user})


@router.get('/add-todo', response_class=HTMLResponse)
async def add_new_todo(request: Request):

    # get the current_user
    user = await get_current_user(request)

    # if user is not logged in -> send back to login page
    if user is None:
        return RedirectResponse(url='/auth', status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("add-todo.html", {'request': request, 'user': user})


@router.post('/add-todo', response_class=HTMLResponse)
async def create_todo(  
                        request: Request, 
                        title: str = Form(...),
                        description: str = Form(...), 
                        priority: int = Form(...),
                        db: Session = Depends(get_db)
                    ):
    # get the current_user
    user = await get_current_user(request)

    # if user is not logged in -> send back to login page
    if user is None:
        return RedirectResponse(url='/auth', status_code=status.HTTP_302_FOUND)
    
    todo_model = models.Todo()
    todo_model.title = title
    todo_model.description = description
    todo_model.priority = priority
    todo_model.complete = False
    todo_model.owner_id = user.get('id')
    db.add(todo_model)
    db.commit()

    return RedirectResponse(url='/todos', status_code=status.HTTP_302_FOUND)



@router.get('/edit-todo/{todo_id}',response_class=HTMLResponse)
async def edit_todo(request: Request, todo_id: int, db: Session = Depends(get_db)):

    # get the current_user
    user = await get_current_user(request)

    # if user is not logged in -> send back to login page
    if user is None:
        return RedirectResponse(url='/auth', status_code=status.HTTP_302_FOUND)

    # grab the todo with id, pass this as a contex in HtmlTemplates
    todo = db.query(models.Todo).filter(models.Todo.id == todo_id).first()

    return templates.TemplateResponse("edit-todo.html", {'request': request, 'todo': todo, 'user': user})


@router.post('/edit-todo/{todo_id}', response_class=HTMLResponse)
async def edit_todo_commit(request: Request, todo_id: int, 
                            title: str = Form(...),
                            description: str = Form(...),
                            priority: int = Form(...),
                            db: Session = Depends(get_db)):

    # get the current_user
    user = await get_current_user(request)

    # if user is not logged in -> send back to login page
    if user is None:
        return RedirectResponse(url='/auth', status_code=status.HTTP_302_FOUND)
    
    todo_model = db.query(models.Todo).filter(models.Todo.id == todo_id).first()
    todo_model.title = title
    todo_model.description = description
    todo_model.priority = priority

    db.add(todo_model)
    db.commit()

    return RedirectResponse(url='/todos', status_code=status.HTTP_302_FOUND)

# delete a todo by an id
@router.get('/delete/{todo_id}', response_class=HTMLResponse)
async def delete_todo(todo_id: int, request: Request, db: Session = Depends(get_db)):

    # get the current_user
    user = await get_current_user(request)

    # if user is not logged in -> send back to login page
    if user is None:
        return RedirectResponse(url='/auth', status_code=status.HTTP_302_FOUND)
    
    todo_model = db.query(models.Todo).filter(models.Todo.id == todo_id).filter(models.Todo.owner_id == user.get('id')).first()
    if todo_model is None:
        return RedirectResponse(url='/todos', status_code=status.HTTP_302_FOUND)

    db.query(models.Todo).filter(models.Todo.id == todo_id).delete()
    db.commit()

    return RedirectResponse(url='/todos', status_code=status.HTTP_302_FOUND)


# COmplete a Todo
@router.get('/complete/{todo_id}', response_class=HTMLResponse)
async def complete_todo(todo_id: int, request: Request, db: Session = Depends(get_db)):

    # get the current_user
    user = await get_current_user(request)

    # if user is not logged in -> send back to login page
    if user is None:
        return RedirectResponse(url='/auth', status_code=status.HTTP_302_FOUND)

    todo = db.query(models.Todo).filter(models.Todo.id == todo_id).first()
    todo.complete = not todo.complete
    db.add(todo)
    db.commit()

    return RedirectResponse(url='/todos', status_code=status.HTTP_302_FOUND)
