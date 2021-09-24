from flask import Flask
from flask import request
from flask import flash, redirect
from flask import jsonify
import sqlite3
import os
import random
import string
import hashlib

app = Flask(__name__)
salt = os.urandom(32)

###########################################
##    Compte Rendu PDF dans ce dossier   ##
##            CHATELAIN  NOAH            ##
##             GYRE AMBROISE             ##
##              FISA TI-2023             ##
##             TP1 WebServeur            ##
###########################################

# /!\ Le mot de passe par défaut de tous les étudiants est : 123456
# Il apparaît dans la base de donné hashé en SHA256

# Run : python3 app.py

@app.route('/bonjour')
def bonjour():
    return 'Hello World\n'


@app.route('/getit')
def getit():
    text = ''
    for argument in request.args:
        text += ' ' + argument
    return text


@app.route('/addition/<number1>/<number2>')
def addition(number1=None, number2=None):
    return str(int(number1) + int(number2)) + '\n'


@app.route('/compare/<arga>/<argb>')
def compare(arga=None, argb=None):
    print(str(arga) + " " + str(argb))
    return str(str(arga) == str(argb)) + "\n"


app.config['UPLOAD_FOLDER'] = './output'

@app.route('/postexample', methods=['POST'])
def postexample():
    filename = 'output.png'
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return "Sent\n"


@app.route('/postarg', methods=['POST'])
def postarg():
    if request.headers['Content-Type'] == 'text/plain':
        return "OBWK: " + str(request.data) + "\n"
    elif request.headers['Content-Type'] == 'application/json':
        if request.json["login"] != "" and request.json["password"] != "":
            return "Compte en attente de validation\n"
        else:
            return "Veuillez compléter le nom d'utilisateur et le mot de passe\n"
    return "NOK"

# Route permettant la création de la table students
@app.route('/createmanu')
def createmanu():
    conn = sqlite3.connect('database.db')
    print("Opened database successfully")
    conn.execute(
        'CREATE TABLE students (name TEXT, addr TEXT, city TEXT, pin TEXT)')
    print("Table created successfully")
    conn.close()
    return 'Your table is created.'

# Fonction qui retourne un boolean
# Permettant de connaitre l'existance de name dans la BD
def nameInTheDataBase(name):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    oneRecord = [name]
    cursor.execute("SELECT * FROM students WHERE name = ?", oneRecord)
    rows = cursor.fetchall()
    return len(rows) >= 1

# Route POST permettant la création d'un étudiant dans la table students
# Avec vérification de l'existance de cet étudiant
@app.route('/addmanu', methods=['POST'])
def addmanu():
    if request.headers['content-type'] == 'application/json':
        name = request.json["name"]
        addr = request.json["addr"]
        city = request.json["city"]
        pin = request.json["pin"]
        if not nameInTheDataBase(name):
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            oneRecord = [name, addr, city, pin]
            cursor.execute('INSERT INTO students VALUES (?,?,?,?)', oneRecord)
            conn.commit()
            conn.close()
            return 'OK\n'
    return str("The name " + name + " is already taken\n")

# Route POST permettant la suppression d'un étudiant de la table students
# Avec verification de l'existance de cet étudiant
@app.route('/deletemanu', methods=['POST'])
def deletemanu():
    if request.headers['content-type'] == 'application/json':
        if request.json["name"] != "":
            name = request.json["name"]
            if nameInTheDataBase(name):
                conn = sqlite3.connect('database.db')
                cursor = conn.cursor()
                oneRecord = [name]
                cursor.execute(
                    'DELETE FROM students WHERE name = ?', oneRecord)
                conn.commit()
                conn.close()
                return 'OK\n'
            else:
                return str("There are no results for the name : " + name + "\n")
    return "NOK"

# Route GET permettant de récuperer les informations d'un étudiant
@app.route('/getmanu/<name>', methods=['GET'])
def getmanu(name=None):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    oneRecord = [name]
    cursor.execute("SELECT * FROM students WHERE name = ?", oneRecord)
    rows = cursor.fetchall()
    result = ""
    for row in rows:
        result += str(row[0] + " | " + row[1] + " | " +
                      row[2] + " | " + row[3] + "\n")
    if nameInTheDataBase(name):
        return result
    else:
        return str("There are no results for the name : " + name + "\n")

# Route permettant la mise à jour d'un étudiant via son name
# Avec vérification de l'existance de cet étudiant
@app.route('/updatemanu', methods=['PUT'])
def updatemanu():
    if request.headers['content-type'] == 'application/json':
        name = request.json["name"]
        addr = request.json["addr"]
        city = request.json["city"]
        pin = request.json["pin"]
        if nameInTheDataBase(name):
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            oneRecord = [addr, city, pin, name]
            cursor.execute(
                'UPDATE students SET addr = ?, city = ?, pin = ? WHERE name = ?', oneRecord)
            conn.commit()
            conn.close()
            return 'OK\n'
    return str("The name " + name + " is already taken\n")

