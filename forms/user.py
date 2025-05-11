import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
from sessions import SqlAlchemyBase
class User(SqlAlchemyBase):
    __tablename__ = 'users'
    id = sa.Column(sa.Integer, primary_key=True)
    name = sa.Column(sa.String)
    age = sa.Column(sa.Integer, nullable=True)
    email = sa.Column(sa.String)
    phone = sa.Column(sa.String)
    password = sa.Column(sa.String)


