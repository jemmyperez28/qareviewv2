from flask import Flask, jsonify
from jira import JIRA
import os

app = Flask(__name__)


@app.route('/')
def index():
    return jsonify({"Choo Choo": "Welcome to your Flask app 🚅"})

@app.route('/jira/<issue_key>')
def consultar_issue(issue_key):
    # Datos en duro solo para pruebas (⚠️ nunca en producción)
    username = 'jemmy.perez'
    token = 'BBDC-MzY3Nzk0NzI0MjgyOqO3TBZ55roayjdja6+8zXmASp8I'
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