# Fonction qui retourne un boolean
# Permettant de savoir s'il existe un étudiant associé au mot de passe password
def nameAndPasswordExist(name, password):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    oneRecord = [name, password]
    cursor.execute(
        "SELECT * FROM students WHERE name = ? AND password = ?", oneRecord)
    rows = cursor.fetchall()
    return len(rows) >= 1

# Fonction qui retourne un String
# Permettant de générer une chaîne de 6 caractères aléatoires
def createRandomString():
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(6))

# Route permettant à l'étudiant de renseigner ses informations
# Et qui créée un identifiant unique pour le relier à la table notes
# Grâce à la fonction createRandomString()
@app.route('/subscribe', methods=['POST'])
def subscribe():
    if request.headers['content-type'] == 'application/json':
        name = request.json["name"]
        addr = request.json["addr"]
        city = request.json["city"]
        password = stringToSha256(request.json["password"])
        if not nameInTheDataBase(name):
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            oneRecord = [name, addr, city, createRandomString(), password]
            cursor.execute(
                'INSERT INTO students VALUES (?,?,?,?,?)', oneRecord)
            conn.commit()
            conn.close()
            return 'OK\n'
    return str("The name " + name + " is already taken\n")

# Fonction qui retourne un String
# Permettant de hasher une chaîne de caractères en SHA256
def stringToSha256(string):
    return hashlib.sha256(string.encode()).hexdigest()

# Route permettant de récuperer les notes au format JSON d'un étudiant à partir de son nom
# Avec vérification du mot de passe hashé en SHA256
# Et vérification de l'existance de cet étudiant dans la BDD
@app.route('/getNote', methods=['POST'])
def getNote():
    if request.headers['content-type'] == 'application/json':
        if request.json["name"] != "" and request.json["password"] != "":
            name = request.json["name"]
            password = stringToSha256(request.json["password"])
            if nameInTheDataBase(name):
                if nameAndPasswordExist(name, password):
                    conn = sqlite3.connect('database.db')
                    cursor = conn.cursor()
                    oneRecord = [name, password]
                    cursor.execute(
                        'SELECT name, note FROM students INNER JOIN notes ON students.pin = notes.id WHERE students.name = ? and students.password = ?', oneRecord)
                    rows = cursor.fetchall()
                    result = ""
                    for row in rows:
                        result += '{"note":' + str(row[1]) + '},'
                    result = "[" + result + "]"
                    return jsonify(result)
                else:
                    return str("Incorrect password\n")
            else:
                return str("There are no results for the name : " + name + "\n")
    return "NOK"

app.config['UPLOAD_STUDENTS_FOLDER'] = './students_photos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route POST permettant la mise à jour de la photo d'un étudiant
# Avec vérification de l'existance de cet étudiant
# Et vérification du mot de passe de celui-ci

# Chaque étudiant possède par défaut la photo basic.png
# Les photos sont uploadées dans le dossier ./students_photos
# Un split sur le nom du fichier est réalisé, ce qui permet d'ajouter des fichiers de types jpg, png, gif etc... dans la liste des fichiers autorises 
@app.route('/updatePhoto', methods=['POST'])
def updatePhoto():
        name = request.form["name"]
        print(name)
        password = stringToSha256(request.form["password"])
        if nameInTheDataBase(name):
            if nameAndPasswordExist(name, password):
                # Ajout de l'image au serveur dans ./students_photos
                if 'file' not in request.files:
                    flash('No file part')
                    return redirect(request.url)
                file = request.files['file']
                if file.filename == '':
                    flash('No selected file')
                    return redirect(request.url)
                # Récupère la partie après le point afin de garder le format de base (jpg, png, etc...)
                if allowed_file(file.filename):
                    extension = file.filename.split(".")[1]
                    filename = str(createRandomString() + "." + extension)
                    print(filename)
                    file.save(os.path.join(app.config['UPLOAD_STUDENTS_FOLDER'], filename))
                    # Associer le nom de l'image à l'étudiant
                    conn = sqlite3.connect('database.db')
                    cursor = conn.cursor()
                    oneRecord = [filename, name, password]
                    cursor.execute(
                        'UPDATE students SET photo = ? WHERE name = ? AND password = ?', oneRecord)
                    conn.commit()
                    conn.close()
                    return 'OK\n'
                else:
                    return str("This type of file is not allowed : " + file.filename.split(".")[1] + "\n")
            else:
                return str("Incorrect password\n")
        else:
            return str("There are no results for the name : " + name + "\n")
app.run()