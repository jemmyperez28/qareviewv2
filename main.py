from flask import Flask, request, jsonify, render_template, Response, redirect, url_for, flash
from jira import JIRA
import os
from datetime import datetime , date
import json

app = Flask(__name__)
app.secret_key = "clave_secreta_temporal"

# Variable global para almacenar el token (temporalmente en memoria)
jira_auth_token = {
    "username": None,
    "token": None
}

@app.route('/')
def index():
    return jsonify({"Choo Choo": " Welcome to your Flask app 🚅"})

@app.route('/form')
def mostrar_formulario():
    return render_template("form.html")

@app.route('/auth', methods=['GET', 'POST'])
def auth_jira():
    global jira_auth_token

    if request.method == 'POST':
        username = request.form.get('username')
        token = request.form.get('token')

        try:
            jira_options = {'server': 'https://jira.globaldevtools.bbva.com'}
            jira_test = JIRA(options=jira_options, auth=(username, token))
            jira_test.projects()  # Intenta acceder a algo para verificar

            # ✅ Guardar token en memoria
            jira_auth_token["username"] = username
            jira_auth_token["token"] = token

            flash("✅ Autenticación exitosa. Token guardado en memoria.", "success")
            return redirect(url_for('auth_jira'))

        except Exception as e:
            flash(f"❌ Error de autenticación: {str(e)}", "error")
            return redirect(url_for('auth_jira'))

    return render_template("auth.html", username=jira_auth_token["username"])

@app.route('/sync', methods=['POST'])
def sync_ticket():
    try:
        datos = request.get_json()
        if not datos:
            return jsonify({"error": "No se recibió JSON válido"}), 400

        # Agrega el timestamp dentro del mismo diccionario
        datos["timestamp_servidor"] = datetime.utcnow().isoformat()

        # Guarda en archivo txt
        ruta_archivo = os.path.join(os.path.dirname(__file__), 'registro.txt')
        with open(ruta_archivo, 'a', encoding='utf-8') as f:
            f.write(json.dumps(datos, ensure_ascii=False) + '\n')

        return jsonify({"estado": "✅ Registro guardado"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/ver-registros', methods=['GET'])
def ver_registros():
    ruta_archivo = os.path.join(os.path.dirname(__file__), 'registro.txt')

    if not os.path.exists(ruta_archivo):
        return Response("📭 No hay registros todavía", mimetype='text/plain')

    registros = []
    hoy = date.today()
    total_hoy = 0

    try:
        with open(ruta_archivo, 'r', encoding='utf-8') as f:
            for linea in f:
                try:
                    registro = json.loads(linea)
                    registros.append(registro)

                    # ✅ Ahora el timestamp está directamente en el registro
                    if "timestamp_servidor" in registro:
                        timestamp = datetime.fromisoformat(registro["timestamp_servidor"])
                        if timestamp.date() == hoy:
                            total_hoy += 1

                except json.JSONDecodeError:
                    registros.append({
                        "error": "❌ Línea no válida",
                        "contenido": linea.strip()
                    })

    except Exception as e:
        return Response(f"❌ Error al leer los registros: {str(e)}", mimetype='text/plain')

    registros_texto = json.dumps(registros, indent=2, ensure_ascii=False)
    mensaje = f"\n\n📅 Total de registros insertados hoy ({hoy}): {total_hoy}"

    return Response(registros_texto + mensaje, mimetype='text/plain')

@app.route('/consulta', methods=['POST'])
def consultar_formulario():
    global jira_auth_token

    username = jira_auth_token.get("username")
    token = jira_auth_token.get("token")
    issue_key = 'DEDATIOCL1-5240'  # fijo

    if not username or not token:
        return jsonify({"error": "❌ No se ha autenticado aún. Ingresa credenciales en /auth"}), 400

    jira_options = {'server': 'https://jira.globaldevtools.bbva.com'}

    try:
        jira_obj = JIRA(options=jira_options, auth=(username, token))
        issue = jira_obj.issue(issue_key)

        resultado = {
            "key": issue.key,
            "summary": issue.fields.summary,
            "assignee": issue.fields.assignee.displayName if issue.fields.assignee else "Sin asignar",
            "created": issue.fields.created,
            "status": issue.fields.status.name,
            "type": issue.fields.issuetype.name
        }

        return jsonify(resultado)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/tickets')
def vista_tickets_multiples():
    global jira_auth_token

    username = jira_auth_token.get("username")
    token = jira_auth_token.get("token")

    if not username or not token:
        return render_template("tickets.html", error="❌ No autenticado. Por favor ve a /auth."), 401

    jira_options = {'server': 'https://jira.globaldevtools.bbva.com'}

    # Mapeo de tickets a su tipo de desarrollo
    tickets_info = {
        "DEDATIOCL1-5015": "ControlM",
        "DEDATIOCL1-5315": "Kirby",
        "DEDATIOCL1-5364": "ControlM",
        "DEDATIOCL1-5299": "ControlM"
    }

    resultados = []
    try:
        jira_obj = JIRA(options=jira_options, auth=(username, token))
        for key, tipo_desarrollo in tickets_info.items():
            try:
                issue = jira_obj.issue(key, expand='changelog')
                # Buscar Team Backlog (ajusta el campo real si es diferente)
                team_backlog = getattr(issue.fields, 'customfield_18900', 'No disponible')

                # Obtener último cambio de estado
                ultimo_cambio_estado = None
                for historial in reversed(issue.changelog.histories):
                    for item in historial.items:
                        if item.field.lower() == 'status':
                            ultimo_cambio_estado = datetime.strptime(historial.created[:19], "%Y-%m-%dT%H:%M:%S")
                            break
                    if ultimo_cambio_estado:
                        break

                if ultimo_cambio_estado:
                    tiempo_transcurrido = datetime.utcnow() - ultimo_cambio_estado
                    dias = tiempo_transcurrido.days
                    horas = round(tiempo_transcurrido.seconds / 3600)
                    tiempo_formateado = f"{dias} días, {horas} horas"
                else:
                    tiempo_formateado = "N/D"

                resultados.append({
                    "key": key,
                    "status": issue.fields.status.name,
                    "assignee": issue.fields.assignee.displayName if issue.fields.assignee else "Sin asignar",
                    "tipo": tipo_desarrollo,
                    "backlog": team_backlog,
                    "horas_estado": tiempo_formateado
                })

            except Exception as e:
                resultados.append({
                    "key": key,
                    "status": "❌ Error",
                    "assignee": str(e),
                    "tipo": tipo_desarrollo,
                    "backlog": "N/D",
                    "horas_estado": "N/D"
                })

    except Exception as e:
        return render_template("tickets.html", error=f"❌ Error conectando a Jira: {str(e)}"), 500

    return render_template("tickets.html", tickets=resultados)




if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
