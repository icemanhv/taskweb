from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, CheckConstraint, Boolean, Double
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
    reviews = relationship('Review', back_populates="user")
    orders = relationship('Order', back_populates="user")

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

class Category(db.Model):
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    products = relationship('Product')

    def set_values(self, form_data):
        self.name = form_data['name']

    def __repr__(self):
        return f'{self.id, self.name}'

class Product(db.Model):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=False)
    desc = Column(Text, nullable=False)
    avg_rate = Column(Double, default=0.0)
    price = Column(Integer, nullable=False)
    stock = Column(Integer, nullable=False)
    id_category = Column(Integer, ForeignKey('categories.id'))
    reviews = relationship('Review', back_populates='product')

    def set_values(self, form_data):
        self.name = form_data['name']
        self.desc = form_data['desc']
        self.avg_rate = form_data['avg_rate']
        self.price = int(form_data['price'])
        self.stock = int(form_data['stock'])
        self.id_category = int(form_data['id_category'])

    def __repr__(self):
        return f'{self.id, self.name, self.desc, self.price, self.id_category}'

class Review(db.Model):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True)
    text = Column(Text, nullable=False)
    rate = Column(Integer, CheckConstraint('rate >= 0 AND rate <= 5'), nullable=False)
    created_at = Column(DateTime(), default=datetime.now)
    updated_at = Column(DateTime(), default=datetime.now, onupdate=datetime.now)
    id_user = Column(Integer, ForeignKey('users.id'))
    id_product = Column(Integer, ForeignKey('products.id'))
    user = relationship('User', back_populates='reviews')
    product = relationship('Product', back_populates='reviews')

    def set_values(self, form_data):
        self.text = form_data['text']
        self.rate = form_data['rate']
        print(self.created_at)
        print(self.updated_at)
        if form_data['created_at'] is None or form_data['created_at'] == '':
            self.created_at = datetime.now()
        else:
            self.created_at = form_data['created_at']
        if form_data['updated_at'] is None or form_data['updated_at'] == '':
            self.updated_at = datetime.now()
        else:
            self.updated_at = form_data['updated_at']
        self.id_user = form_data['id_user']
        self.id_product = form_data['id_product']
        print(self.created_at)
        print(self.updated_at)

    def __repr__(self):
        return f'{self.id, self.text, self.rate, self.created_at, self.updated_at, self.id_user, self.id_product}'

class Order(db.Model):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)                      # id заказа
    id_user = Column(Integer, ForeignKey('users.id'))           # id покупателя
    created_at = Column(DateTime(), default=datetime.now)       # дата создания
    dest = Column(Text, nullable=False)                         # адрес доставки
    order_items = relationship('OrderItem')
    user = relationship('User', back_populates='orders')

    def set_values(self, form_data):
        self.id_user = form_data['id_user']
        self.dest = form_data['dest']
        if form_data['created_at'] is None or form_data['created_at'] == '':
            self.created_at = datetime.now()
        else:
            self.created_at = form_data['created_at']

    def __repr__(self):
        return f'{self.id, self.id_user, self.dest, self.created_at}'

class OrderItem(db.Model):                                      # Таблица продуктов относящихся к заказу
    __tablename__ = 'orderitems'
    id = Column(Integer, primary_key=True)
    id_order = Column(Integer, ForeignKey('orders.id'))         # принадлежность к номеру заказа, один ко многим
    id_product = Column(Integer, ForeignKey('products.id'))     # id продукта, один к одному

    def set_values(self, form_data):
        self.id_order = form_data['id_order']
        self.id_product = form_data['id_product']

    def __repr__(self):
        return f'{self.id, self.id_order, self.id_product}'

def getModel(tablename):
    dictTables = { User.__tablename__ : User,
                   Category.__tablename__ : Category,
                   Product.__tablename__ : Product,
                   Review.__tablename__ : Review,
                   Order.__tablename__ : Order,
                   OrderItem.__tablename__ : OrderItem }
    return dictTables[tablename]

#Первоначальное создание базы данных и таблиц прямым вызовом файла
if __name__ == '__main__':
    from flask import Flask
    from database import db
    app = Flask(__name__, static_url_path='/static')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
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

