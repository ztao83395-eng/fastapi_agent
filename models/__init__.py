from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from .news import News, Category
from .users import User, UserToken
from .favorite import Favorite
from .history import History
