from datetime import datetime

import sqlalchemy as sa
import sqlalchemy.orm as orm
from sessions import SqlAlchemyBase





class Task(SqlAlchemyBase):
    __tablename__ = 'tasks'
    
    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'))
    time = sa.Column(sa.String)
    text = sa.Column(sa.String)
    created_at = sa.Column(sa.DateTime, default=datetime.now)
