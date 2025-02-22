from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'clave_secreta_segura'
app.config['SESSION_TYPE'] = 'filesystem'

def get_db_connection():
    connection = pymysql.connect(
        host="sql10.freesqldatabase.com",
        user="sql10764018",
        password="VADDdPEiY2",
        database="sql10764018",
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/contacto')
def contacto():
    return render_template('contacto.html')

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            username = request.form["username"]
            email = request.form["email"]
            password = request.form["password"]
            region = request.form.get("region", None)
            tipo = request.form.get("tipo", "Particular")  
            nombre_empresa = request.form.get("nombre_empresa") if tipo == "Empresa" else None

            if not username or not email or not password:
                flash("Todos los campos son obligatorios.", "error")
                return redirect(url_for("register"))

            hashed_password = generate_password_hash(password)

            conn = get_db_connection()
            cursor = conn.cursor()

            sql = "INSERT INTO usuarios (username, email, password, region, tipo, nombre_empresa) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (username, email, hashed_password, region, tipo, nombre_empresa))

            conn.commit()
            cursor.close()
            conn.close()

            flash("Registro exitoso. Ahora puedes iniciar sesión.", "success")
            return redirect(url_for("login"))

        except Exception as e:
            flash(f"Error al registrar usuario: {str(e)}", "error")
            return redirect(url_for("register"))

    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if not email or not password:
            flash('Todos los campos son obligatorios.', 'danger')
            return redirect(url_for('login'))

        connection = get_db_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
            user = cursor.fetchone()

            if not user:
                flash('El correo no está registrado. Verifica e inténtalo nuevamente.', 'danger')
                return redirect(url_for('login'))

            if not check_password_hash(user['password'], password):
                flash('La contraseña es incorrecta. Inténtalo de nuevo.', 'danger')
                return redirect(url_for('login'))

            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['tipo'] = user['tipo']
            session['region'] = user['region']

            flash(f'Bienvenido, {user["username"]}!', 'success')
            return redirect(url_for('vehicles'))  
        except Exception as e:
            flash('Hubo un error al iniciar sesión. Inténtalo más tarde.', 'danger')
            print(f"Error: {e}")
        finally:
            cursor.close()
            connection.close()

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Has cerrado sesión.', 'success')
    return redirect(url_for('index'))

@app.route('/vehicles')

def vehicles():
    page = request.args.get('page', 1, type=int)
    limit = 10 
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

@app.route('/')
def index_vehicles():
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM vehiculos ORDER BY id DESC LIMIT 5") 
    vehiculos = cursor.fetchall()
    cursor.close()
    connection.close()
    
    return render_template('index.html', vehiculos=vehiculos)  

@app.route('/view_vehicles')
def view_vehicles():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute("""
        SELECT v.id, v.marca, v.modelo, v.año, v.color, v.placas, v.estado, 
               v.kilometraje, v.precio_dia, t.nombre AS tipo 
        FROM vehiculos v
        LEFT JOIN tipos_vehiculo t ON v.tipo_id = t.id
    """)
    
    vehiculos = cursor.fetchall()
    cursor.close()
    connection.close()
    
    return render_template('view_vehicles.html', vehiculos=vehiculos)


@app.route('/add_vehicle', methods=['GET', 'POST'])
def add_vehicle():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('index'))


    if request.method == 'POST':
        marca = request.form['marca']
        modelo = request.form['modelo']
        año = request.form['año']
        color = request.form['color']
        placas = request.form['placas']
        estado = request.form['estado']
        kilometraje = request.form['kilometraje']
        precio_dia = request.form['precio_dia']
        tipo_id = request.form['tipo_id']

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO vehiculos (marca, modelo, año, color, placas, estado, kilometraje, precio_dia, tipo_id) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
            (marca, modelo, año, color, placas, estado, kilometraje, precio_dia, tipo_id)
        )
        connection.commit()
        cursor.close()
        connection.close()
        flash('Vehículo añadido con éxito.', 'success')
        return redirect(url_for('view_vehicles'))


    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id, nombre FROM tipo_vehiculo")
    tipos = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('edit_vehicle.html', action="Añadir", tipos=tipos)


@app.route('/edit_vehicle/<int:id>', methods=['GET', 'POST'])
def edit_vehicle(id):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('index'))

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT id, nombre FROM tipos_vehiculo")
    tipos = cursor.fetchall()

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
        tipo_id = request.form['tipo_id']

        cursor.execute(
            "UPDATE vehiculos SET marca = %s, modelo = %s, año = %s, color = %s, placas = %s, estado = %s, "
            "kilometraje = %s, precio_dia = %s, tipo_id = %s WHERE id = %s",
            (marca, modelo, año, color, placas, estado, kilometraje, precio_dia, tipo_id, id)
        )

        connection.commit()
        cursor.close()
        connection.close()
        flash('Vehículo actualizado con éxito.', 'success')
        return redirect(url_for('view_vehicles'))

    cursor.close()
    connection.close()
    return render_template('edit_vehicle.html', vehicle=vehicle, tipos=tipos, action="Editar")



