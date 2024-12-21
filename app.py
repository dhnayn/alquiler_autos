from flask import Flask, render_template, request, redirect, url_for, session, flash
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'clave_secreta_segura'
app.config['SESSION_TYPE'] = 'filesystem'

# Función para obtener la conexión a la base de datos
def get_db_connection():
    connection = pymysql.connect(
        host="sql10.freemysqlhosting.net",
        user="sql10753323",
        password="9eTIyjYawF",
        database="sql10753323",
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection

# Ruta de inicio (index)
@app.route('/')
def index():
    return render_template('index.html')

# Ruta de contacto
@app.route('/contacto')
def contacto():
    return render_template('contacto.html')

# Ruta de registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = 'usuario'  
        hashed_password = generate_password_hash(password)  
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("INSERT INTO usuarios (username, email, password, role) VALUES (%s, %s, %s, %s)",
                       (username, email, hashed_password, role))
        connection.commit()
        cursor.close()
        connection.close()

        flash('Registro exitoso. Ahora puedes iniciar sesión.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# Ruta de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']  
            flash(f'Bienvenido, {user["username"]}!', 'success')  
            return redirect(url_for('vehicles'))
        else:
            flash('Credenciales inválidas. Inténtalo de nuevo.', 'danger')  

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión.', 'success')
    return redirect(url_for('index'))

# Ruta de vehículos (ya no requiere sesión)
@app.route('/vehicles')
def vehicles():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM vehiculos")
    vehiculos = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('vehicles.html', vehiculos=vehiculos)


@app.route('/view_vehicles')
def view_vehicles():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM vehiculos")
    vehiculos = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('view_vehicles.html', vehiculos=vehiculos)

# Ruta para agregar un vehículo 
@app.route('/add_vehicle', methods=['GET', 'POST'])
def add_vehicle():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        marca = request.form['marca']
        modelo = request.form['modelo']
        año = request.form['año']
        color = request.form['color']

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO vehiculos (marca, modelo, año, color) VALUES (%s, %s, %s, %s)",
            (marca, modelo, año, color)
        )
        connection.commit()
        cursor.close()
        connection.close()
        flash('Vehículo añadido con éxito.', 'success')
        return redirect(url_for('view_vehicles'))

    return render_template('edit_vehicle.html', action="Añadir")

@app.route('/edit_vehicle/<int:id>', methods=['GET', 'POST'])
def edit_vehicle(id):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    connection = get_db_connection()
    cursor = connection.cursor()

    if id == 0:
        vehicle = None
    else:
        cursor.execute("SELECT * FROM vehiculos WHERE id = %s", (id,))
        vehicle = cursor.fetchone()

    if request.method == 'POST':
        marca = request.form['marca']
        modelo = request.form['modelo']
        año = request.form['año']
        color = request.form['color']

        if vehicle:
            cursor.execute(
                "UPDATE vehiculos SET marca = %s, modelo = %s, año = %s, color = %s WHERE id = %s",
                (marca, modelo, año, color, id)
            )
        else:
            cursor.execute(
                "INSERT INTO vehiculos (marca, modelo, año, color) VALUES (%s, %s, %s, %s)",
                (marca, modelo, año, color)
            )

        connection.commit()
        cursor.close()
        connection.close()
        flash('Vehículo guardado exitosamente.', 'success')
        return redirect(url_for('view_vehicles'))

    cursor.close()
    connection.close()
    return render_template('edit_vehicle.html', vehicle=vehicle, action="Editar" if vehicle else "Añadir")

# Ruta para eliminar un vehículo 
@app.route('/delete_vehicle/<int:id>', methods=['POST'])
def delete_vehicle(id):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM vehiculos WHERE id = %s", (id,))
    connection.commit()
    cursor.close()
    connection.close()
    flash('Vehículo eliminado con éxito.', 'success')
    return redirect(url_for('view_vehicles'))


@app.route('/manage_users')
def manage_users():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM usuarios")
    usuarios = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template('manage_users.html', usuarios=usuarios)

@app.route('/update_role/<int:id>', methods=['POST'])
def update_role(id):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    role = request.form['role']

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("UPDATE usuarios SET role = %s WHERE id = %s", (role, id))
    connection.commit()
    cursor.close()
    connection.close()

    flash('Rol actualizado correctamente.', 'success')
    return redirect(url_for('manage_users'))


if __name__ == '__main__':
    app.run(debug=True)
