from flask import Flask, request, render_template, redirect, url_for, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, text
from sqlalchemy.orm import declarative_base, sessionmaker

import os
import time
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "USERinformation.db"

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev_secret_key')
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH.as_posix()}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

ITEM_DB_PATH = BASE_DIR / "item_sorter.db"
item_engine = create_engine(f"sqlite:///{ITEM_DB_PATH.as_posix()}")
ItemBase = declarative_base()
ItemSessionLocal = sessionmaker(bind=item_engine, expire_on_commit=False)


class User(db.Model):
    __tablename__ = "ImportantInfo"

    Username = db.Column(db.String(80), primary_key=True, nullable=False)
    Password = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return f"<User {self.Username}>"


class ItemRecord(ItemBase):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    category = Column(String(80), default="Uncategorized")
    cost = Column(Float, nullable=False)
    qty = Column(Integer, nullable=False)
    total = Column(Float, nullable=False)
    created_by = Column(String(80), nullable=True)


class ItemActionLog(ItemBase):
    __tablename__ = "item_logs"

    id = Column(Integer, primary_key=True)
    action = Column(String(20), nullable=False)
    item_name = Column(String(120), nullable=False)
    category = Column(String(80), default="Uncategorized")
    cost = Column(Float, nullable=False)
    qty = Column(Integer, nullable=False)
    total = Column(Float, nullable=False)
    username = Column(String(80), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


ItemBase.metadata.create_all(item_engine)


with app.app_context():
    db.create_all()


def verify_user_login(username, password): # verifys credentials
    """Verify user credentials by checking username and password against the database."""
    try:
        user = db.session.execute(
            db.select(User).filter_by(Username=username)
        ).scalar_one_or_none()
        return user is not None and user.Password == password
    except Exception as e:
        print(f"Database error: {e}")
        return False


def serialize_item(record): # turns item data into JSON
    return {
        "id": record.id,
        "name": record.name,
        "category": record.category,
        "cost": record.cost,
        "qty": record.qty,
        "total": record.total,
        "created_by": record.created_by,
    }

@app.context_processor
def inject_login_status(): # shares login info with templates
    return {
        'logged_in': session.get('logged_in', False),
        'username': session.get('username')
    }

@app.route('/', methods=['GET', 'POST'])
def advert(): # shows the main landing page
    return render_template('Advertisement.html')


@app.route('/log', methods=['GET', 'POST'])
def Logins(): # handles user login
    if request.method == 'POST':
        name = request.form.get("usernamelogin", "")
        name2 = request.form.get("passwordlogin", "")
        if verify_user_login(name, name2):
            session['logged_in'] = True
            session['username'] = name
            return render_template('classitem.html')
        return render_template('IncorLogin.html')

    return render_template('Login.html')


@app.route('/logout')
def logout(): # logs the user out
    session.clear()
    return redirect(url_for('Logins'))


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password(): # lets users reset passwords
    if request.method == 'POST':
        username = request.form.get('forgot_username', '').strip()
        new_password = request.form.get('new_password', '').strip()

        if not username or not new_password:
            return render_template('ForgotPassword.html', error='Please enter both username and a new password')

        if len(new_password) < 8:
            return render_template('ForgotPassword.html', error='Password must be at least 8 characters long')

        try:
            user = db.session.execute(
                db.select(User).filter_by(Username=username)
            ).scalar_one_or_none()

            if not user:
                return render_template('ForgotPassword.html', error='Username not found')

            user.Password = new_password
            db.session.commit()
            return render_template('ForgotPassword.html', message='Password updated successfully')
        except Exception as exc:
            db.session.rollback()
            print(f"Could not reset password: {exc}")
            return render_template('ForgotPassword.html', error='Could not reset password')

    return render_template('ForgotPassword.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup(): # creates new user accounts
    if request.method == 'POST':
        username = request.form.get('newusername', '').strip()
        password = request.form.get('newpassword', '').strip()

        if not username or not password:
            return render_template('Signuppage.html')

        if len(password) < 8:
            return render_template('Signuppage.html', error='Password must be at least 8 characters long')

        existing_user = db.session.execute(
            db.select(User).filter_by(Username=username)
        ).scalar_one_or_none()

        if existing_user:
            return render_template('Signuppage.html', error='Username already exists')

        try:
            new_user = User(Username=username, Password=password)
            db.session.add(new_user)
            db.session.commit()
            print(f"Created user: {username}")
            return render_template('AccountCreated.html')
        except Exception as exc:
            db.session.rollback()
            print(f"Could not create user: {exc}")
            return render_template('Signuppage.html', error='Could not create account')

    return render_template('Signuppage.html')

        

@app.route('/itemwebsite', methods=['GET', 'POST'])
def login(): # test route for name input
    if request.method == 'POST':
        name = request.form['username']
        return f"Hello {name}, POST request received"
    return render_template('name.html')


@app.route('/users', methods=['GET'])
def users(): # shows registered users
    try:
        rows = db.session.execute(
            text("SELECT rowid, Username, Password FROM ImportantInfo ORDER BY rowid DESC")
        ).fetchall()
        return render_template('users.html', users=[tuple(row) for row in rows])
    except Exception as e:
        print(f"Database error: {e}")
        return render_template('users.html', users=[])


@app.route('/users_data', methods=['GET'])
def users_data(): # returns user data as JSON
    try:
        rows = db.session.execute(
            text("SELECT rowid, Username, Password FROM ImportantInfo ORDER BY rowid DESC")
        ).fetchall()
        users = [{"id": row[0], "username": row[1], "password": row[2]} for row in rows]
        return jsonify({"users": users, "ts": int(time.time())})
    except Exception as e:
        print(f"Database error: {e}")
        return jsonify({"users": [], "error": str(e)}), 500

@app.route('/item_data', methods=['GET'])
def item_data(): # returns saved items as JSON
    item_session = ItemSessionLocal()
    try:
        items = item_session.query(ItemRecord).order_by(ItemRecord.id.desc()).all()
        return jsonify({"items": [serialize_item(item) for item in items]})
    except Exception as exc:
        print(f"Could not load items: {exc}")
        return jsonify({"items": []}), 500
    finally:
        item_session.close()


@app.route('/item', methods=['GET', 'POST'])
def website(): # handles item add, edit, and remove actions
    if request.method == 'POST':
        payload = request.get_json(silent=True) or request.form or {}
        action = (payload.get('action') or '').strip().lower()
        username = session.get('username') or 'anonymous'

        if action == 'add':
            name = (payload.get('name') or payload.get('itemName') or '').strip()
            category = (payload.get('category') or payload.get('itemCategory') or 'Uncategorized').strip() or 'Uncategorized'
            cost = float(payload.get('cost') or payload.get('itemCost') or 0)
            qty = int(payload.get('qty') or payload.get('itemQty') or 0)

            if not name or qty <= 0:
                return jsonify({"ok": False, "error": "Invalid item details"}), 400

            item_session = ItemSessionLocal()
            try:
                existing = item_session.query(ItemRecord).filter_by(name=name, category=category).first()
                if existing:
                    existing.qty += qty
                    existing.total = round(existing.cost * existing.qty, 2)
                    existing.created_by = username
                    record = existing
                else:
                    record = ItemRecord(
                        name=name,
                        category=category,
                        cost=round(cost, 2),
                        qty=qty,
                        total=round(cost * qty, 2),
                        created_by=username,
                    )
                    item_session.add(record)
                    item_session.flush()

                item_session.add(ItemActionLog(
                    action='add',
                    item_name=name,
                    category=category,
                    cost=round(cost, 2),
                    qty=qty,
                    total=round(cost * qty, 2),
                    username=username,
                ))
                item_session.commit()
                return jsonify({
                    "ok": True,
                    "item": {
                        "id": record.id,
                        "name": record.name,
                        "category": record.category,
                        "cost": record.cost,
                        "qty": record.qty,
                        "total": record.total,
                    },
                })
            except Exception as exc:
                item_session.rollback()
                print(f"Could not save item: {exc}")
                return jsonify({"ok": False, "error": "Could not save item"}), 500
            finally:
                item_session.close()

        if action == 'edit':
            item_id = payload.get('id')
            if not item_id:
                return jsonify({"ok": False, "error": "Missing item id"}), 400

            name = (payload.get('name') or '').strip()
            category = (payload.get('category') or 'Uncategorized').strip() or 'Uncategorized'
            cost = float(payload.get('cost') or 0)
            qty = int(payload.get('qty') or 0)

            if not name or qty <= 0:
                return jsonify({"ok": False, "error": "Invalid item details"}), 400

            item_session = ItemSessionLocal()
            try:
                record = item_session.get(ItemRecord, int(item_id))
                if not record:
                    return jsonify({"ok": False, "error": "Item not found"}), 404

                old_total = record.total
                record.name = name
                record.category = category
                record.cost = round(cost, 2)
                record.qty = qty
                record.total = round(cost * qty, 2)
                record.created_by = username

                item_session.add(ItemActionLog(
                    action='edit',
                    item_name=name,
                    category=category,
                    cost=round(cost, 2),
                    qty=qty,
                    total=round(cost * qty, 2),
                    username=username,
                ))
                item_session.commit()
                return jsonify({"ok": True, "item": serialize_item(record)})
            except Exception as exc:
                item_session.rollback()
                print(f"Could not edit item: {exc}")
                return jsonify({"ok": False, "error": "Could not edit item"}), 500
            finally:
                item_session.close()

        if action == 'remove':
            item_id = payload.get('id')
            if not item_id:
                return jsonify({"ok": False, "error": "Missing item id"}), 400

            item_session = ItemSessionLocal()
            try:
                record = item_session.get(ItemRecord, int(item_id))
                if not record:
                    return jsonify({"ok": False, "error": "Item not found"}), 404

                item_session.add(ItemActionLog(
                    action='remove',
                    item_name=record.name,
                    category=record.category,
                    cost=record.cost,
                    qty=record.qty,
                    total=record.total,
                    username=username,
                ))
                item_session.delete(record)
                item_session.commit()
                return jsonify({"ok": True, "removed": True})
            except Exception as exc:
                item_session.rollback()
                print(f"Could not remove item: {exc}")
                return jsonify({"ok": False, "error": "Could not remove item"}), 500
            finally:
                item_session.close()

        return jsonify({"ok": False, "error": "Unsupported action"}), 400

    return render_template('classitem.html')





if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)