from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from database import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    email = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    is_admin = Column(Boolean, default=False)
    tasks = relationship('Task', back_populates="user")

    def __repr__(self):
        return f'{self.id, self.name, self.email, self.password_hash}'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_values(self, form_data):
        self.name = form_data['name']
        self.email = form_data['email']
        self.password_hash = generate_password_hash(form_data['password_hash'])

class Task(db.Model):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    desc = Column(Text, nullable=False)
    created_at = Column(DateTime(), default=datetime.now)
    end_date = Column(DateTime(), default=datetime.now)
    id_user = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', back_populates='tasks')
    def set_values(self, form_data):
        self.name = form_data['name']
        self.desc = form_data['desc']
        if form_data['created_at'] is None or form_data['created_at'] == '':
            self.created_at = datetime.now()
        else:
            self.created_at = form_data['created_at']
        if form_data['end_date'] is None or form_data['end_date'] == '':
            self.end_date = datetime.now()
        else:
            self.end_date = form_data['end_date']
        self.id_user = form_data['id_user']

    def __repr__(self):
        return f'{self.id, self.name}'

def getModel(tablename):
    dictTables = { User.__tablename__ : User,
                   Task.__tablename__ : Task}
    return dictTables[tablename]

#Первоначальное создание базы данных и таблиц прямым вызовом файла
if __name__ == '__main__':
    from flask import Flask
    from database import db
    app = Flask(__name__, static_url_path='/static')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///task.db'
    app.app_context().push()
    db.init_app(app)
    db.create_all()
    admin = User()
    admin.is_admin = True
    admin.name = 'Администратор'
    admin.set_password('1234')
    admin.email = ''
    db.session.add(admin)
    db.session.commit()

