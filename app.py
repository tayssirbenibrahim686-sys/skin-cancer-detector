from flask import Flask, render_template, request, redirect, session, flash
import mysql.connector
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from PIL import Image
import os

app = Flask(__name__)
app.secret_key = "secret"

model = load_model("model/vgg16_malignant_benign.h5")

def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="skin_cancer_db"
    )

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (username, password)
        )
        user = cursor.fetchone()
        if user:
            session["user"] = username
            return redirect("/dashboard")
        else:
            flash("Identifiants incorrects", "danger")
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template("dashboard.html")

@app.route("/predict", methods=["GET", "POST"])
def predict():
    if "user" not in session:
        return redirect("/")
    if request.method == "POST":
        name = request.form["name"]
        age = request.form["age"]
        image = request.files["image"]
        img_path = "static/uploads/" + image.filename
        image.save(img_path)
        img = Image.open(img_path).resize((224, 224))
        img_array = np.array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)
        prediction = model.predict(img_array)
        prob = float(prediction[0][0])
        result = "Malin" if prob > 0.5 else "Bénin"
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "INSERT INTO patients (name, age, result, probability, image_path) VALUES (%s,%s,%s,%s,%s)",
            (name, age, result, prob, img_path)
        )
        db.commit()
        return render_template("result.html",
                               result=result,
                               prob=round(prob * 100, 2),
                               img=img_path)
    return render_template("predict.html")

@app.route("/patients")
def patients():
    if "user" not in session:
        return redirect("/")
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM patients")
    all_patients = cursor.fetchall()
    return render_template("patients.html", patients=all_patients)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)