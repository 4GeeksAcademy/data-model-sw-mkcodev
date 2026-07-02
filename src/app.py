"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Planet, Character, Favorite

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)


# como todavia no hay sistema de login, uso el usuario 1 como "usuario actual"
# TODO: cambiar esto cuando implementemos autenticacion
CURRENT_USER_ID = 1


# -------------------------------------------------------
# PEOPLE
# -------------------------------------------------------

@app.route('/people', methods=['GET'])
def get_all_people():
    # traigo todos los personajes y los serializo
    people = Character.query.all()
    result = list(map(lambda x: x.serialize(), people))
    return jsonify(result), 200


@app.route('/people/<int:people_id>', methods=['GET'])
def get_one_person(people_id):
    person = Character.query.get(people_id)
    if person is None:
        return jsonify({"msg": "personaje no encontrado"}), 404
    return jsonify(person.serialize()), 200


# -------------------------------------------------------
# PLANETS
# -------------------------------------------------------

@app.route('/planets', methods=['GET'])
def get_all_planets():
    planets = Planet.query.all()
    result = list(map(lambda x: x.serialize(), planets))
    return jsonify(result), 200


@app.route('/planets/<int:planet_id>', methods=['GET'])
def get_one_planet(planet_id):
    planet = Planet.query.get(planet_id)
    if planet is None:
        return jsonify({"msg": "planeta no encontrado"}), 404
    return jsonify(planet.serialize()), 200


# -------------------------------------------------------
# USERS
# -------------------------------------------------------

@app.route('/users', methods=['GET'])
def get_all_users():
    users = User.query.all()
    result = list(map(lambda x: x.serialize(), users))
    return jsonify(result), 200


@app.route('/users/favorites', methods=['GET'])
def get_user_favorites():
    # verifico que el usuario exista antes de buscar sus favoritos
    user = User.query.get(CURRENT_USER_ID)
    if user is None:
        return jsonify({"msg": "usuario no encontrado, crea uno desde el admin"}), 404

    favorites = Favorite.query.filter_by(user_id=CURRENT_USER_ID).all()
    result = list(map(lambda x: x.serialize(), favorites))
    return jsonify(result), 200


# -------------------------------------------------------
# FAVORITES - agregar
# -------------------------------------------------------

@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(planet_id):
    planet = Planet.query.get(planet_id)
    if planet is None:
        return jsonify({"msg": "ese planeta no existe"}), 404

    # no quiero duplicados en la lista de favoritos
    ya_existe = Favorite.query.filter_by(user_id=CURRENT_USER_ID, planet_id=planet_id).first()
    if ya_existe:
        return jsonify({"msg": "este planeta ya esta en tus favoritos"}), 400

    nuevo_fav = Favorite(user_id=CURRENT_USER_ID, planet_id=planet_id)
    db.session.add(nuevo_fav)
    db.session.commit()
    return jsonify(nuevo_fav.serialize()), 201


@app.route('/favorite/people/<int:people_id>', methods=['POST'])
def add_favorite_people(people_id):
    # ojo: el endpoint dice /people pero el modelo lo llama character_id, un poco confuso
    person = Character.query.get(people_id)
    if person is None:
        return jsonify({"msg": "ese personaje no existe"}), 404

    ya_existe = Favorite.query.filter_by(user_id=CURRENT_USER_ID, character_id=people_id).first()
    if ya_existe:
        return jsonify({"msg": "este personaje ya esta en tus favoritos"}), 400

    nuevo_fav = Favorite(user_id=CURRENT_USER_ID, character_id=people_id)
    db.session.add(nuevo_fav)
    db.session.commit()
    return jsonify(nuevo_fav.serialize()), 201


# -------------------------------------------------------
# FAVORITES - eliminar
# -------------------------------------------------------

@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def delete_favorite_planet(planet_id):
    fav = Favorite.query.filter_by(user_id=CURRENT_USER_ID, planet_id=planet_id).first()
    if fav is None:
        return jsonify({"msg": "favorito no encontrado"}), 404

    db.session.delete(fav)
    db.session.commit()
    return jsonify({"msg": "planeta eliminado de favoritos"}), 200


@app.route('/favorite/people/<int:people_id>', methods=['DELETE'])
def delete_favorite_people(people_id):
    fav = Favorite.query.filter_by(user_id=CURRENT_USER_ID, character_id=people_id).first()
    if fav is None:
        return jsonify({"msg": "favorito no encontrado"}), 404

    db.session.delete(fav)
    db.session.commit()
    return jsonify({"msg": "personaje eliminado de favoritos"}), 200


# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
