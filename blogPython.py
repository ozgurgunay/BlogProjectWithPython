from flask import Flask, render_template, flash, redirect, url_for, session, logging, request
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

# user login decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Please login for this page.", "danger")
            return redirect(url_for("login"))
    return decorated_function

# user register form fields and validations
class RegisterForm(Form):
    name = StringField("Name Surname", validators=[validators.Length(min = 4, max = 25)])
    username = StringField("User Name", validators=[validators.Length(min = 5, max=25)])
    email = StringField("E-Mail", validators=[validators.Email(message="Enter valid email address!")])
    password = PasswordField("Password", validators=[
        validators.DataRequired(message="Password"),
        validators.EqualTo(fieldname="confirm", message="Check your password!")
    ])
    confirm = PasswordField("Verify Password")

# Article Form
class ArticleForm(Form):
    title = StringField("Title",validators=[validators.Length(min = 5,max = 100)])
    content = TextAreaField("content",validators=[validators.Length(min = 10)])

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
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    sqlQuery = "SELECT * FROM articles WHERE Author = %s"
    result = cursor.execute(sqlQuery,(session["username"],))

    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html", articles = articles)
    else:
        return render_template("dashboard.html")

# Add Article
@app.route("/addArticle", methods = ["GET", "POST"])
def addarticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data
        
        #article save to database
        cursor = mysql.connection.cursor()
        sqlQuery = "INSERT INTO articles(title, author, content) VALUES(%s, %s, %s)"
        cursor.execute(sqlQuery, (title, session["username"], content))
        mysql.connection.commit()
        cursor.close()

        flash("Article added successfly", "success")
        return redirect(url_for("dashboard"))

    return render_template("addArticle.html", form = form)

# Delete Article
@app.route("/delete/<string:Id>")
@login_required
def delete(Id):
    cursor = mysql.connection.cursor()
    sqlQuery = "SELECT * FROM articles WHERE author = %s and Id = %s"
    result = cursor.execute(sqlQuery,(session["username"],Id))

    if result > 0:
        deleteQuery = "DELETE FROM articles WHERE Id = %s"
        cursor.execute(deleteQuery,(Id,))
        mysql.connection.commit()

        return redirect(url_for("dashboard"))
    else:
        flash("No such article exist or you're not authorized for this operation!", "danger")
        return redirect(url_for("index"))

# Update Article
@app.route("/edit/<string:Id>", methods = ["GET", "POST"])
@login_required
def update(Id):
    #GET Request
    if request.method == "GET":
        cursor = mysql.connection.cursor()
        sqlQuery = "SELECT * FROM articles WHERE Id = %s AND Author = %s"
        result = cursor.execute(sqlQuery,(Id,session["username"]))

        if result == 0:
            flash("","danger")
            return redirect(url_for("index"))
        else:
            article = cursor.fetchone()
            form = ArticleForm()
            form.title.data = article["Title"]
            form.content.data = article["Content"]
            return render_template("update.html", form = form)
    else:
        #POST Request
        form = ArticleForm(request.form)
        newTitle = form.title.data
        newContent = form.content.data
        #sql connection and query
        sqlQueryUpdate = "UPDATE articles SET Title = %s, Content = %s WHERE Id = %s"
        cursor = mysql.connection.cursor()
        cursor.execute(sqlQueryUpdate,(newTitle, newContent, Id))
        mysql.connection.commit()
        flash("Article updated successfly.","success")
        return redirect(url_for("dashboard"))

# Search Article
@app.route("/search",methods = ["GET","POST"])
def search():
   if request.method == "GET":
       return redirect(url_for("index"))
   else:
       keyword = request.form.get("keyword")
       cursor = mysql.connection.cursor()
       sqlQuery = "SELECT * FROM articles WHERE Title LIKE '%" + keyword +"%'"
       result = cursor.execute(sqlQuery)
       if result == 0:
           flash("No result!","warning")
           return redirect(url_for("articles"))
       else:
           articles = cursor.fetchall()
           return render_template("articles.html",articles = articles)

# Article Page
@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()
    sqlQuery = "SELECT * FROM articles"
    result = cursor.execute(sqlQuery)

    if result > 0:
        articles = cursor.fetchall()
        return render_template("articles.html",articles = articles)
    else:
        return render_template("articles.html")

#Detail Page
@app.route("/article/<string:id>")
def article(id):
    cursor = mysql.connection.cursor()
    sqlQuery = "SELECT * FROM articles WHERE id = %s"
    result = cursor.execute(sqlQuery,(id,))
    if result > 0:
        article = cursor.fetchone()
        return render_template("article.html", article = article)
    else:
        return render_template("article.html")

if __name__ == "__main__":
    app.run(debug=True)
