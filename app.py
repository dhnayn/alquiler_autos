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
        user="sql10756621",
        password="lz8Tk7kUqM",
        database="sql10756621",
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
    page = request.args.get('page', 1, type=int)
    limit = 10  # Número de elementos por página
    offset = (page - 1) * limit

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM vehiculos LIMIT %s OFFSET %s", (limit, offset))
    vehiculos = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) FROM vehiculos")
    total_vehiculos = cursor.fetchone()['COUNT(*)']
    total_pages = (total_vehiculos // limit) + (1 if total_vehiculos % limit > 0 else 0)

    cursor.close()
    connection.close()

    return render_template('vehicles.html', vehiculos=vehiculos, page=page, total_pages=total_pages)







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

@app.route('/add_vehicle', methods=['GET', 'POST'])
def add_vehicle():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))

    if request.method == 'POST':
        marca = request.form['marca']
        modelo = request.form['modelo']
        año = request.form['año']
        color = request.form['color']
        placas = request.form['placas']
        estado = request.form['estado']
        kilometraje = request.form['kilometraje']
        precio_dia = request.form['precio_dia']

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO vehiculos (marca, modelo, año, color, placas, estado, kilometraje, precio_dia) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            (marca, modelo, año, color, placas, estado, kilometraje, precio_dia)
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
        placas = request.form['placas']
        estado = request.form['estado']
        kilometraje = request.form['kilometraje']
        precio_dia = request.form['precio_dia']

        if vehicle:
            cursor.execute(
                "UPDATE vehiculos SET marca = %s, modelo = %s, año = %s, color = %s, placas = %s, estado = %s, "
                "kilometraje = %s, precio_dia = %s WHERE id = %s",
                (marca, modelo, año, color, placas, estado, kilometraje, precio_dia, id)
            )
        else:
            cursor.execute(
                "INSERT INTO vehiculos (marca, modelo, año, color, placas, estado, kilometraje, precio_dia) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (marca, modelo, año, color, placas, estado, kilometraje, precio_dia)
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


@app.route('/reserve_vehicle/<int:vehicle_id>', methods=['GET', 'POST'])
def reserve_vehicle(vehicle_id):
    if 'user_id' not in session:
        flash('Debes iniciar sesión para reservar un vehículo.', 'danger')
        return redirect(url_for('login'))

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM vehiculos WHERE id = %s", (vehicle_id,))
    vehicle = cursor.fetchone()

    if not vehicle:
        flash('El vehículo no existe.', 'danger')
        return redirect(url_for('vehicles'))

    if request.method == 'POST':
        user_id = session['user_id']
        nombre = request.form['nombre']
        fecha_inicio = request.form['fecha_inicio']
        fecha_fin = request.form['fecha_fin']
        comentarios = request.form['comentarios']
        
        cursor.execute(
            "INSERT INTO reserva (user_id, vehiculo_id, nombre, fecha_inicio, fecha_fin, comentarios) VALUES (%s, %s, %s, %s, %s, %s)",
            (user_id, vehicle_id, nombre, fecha_inicio, fecha_fin, comentarios)
        )
        connection.commit()
        flash('Reservación realizada exitosamente.', 'success')
        return redirect(url_for('view_reservations'))

    cursor.close()
    connection.close()
    return render_template('vehicle_details.html', vehicle=vehicle)


@app.route('/view_reservations')
def view_reservations():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para ver tus reservaciones.', 'danger')
        return redirect(url_for('login'))

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("""
        SELECT r.id AS reserva_id, v.marca, v.modelo, v.año, v.color, v.precio_dia, r.fecha_inicio, r.fecha_fin, r.comentarios
        FROM reserva r
        JOIN vehiculos v ON r.vehiculo_id = v.id
        WHERE r.user_id = %s
    """, (session['user_id'],))
    reservas = cursor.fetchall()
    cursor.close()
    connection.close()

    return render_template('reservations.html', reservas=reservas)


@app.route('/cancel_reservation/<int:reservation_id>', methods=['POST'])
def cancel_reservation(reservation_id):
    if 'user_id' not in session:
        flash('Debes iniciar sesión para cancelar una reservación.', 'danger')
        return redirect(url_for('login'))

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM reserva WHERE id = %s AND user_id = %s", (reservation_id, session['user_id']))
    connection.commit()
    cursor.close()
    connection.close()

    flash('Reservación cancelada con éxito.', 'success')
    return redirect(url_for('view_reservations'))


@app.route('/vehicle/<int:vehicle_id>/reserve', methods=['GET'])
def create_reservation(vehicle_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM vehiculos WHERE id = %s", (vehicle_id,))
    vehicle = cursor.fetchone()
    cursor.close()
    connection.close()
    
    if not vehicle:
        flash('El vehículo no existe.', 'danger')
        return redirect(url_for('vehicles'))

    return render_template('reservation_form.html', vehicle=vehicle)


@app.route('/vehicle/<int:vehicle_id>/reserve', methods=['POST'])
def save_reservation(vehicle_id):
    if 'user_id' not in session:
        flash('Debes iniciar sesión para realizar una reserva.', 'danger')
        return redirect(url_for('login'))

    nombre = request.form['nombre']
    fecha_inicio = request.form['fecha_inicio']
    fecha_fin = request.form['fecha_fin']
    comentarios = request.form['comentarios']
    
    # Insertamos los datos de la reserva en la base de datos
    connection = get_db_connection()
    cursor = connection.cursor()
    query = "INSERT INTO reserva (user_id, vehiculo_id, nombre, fecha_inicio, fecha_fin, comentarios) VALUES (%s, %s, %s, %s, %s, %s)"
    values = (session['user_id'], vehicle_id, nombre, fecha_inicio, fecha_fin, comentarios)
    cursor.execute(query, values)
    connection.commit()
    
    cursor.close()
    connection.close()

    flash('Reserva confirmada con éxito.', 'success')
    return redirect(url_for('vehicles'))

if __name__ == '__main__':
    app.run(debug=True)