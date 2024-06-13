from flask import Flask, render_template, request, jsonify
import json
import pymongo
from pymongo import MongoClient

cluster = MongoClient(
    "mongodb+srv://exbyte:1234@cluster0.aw1f22q.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
)

db = cluster["KronosTwikit"]
collection = db["KronosTwikit"]

app = Flask(__name__)

@app.route("/")
def edit_db():
    return render_template("index.html")

@app.route("/save", methods=["POST"])
def save_changes():
    # get form data
    main_bot_email = request.form.get("main_bot_email")
    main_bot_password = request.form.get("main_bot_password")
    main_bot_username = request.form.get("main_bot_username")
    
    # update data dictionary
    data = {
        "main_bot_email": main_bot_email,
        "main_bot_password": main_bot_password,
        "main_bot_username": main_bot_username
    }
    
    # save data to database
    collection.insert_one(data)
    
    # return success message as JSON
    return render_template("save.html", data=data)

if __name__ == "__main__":
    app.run(debug=True)
