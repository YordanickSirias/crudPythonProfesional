from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

from config import Config
from models.database import db, User, Persona

app = Flask(__name__)
app.config.from_object(Config)

# Inicializar la base de datos
db.init_app(app)

# Inicializar login manager
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

# Crear base.db automáticamente
with app.app_context():
    db.create_all()

# Cargar usuario para Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# === RUTAS PRINCIPALES === #

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['username']
        clave = request.form['password']
        user = User.query.filter_by(username=usuario).first()
        if user and check_password_hash(user.password, clave):
            login_user(user)
            flash('Inicio de sesión exitoso ✅')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuario o contraseña incorrectos ❌')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        usuario = request.form['username']
        clave = generate_password_hash(request.form['password'])
        email = request.form['email']
        telefono = request.form['telefono']
        foto = ""  # Puedes agregar subida de foto más adelante

        if User.query.filter_by(username=usuario).first():
            flash('Ese nombre de usuario ya existe ❌')
            return redirect(url_for('register'))

        nuevo = User(username=usuario, password=clave, email=email, telefono=telefono, foto=foto)
        db.session.add(nuevo)
        db.session.commit()
        flash('Registro exitoso ✅')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada exitosamente 📴')
    return redirect(url_for('login'))

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        buscar = request.form['buscar']
        personas = Persona.query.filter(Persona.nombre.ilike(f'%{buscar}%')).all()
    else:
        personas = Persona.query.all()
    return render_template('dashboard.html', personas=personas)

# === CRUD DE PERSONAS === #

@app.route('/create', methods=['GET', 'POST'])
@login_required
def create_persona():
    if request.method == 'POST':
        nombre = request.form['nombre']
        edad = request.form['edad']
        correo = request.form['correo']
        telefono = request.form['telefono']
        
        archivo = request.files['documento']
        nombre_archivo = ""
        if archivo and archivo.filename != "":
            nombre_archivo = secure_filename(archivo.filename)
            archivo.save(os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo))

        nueva = Persona(
            nombre=nombre,
            edad=edad,
            correo=correo,
            telefono=telefono,
            documento=nombre_archivo
        )
        db.session.add(nueva)
        db.session.commit()
        flash('Persona registrada exitosamente ✅')
        return redirect(url_for('dashboard'))

    return render_template('create.html')

@app.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_persona(id):
    persona = Persona.query.get_or_404(id)

    if request.method == 'POST':
        persona.nombre = request.form['nombre']
        persona.edad = request.form['edad']
        persona.correo = request.form['correo']
        persona.telefono = request.form['telefono']

        archivo = request.files['documento']
        if archivo and archivo.filename != "":
            nombre_archivo = secure_filename(archivo.filename)
            archivo.save(os.path.join(app.config['UPLOAD_FOLDER'], nombre_archivo))
            persona.documento = nombre_archivo

        db.session.commit()
        flash('Persona actualizada ✅')
        return redirect(url_for('dashboard'))

    return render_template('update.html', persona=persona)

@app.route('/delete/<int:id>')
@login_required
def eliminar_persona(id):
    persona = Persona.query.get_or_404(id)
    db.session.delete(persona)
    db.session.commit()
    flash('Persona eliminada 🗑️')
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(debug=True)
