from datetime import datetime, timedelta
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, current_user, login_user, logout_user, login_required

from database import db, get_model_fields, get_tables_name
from models import User, getModel, Task

app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = '12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///task.db'
app.app_context().push()
db.init_app(app)

login = LoginManager(app)


@login.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/')
def index():
    tasks = Task.query.filter(Task.id.between(0, 10)).all()
    start = datetime.now()
    end = (datetime.now() + timedelta(hours=24))
    return render_template('index.html', tasks=tasks, start=start, end=end)


@app.route('/task/<task_id>', methods=['GET', 'POST'])
def task(task_id):
    return render_template('task.html', task=db.session.get(Task, int(task_id)))

@app.route('/add_task', methods=['POST'])
def add_task():
    if request.form['created_at'] is not None and request.form['end_date'] is not None:
        try:
            print(request.form['created_at'], request.form['end_date'])
            created_at = datetime.strptime(request.form['created_at'], '%Y-%m-%dT%H:%M')
            end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%dT%H:%M')
            name = request.form['name']
            desc = request.form['desc']
            created_at = created_at
            end_date = end_date
            new_task = Task(name=name, desc=desc, created_at=created_at, end_date=end_date)
            db.session.add(new_task)
            db.session.commit()
        except ValueError:
            flash('Неправильный формат даты', 'danger')
    return redirect(url_for('index'))
@app.route('/update_task/<task_id>', methods=['POST'])
def update_task(task_id):
    sel_task = db.session.get(Task, int(task_id))
    if task is None:
        flash('Не найдена задача', 'danger')
        return redirect(url_for('task', task_id=task_id))
    if request.form['created_at'] is not None and request.form['end_date'] is not None:
        try:
            created_at = datetime.strptime(request.form['created_at'], '%Y-%m-%dT%H:%M')
            end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%dT%H:%M')
            sel_task.name = request.form['name']
            sel_task.desc = request.form['desc']
            sel_task.created_at = created_at
            sel_task.end_date = end_date
            db.session.commit()
            return redirect(url_for('task', task_id=task_id))
        except ValueError:
            flash('Неправильный формат даты', 'danger')
            redirect(url_for('task', task_id=task_id))
    return redirect(url_for('task', task_id=task_id))

@app.route('/remove_task/<task_id>')
def remove_task(task_id):
    sel_task = db.session.get(Task, int(task_id))
    if sel_task is not None:
        db.session.delete(sel_task)
        db.session.commit()
    return redirect(url_for('index'))
@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/auth/register/', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index', username=current_user.name))
    if request.method == 'POST':
        form_name = request.form['name']
        form_email = request.form['email']
        form_password = request.form['password']
        if User.query.filter_by(email=form_email).first():
            flash('Такой пользователь уже существует')
        user = User()
        user.name = form_name
        user.email = form_email
        user.set_password(form_password)

        db.session.add(user)
        db.session.commit()
        return redirect(url_for('/auth/login'))
    return render_template('/auth/register.html')


@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        print("already auth")
        return redirect(url_for('index'))
    if request.method == 'POST':
        form_email = request.form['email']
        form_password = request.form['password']
        user = User.query.filter_by(email=form_email).first()
        if user and user.check_password(form_password):
            print("login accept")
            login_user(user)
            return redirect(url_for('index'))
        flash("Неверно введенные данные", 'danger')
    return render_template('/auth/login.html')


@app.route('/auth/logout')
@login_required
def logout():
    logout_user()
    return redirect('/auth/login')


@app.route('/admin')
@login_required
def admin():
    tables = get_tables_name()
    return render_template('/admin/main.html', tables=tables)


@app.route('/admin/tables/<name>', methods=['GET', 'POST'])
@login_required
def admin_tables(name):
    if request.method == 'POST':
        model = getModel(name)()
        model.set_values(request.form)
        db.session.add(model)
        db.session.commit()
    tables = get_tables_name()
    fields = get_model_fields(getModel(name))
    fkdict = dict()
    for field in fields:
        if field['foreign_key']:
            col = list(field['foreign_key'])[0].column
            res = db.session.query(col.table).all()
            fkdict[field['name']] = res
    fields_data = getModel(name).query.all()
    return render_template('/admin/basicTable.html', tables=tables, tablename=name, fields=fields, data=fields_data,
                           fkdict=fkdict)


if __name__ == '__main__':
    app.run(debug=True)
