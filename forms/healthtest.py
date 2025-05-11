import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
from datetime import datetime

from sessions import SqlAlchemyBase


class HealthTest(SqlAlchemyBase):
    __tablename__ = 'health_tests'
    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'))
    test_type = sa.Column(sa.String)
    result = sa.Column(sa.String)
    created_at = sa.Column(sa.DateTime, default=datetime.now)