from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from redis import Redis
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

db = SQLAlchemy(app)
redis_client = Redis.from_url(os.environ.get('REDIS_URL'))


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)


@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})


@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.all()
    return jsonify([{'id': t.id, 'title': t.title, 'completed': t.completed} for t in tasks])


@app.route('/api/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    task = Task(title=data['title'])
    db.session.add(task)
    db.session.commit()
    redis_client.delete('tasks_cache')
    return jsonify({'id': task.id, 'title': task.title}), 201


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8080)
