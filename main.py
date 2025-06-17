from flask import Flask, request, jsonify, render_template, Response
from jira import JIRA
import os
from datetime import datetime , date
import json

app = Flask(__name__)


@app.route('/')
def index():
    return jsonify({"Choo Choo": "Welcome to your Flask app 🚅"})

@app.route('/form')
def mostrar_formulario():
    return render_template("form.html")

@app.route('/sync', methods=['POST'])
def sync_ticket():
    try:
        datos = request.get_json()
        if not datos:
            return jsonify({"error": "No se recibió JSON válido"}), 400

        # Agrega timestamp del servidor
        registro = {
            "timestamp_servidor": datetime.utcnow().isoformat(),
            "datos": datos
        }

        # Guarda en archivo txt
        ruta_archivo = os.path.join(os.path.dirname(__file__), 'registro.txt')
        with open(ruta_archivo, 'a', encoding='utf-8') as f:
            f.write(json.dumps(registro, ensure_ascii=False) + '\n')

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

                    # Cuenta si el timestamp del servidor es de hoy
                    timestamp = datetime.fromisoformat(registro["timestamp_servidor"])
                    if timestamp.date() == hoy:
                        total_hoy += 1

                except json.JSONDecodeError:
                    registros.append({"error": "❌ Línea no válida", "contenido": linea.strip()})

    except Exception as e:
        return Response(f"Error al leer los registros: {str(e)}", mimetype='text/plain')

    # Formatear como texto legible con saltos de línea
    registros_texto = json.dumps(registros, indent=2, ensure_ascii=False)
    mensaje = f"\n\n📅 Total de registros insertados hoy ({hoy}): {total_hoy}"

    return Response(registros_texto + mensaje, mimetype='text/plain')

@app.route('/consulta', methods=['POST'])
def consultar_formulario():
    username = request.form.get('username')
    token = request.form.get('token')
    issue_key = request.form.get('issue_key')

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

if __name__ == '__main__':
    app.run(debug=True, port=os.getenv("PORT", default=5000))
