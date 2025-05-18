import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import matplotlib.pyplot as plt
from datetime import datetime
import io
from data.sessions import *
from data.user import User
from data.healthtest import HealthTest
global_init("db/bot_database.db")

def plot_bmi():
    session = create_session()
    
    try:
        users = session.query(
            HealthTest.user_id,
            HealthTest.result,
            User.age, 
            User.name
        ).join(User).filter(
            User.age.isnot(None),
            HealthTest.test_type == 'BMI'
        ).distinct().order_by(
            User.age
        ).all()

        if not users:
            print("Нет пользователей с указанным возрастом и тестами BMI")
            return None

        ages = []
        bmis = []
        names = []
        
        for user in users:
            ages.append(user.age)
            bmis.append(float(user.result.split()[0]))
            names.append(user.name)

        plt.figure(figsize=(12, 8))
        
        scatter = plt.scatter(ages, bmis, c=bmis, cmap='viridis', s=100, alpha=0.7)
        plt.colorbar(scatter, label='Значение BMI')

        plt.axhline(y=18.5, color='red', linestyle='--', label='Недостаточный вес')
        plt.axhline(y=25, color='green', linestyle='--', label='Нормальный вес')
        plt.axhline(y=30, color='orange', linestyle='--', label='Избыточный вес')
        
        plt.title("Зависимость BMI от возраста")
        plt.xlabel("Возраст (лет)")
        plt.ylabel("Значение BMI")
        plt.legend()
        plt.grid(True, alpha=0.3)
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=120, bbox_inches='tight')
        buf.seek(0)
        
       
        return buf

    except Exception as e:
        print(f"Ошибка: {str(e)}")
        return None
    finally:
        session.close()
