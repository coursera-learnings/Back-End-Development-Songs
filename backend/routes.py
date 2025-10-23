from . import app
import os
import json
import pymongo
from flask import jsonify, request, make_response, abort, url_for  # noqa; F401
from pymongo import MongoClient
from bson import json_util
from pymongo.errors import OperationFailure
from pymongo.results import InsertOneResult
from bson.objectid import ObjectId
import sys

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, "data", "songs.json")
songs_list: list = json.load(open(json_url))

# client = MongoClient(
#     f"mongodb://{app.config['MONGO_USERNAME']}:{app.config['MONGO_PASSWORD']}@localhost")
mongodb_service = os.environ.get('MONGODB_SERVICE')
mongodb_username = os.environ.get('MONGODB_USERNAME')
mongodb_password = os.environ.get('MONGODB_PASSWORD')
mongodb_port = os.environ.get('MONGODB_PORT')

print(f'The value of MONGODB_SERVICE is: {mongodb_service}')

if mongodb_service == None:
    app.logger.error('Missing MongoDB server in the MONGODB_SERVICE variable')
    # abort(500, 'Missing MongoDB server in the MONGODB_SERVICE variable')
    sys.exit(1)

if mongodb_username and mongodb_password:
    url = f"mongodb://{mongodb_username}:{mongodb_password}@{mongodb_service}"
else:
    url = f"mongodb://{mongodb_service}"


print(f"connecting to url: {url}")

try:
    client = MongoClient(url)
except OperationFailure as e:
    app.logger.error(f"Authentication error: {str(e)}")

db = client.songs
db.songs.drop()
db.songs.insert_many(songs_list)

def parse_json(data):
    return json.loads(json_util.dumps(data))

######################################################################
# INSERT CODE HERE
######################################################################
@app.get("/health")
def get_health():
    return {"status": "OK"}

@app.get("/count")
def get_count():
    count = db.songs.count_documents({})
    return jsonify(count=count)

@app.get("/song")
def get_songs():
    songs = db.songs.find({})
    return jsonify(songs=json.loads(json_util.dumps(songs)))

@app.get("/song/<int:id>")
def get_song_by_id(id):
    song = db.songs.find_one({"id": id})
    if song is None:
        return jsonify(message="song with id not found"), 404
    return jsonify(**json.loads(json_util.dumps(song)))


@app.post("/song")
def create_song():
    payload = request.get_json()
    if db.songs.count_documents({"id": id}) == 1:
        return jsonify(Message=f"song with id {payload['id']} already present"), 302
    
    result = db.songs.insert_one(payload)
    return jsonify({
        "inserted id": json.loads(json_util.dumps(result.inserted_id))
    }), 201

@app.put("/song/<int:id>")
def update_song(id):
    payload = request.get_json()
    result = db.songs.update_one({"id": id}, {"$set": payload})
    
    if result.matched_count == 0:
        return jsonify(message="song not found"), 404
    elif result.modified_count == 0:
        return jsonify(message="song found, but nothing updated")
    else:
        return jsonify(**json.loads(json_util.dumps(db.songs.find_one({"id": id})))), 201

@app.delete("/song/<int:id>")
def delete_one(id):
    result = db.songs.delete_one({"id": id})
    if result.deleted_count == 1:
        return make_response(('', 204))
    return jsonify(message="song not found")