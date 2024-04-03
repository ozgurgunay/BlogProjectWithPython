from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
#new
# user register form fields and validations:
class RegisterForm(Form):
    name = StringField("Name Surname", validators=[validators.Length(min = 4, max = 25)])
    username = StringField("User Name", validators=[validators.Length(min = 5, max=25)])
    email = StringField("E-Mail", validators=[validators.Email(message="Enter valid email address!")])
    password = PasswordField("Password", validators=[
        validators.DataRequired(message="Password"),
        validators.EqualTo(fieldname="confirm", message="Check your password!")
    ])
    confirm = PasswordField("Verify Password")
# user login 
class LoginForm(Form):
    username = StringField("User Name")
    password = PasswordField("Password")

app = Flask(__name__)
app.secret_key = "blogprojectpython"

#sql config
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "blogprojectpython"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"  #bunun amacı sql den verileri alırken dictionary yapısınd alacağın anlamına geliyor.!

mysql = MySQL(app)

@app.route("/")
def index():
    return render_template("index.html")
@app.route("/about")
def about():
    return render_template("about.html")

#register part
@app.route("/register", methods = ["GET", "POST"])
def register():
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()
        sqlQuery = "INSERT INTO users(name, email, username, password) VALUES (%s, %s, %s, %s)"
        cursor.execute(sqlQuery,(name, email, username, password))
        mysql.connection.commit()
        cursor.close()
        flash("Yees, you did it!", "success")

        return redirect(url_for("login"))
    else:
        return render_template("register.html", form = form)

#login part
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()
        sqlQuery = "SELECT * FROM users WHERE UserName = %s"
        result = cursor.execute(sqlQuery,(username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data["Password"]
            if sha256_crypt.verify(password_entered, real_password):
                flash("Login successfull", "success")

                session["logged_in"] = True
                session["username"] = username

                return redirect(url_for("index"))
            else:
                flash("Incorrect Password!", "danger")
                return redirect(url_for("login"))
        else:
            flash("Doesn't exist user name!", "danger")
            return redirect(url_for("login"))
    return render_template("login.html", form = form)  

#LogOut Part
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

#Dashboard 
@app.route("/dashboard")
def dashboard():
    # cursor = mysql.connection.cursor()
    # sqlQuery = "SELECT * FROM articles WHERE author = %s"
    # result = cursor.execute(sqlQuery,(session["username"],))

    # if result > 0:
    #     articles = cursor.fetchall()
    #     return render_template("dashboard.html", articles = articles)
    # else:
    #     return render_template("dashboard.html")
    return render_template("dashboard.html")

if __name__ == "__main__":
    app.run(debug=True)
