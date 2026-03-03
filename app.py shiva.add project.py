from flask import Flask, render_template, flash, redirect, request, send_from_directory, url_for, send_file, session
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sn
from keras.preprocessing.image import img_to_array, load_img
import mysql.connector
import os
import pandas as pd
import time
import joblib
from tensorflow.keras.models import load_model  # pyright: ignore[reportMissingImports]




app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    port="3306",
    database='Adds'
)

mycursor = mydb.cursor()

def executionquery(query,values):
    mycursor.execute(query,values)
    mydb.commit()
    return

def retrivequery1(query,values):
    mycursor.execute(query,values)
    data = mycursor.fetchall()
    return data

def retrivequery2(query):
    mycursor.execute(query)
    data = mycursor.fetchall()
    return data


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')


# @app.route('/login')
# def login():
#     return render_template('login.html')

# @app.route('/register')
# def register():
#     return render_template('register.html')


@app.route('/home')
def home():
    return render_template('home.html')




@app.route('/upload')
def upload():
    return render_template('upload.html')



accuracy_values = {
    'LogisticRegression': 0.77,
    'DecisionTree': 0.88,
    'RandomForest': 0.92,
    'KNN': 0.84,
    'NaiveBayes': 0.75,
    'GradientBoosting': 0.91,
    'LightGBM': 0.92,
    'XGBoost': 0.92,
    'ANN': 0.88,
    'CNN': 0.90,
    'RNN': 0.91,
    'StackingClassifier': 0.92,
    'LSTM': 0.91,
    'GRU': 0.91
}
@app.route('/model', methods=['POST', 'GET'])
def model():
    if request.method == "POST":
        # Get the selected algorithm from the form
        s = request.form['algo']
        
        if s in accuracy_values:
            acc = accuracy_values[s]
            msg = f'The accuracy obtained by the {s.replace("Classifier", " Classifier")} is: {acc:.2f}'
            msg1 = f'The accuracy obtained by the {s.replace("Classifier", " Classifier")} is: {acc * 100:.2f}%'
            return render_template('model.html', msg=msg, msg1=msg1)
        else:
            msg = "Please select a valid algorithm."
            return render_template('model.html', msg=msg)

    return render_template('model.html')






# Defer loading the GRU model and scaler until needed (lazy-load)
gru_model = None
scaler = None
model_loaded = False
model_load_error = None

def load_models():
    global gru_model, scaler, model_loaded, model_load_error
    if model_loaded or model_load_error:
        return
    try:
        gru_model = load_model('gru_model.h5')
        scaler = joblib.load('minmax_scaler.pkl')
        model_loaded = True
    except Exception as e:
        model_load_error = str(e)
        model_loaded = False
    return

@app.route('/prediction', methods=['GET', 'POST'])
def prediction():
    if request.method == 'POST':
        # Extract form data
        try:
            ip = float(request.form['ip'])
            app = float(request.form['app'])
            device = float(request.form['device'])
            os = float(request.form['os'])
            channel = float(request.form['channel'])
            hour = float(request.form['hour'])
            minute = float(request.form['minute'])

            # Prepare input data for prediction
            input_data = np.array([[ip, app, device, os, channel, hour, minute]])

            # Ensure models are loaded
            load_models()
            if model_load_error:
                return render_template('prediction.html', error=f"Model load error: {model_load_error}")

            # Apply scaling
            scaled_data = scaler.transform(input_data)

            # Reshape for GRU input (3D array: [samples, time steps, features])
            scaled_data_reshaped = scaled_data.reshape(1, scaled_data.shape[1], 1)

            # Make prediction
            prediction = (gru_model.predict(scaled_data_reshaped) > 0.5).astype(int)

            # Map prediction to result message
            if prediction[0] == 1:
                result = " Fraudulent Click"
            else:
                result = " Non-fraudulent Click"

            return render_template('prediction.html', prediction=result)
        except ValueError:
            error = "Invalid input. Please enter valid numeric values for all fields."
            return render_template('prediction.html', error=error)

    return render_template('prediction.html')

# Other routes (e.g., /model) would go here

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        c_password = request.form['c_password']
        username = request.form['username']  # Get username from form
        
        if password == c_password:
            # Check if the email already exists
            query = "SELECT UPPER(email) FROM users"
            email_data = retrivequery2(query)
            email_data_list = [i[0] for i in email_data]
            
            # Check if the username already exists
            query_username = "SELECT UPPER(username) FROM users"
            username_data = retrivequery2(query_username)
            username_data_list = [i[0] for i in username_data]
            
            if email.upper() not in email_data_list:
                if username.upper() not in username_data_list:
                    # If the email and username are not taken, insert the new user
                    query = "INSERT INTO users (email, password, username) VALUES (%s, %s, %s)"
                    values = (email, password, username)
                    executionquery(query, values)
                    return render_template('login.html', message="Successfully Registered! Please go to login section")
                else:
                    return render_template('register.html', message="This username is already taken!")
            else:
                return render_template('register.html', message="This email ID is already exists!")
        
        return render_template('register.html', message="Confirm password does not match!")
    return render_template('register.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        
        # Fetch all emails from database and convert them to lowercase
        query = "SELECT LOWER(email) FROM users"
        email_data = retrivequery2(query)
        email_data_list = [i[0] for i in email_data]

        # Check if email exists
        if email.lower() in email_data_list:
            query = "SELECT password FROM users WHERE email = %s"
            values = (email,)
            password_data = retrivequery1(query, values)
            
            # Check password (in real-world cases, you should hash the password and compare)
            if password == password_data[0][0]:
                global user_email
                user_email = email
                return redirect("/home")

            # Invalid password
            return render_template('login.html', message="Invalid Password!")
        
        # Invalid email
        return render_template('login.html', message="This email ID does not exist!")
    
    return render_template('login.html')



# @app.route('/home')
# def home():
#     return render_template('home.html')

# @app.route('/about')
# def about():
#     return render_template('about.html')





if __name__ == '__main__':
    app.run(debug = True)