@app.route('/delete_vehicle/<int:id>', methods=['POST'])
def delete_vehicle(id):
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('index'))

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
        return redirect(url_for('index'))

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
        return redirect(url_for('index'))

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
    cursor = connection.cursor(pymysql.cursors.DictCursor)  

    try:
        cursor.execute("SELECT * FROM vehiculos WHERE id = %s", (vehicle_id,))
        vehicle = cursor.fetchone()

        if not vehicle:
            flash('El vehículo no existe.', 'danger')
            return redirect(url_for('vehicles'))

        cursor.execute("SELECT tipo, nombre_empresa, region FROM usuarios WHERE id = %s", (session['user_id'],))
        user_data = cursor.fetchone()

        if request.method == 'POST':
            user_id = session['user_id']
            nombre = request.form['nombre']
            fecha_inicio = request.form['fecha_inicio']
            fecha_fin = request.form['fecha_fin']
            comentarios = request.form.get('comentarios', '')  

            cursor.execute(
                """INSERT INTO reserva (user_id, vehiculo_id, nombre, fecha_inicio, fecha_fin, comentarios) 
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (user_id, vehicle_id, nombre, fecha_inicio, fecha_fin, comentarios)
            )
            connection.commit()
            flash('Reservación realizada exitosamente.', 'success')
            return redirect(url_for('view_reservations'))

    except pymysql.MySQLError as e:
        flash(f'Error en la base de datos: {e}', 'danger')
        connection.rollback()

    finally:
        cursor.close()
        connection.close()
    
    return render_template('vehicle_details.html', vehicle=vehicle, user_data=user_data)



@app.route('/view_reservations')
def view_reservations():
    if 'user_id' not in session:
        flash('Debes iniciar sesión para ver tus reservaciones.', 'danger')
        return redirect(url_for('login'))

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT r.id AS reserva_id, v.marca, v.modelo, v.año, v.color, v.precio_dia, 
               r.fecha_inicio, r.fecha_fin, r.comentarios, 
               u.tipo AS tipo_cliente, u.nombre_empresa, u.region
        FROM reserva r
        JOIN vehiculos v ON r.vehiculo_id = v.id
        JOIN usuarios u ON r.user_id = u.id
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

    connection = get_db_connection()
    cursor = connection.cursor()

    query_reserva = """
        INSERT INTO reserva (user_id, vehiculo_id, nombre, fecha_inicio, fecha_fin, comentarios) 
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    values_reserva = (session['user_id'], vehicle_id, nombre, fecha_inicio, fecha_fin, comentarios)
    cursor.execute(query_reserva, values_reserva)
    reserva_id = cursor.lastrowid  

    query_ingreso = """
        INSERT INTO ingresos (reserva_id, vehiculo_id, total)
        SELECT %s, v.id, (DATEDIFF(%s, %s) + 1) * v.precio_dia
        FROM vehiculos v
        WHERE v.id = %s
    """
    values_ingreso = (reserva_id, fecha_fin, fecha_inicio, vehicle_id)
    cursor.execute(query_ingreso, values_ingreso)

    connection.commit()
    cursor.close()
    connection.close()

    flash('Reserva confirmada con éxito.', 'success')
    return redirect(url_for('vehicles'))


@app.route('/api/ingresos')
def api_ingresos():
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)
    
    cursor.execute("""
        SELECT 
            i.id,
            r.nombre AS cliente,
            v.marca,
            v.modelo,
            r.fecha_inicio,
            r.fecha_fin,
            (DATEDIFF(r.fecha_fin, r.fecha_inicio) + 1) AS dias_alquilados,
            v.precio_dia,
            r.costo_adicional,
            i.total,
            i.fecha AS fecha_ingreso
        FROM ingresos i
        JOIN reserva r ON i.reserva_id = r.id
        JOIN vehiculos v ON i.vehiculo_id = v.id;
    """)
    
    ingresos = cursor.fetchall()
    cursor.close()
    connection.close()

    return jsonify(ingresos)


@app.route('/ingresos')
def ingresos():
    connection = get_db_connection()
    cursor = connection.cursor(pymysql.cursors.DictCursor)  
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('index'))
    
    cursor.execute("""
        SELECT 
            i.id,
            r.nombre AS cliente,
            v.marca,
            v.modelo,
            r.fecha_inicio,
            r.fecha_fin,
            (DATEDIFF(r.fecha_fin, r.fecha_inicio) + 1) AS dias_alquilados,
            v.precio_dia,
            r.costo_adicional,
            i.total,
            i.fecha AS fecha_ingreso
        FROM ingresos i
        JOIN reserva r ON i.reserva_id = r.id
        JOIN vehiculos v ON i.vehiculo_id = v.id;
    """)
    
    ingresos = cursor.fetchall() 
    cursor.close()
    connection.close()

    return render_template('ingresos.html', ingresos=ingresos)


if __name__ == '__main__':
    app.run(debug=True)
