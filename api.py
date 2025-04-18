
from flask import Flask, jsonify, request, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os
app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://steph:EudVLUL5n54OihQJVVcIlfcOWLiy2QQW@dpg-d00oqsidbo4c73di3lhg-a.frankfurt-postgres.render.com/incremental_game'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pseudo = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    scores = db.relationship('Score', backref='user', lazy=True)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, nullable=False, default=0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@app.route("/api/users/login", methods=["POST"])
def login_user():
    data = request.json
    if not data or not data.get('pseudo') or not data.get('password'):
        return make_response('Pseudo ou mot de passe manquant', 400)
    pseudo = data['pseudo']
    password = data['password']
    user = User.query.filter_by(pseudo=pseudo).first()
    if user and user.password == password:
        score = Score.query.filter_by(user_id=user.id).order_by(Score.id.desc()).first()
        return jsonify({"ida": user.id}), 200
    return make_response("Erreur dauthentification", 401)

@app.route("/api/users/score", methods=["POST"])
def score_of_user():
    data = request.json
    pseudo = data.get('pseudo')
    password = data.get('password')
    user = User.query.filter_by(pseudo=pseudo).first()
    if user and user.password == password:
        score = Score.query.filter_by(user_id=user.id).order_by(Score.id.desc()).first()
        return jsonify({"score": score.score if score else 0}), 200
    return make_response("Erreur d'authentification", 401)

@app.route("/api/users/register", methods=["POST"])
def register_user():
    data = request.json
    pseudo = data.get('pseudo')
    password = data.get('password')
    if User.query.filter_by(pseudo=pseudo).first():
        return make_response('Utilisateur déjà existant', 400)
    new_user = User(pseudo=pseudo, password=password)
    db.session.add(new_user)
    db.session.commit()
    return "200"

@app.route('/api/scores', methods=['POST'])
def add_score():
    data = request.json
    score_value = data.get('score')
    user_id = data.get('user_id')
    if not score_value or not user_id:
        return make_response("Score ou ID de l'utilisateur manquant", 400)
    new_score = Score(score=score_value, user_id=user_id)
    db.session.add(new_score)
    db.session.commit()
    return jsonify({'message': 'Score ajouté avec succès', 'user_id': user_id, 'score': score_value})

@app.route('/api/scores', methods=['GET'])
def get_scores():
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    scores = Score.query.filter_by(user_id=user_id).all()
    return jsonify({"scores": [{"score": s.score} for s in scores]})

@app.route('/api/users/update_score', methods=['POST'])
def update_score():
    data = request.json
    user_id = data.get('user_id')
    new_score = data.get('score')
    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    if user.scores:
        user.scores[0].score = new_score
    else:
        db.session.add(Score(score=new_score, user_id=user.id))
    db.session.commit()
    return jsonify({"message": "Score updated successfully"}), 200

@app.route('/api/top_scores', methods=['GET'])
def get_top_scores():
    top_scores = User.query.join(Score).order_by(Score.score.desc()).limit(5).all()
    results = ','.join(f"{user.pseudo}:{user.scores[0].score}" for user in top_scores)
    return results, 700




if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    with app.app_context():
        db.create_all()  # Crée les tables dans la base PostgreSQL
    app.run(debug=True, host='0.0.0.0', port=port)


