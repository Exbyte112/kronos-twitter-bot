from flask import Flask, render_template, request
import pymongo
from pymongo import MongoClient

# MongoDB connection
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
    main_bot_email = request.form.get("email")
    main_bot_password = request.form.get("password")
    main_bot_username = request.form.get("username")
    
    # update data dictionary
    data = {
        "main_bot_email": main_bot_email,
        "main_bot_password": main_bot_password,
        "main_bot_username": main_bot_username
    }
    
    # save data to database
    collection.update_one(
        {"_id": 0},
        {"$set": data},
        upsert=True
    )
    
    # return success message as JSON
    return render_template("save.html", data=data)

import os

if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))
