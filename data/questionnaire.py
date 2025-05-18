from datetime import datetime

import sqlalchemy as sa
import sqlalchemy.orm as orm
from data.sessions import SqlAlchemyBase


class Questionnaire(SqlAlchemyBase):
    __tablename__ = 'questionnaires'
    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer)
    symptoms = sa.Column(sa.String)
    status = sa.Column(sa.String, default='Новый')
    recommendations = sa.Column(sa.String)
    created_at = sa.Column(sa.DateTime, default=datetime.now)