######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>, Kevin Kim <kevkim@bu.edu>, Jiahao Huamani <jhuamani@bu.edu>
# Group project by: Kevin Kim <kevkim@bu.edu>, Jiahao Huamani <jhuamani@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login

#for getting current date
from datetime import date

#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'cs460projectkevinkimjiahaohuamani'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'cs460cs460'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

def getAlbumPhotos(aid):
    cursor = conn.cursor()
    cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE picture_id IN (SELECT picture_id FROM Contains WHERE album_id = '{0}')".format(aid))
    return cursor.fetchall() #NOTE return a list of tuples, [(imgdata, pid, caption), ...]

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='email' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
		firstname=request.form.get('firstname')
		lastname=request.form.get('lastname')
		gender=request.form.get('gender')
		hometown=request.form.get('hometown')
		birthday=request.form.get('birthday')
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO Users (email, password, firstname, lastname, gender, hometown, birthday) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}')".format(email, password, firstname, lastname, gender, hometown, birthday)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		print("couldn't find all tokens")
		return flask.redirect(flask.url_for('register'))

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE return a list of tuples, [(imgdata, pid, caption), ...]

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code

@app.route('/profile')
@flask_login.login_required
def protected():
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile")

@app.route('/albums/<path:subpath>', methods=['GET'])
def display_photos(subpath):
    return render_template('photos.html', photos=getAlbumPhotos(subpath), base64=base64)

@app.route('/userAlbums', methods=['GET'])
def userAlbums():
	cursor = conn.cursor()
	cursor.execute("SELECT album_id, albumname FROM Albums WHERE user_id = '{0}'".format(getUserIdFromEmail(flask_login.current_user.id)))
	albumsv = cursor.fetchall()
	albums_list = [(row[1], "albums/" + str(row[0])) for row in albumsv]
	return render_template('userAlbums.html', albums=albums_list)

@app.route('/userAlbums', methods=['POST'])
def add_album():
	albumname=request.form.get('albumname')
	cursor = conn.cursor()
	print(albumname)
	cursor.execute("INSERT INTO Albums (date, albumname, user_id) VALUES ('{0}', '{1}', '{2}')".format(date.today(), albumname, getUserIdFromEmail(flask_login.current_user.id)))
	conn.commit()
	cursor.execute("SELECT album_id, albumname FROM Albums WHERE user_id = '{0}'".format(getUserIdFromEmail(flask_login.current_user.id)))
	albumsv = cursor.fetchall()
	albums_list = [(row[1], row[0]) for row in albumsv]
	return render_template('userAlbums.html', albums=albums_list)

@app.route("/friends", methods=['GET'])
def friends():
	cursor.execute("SELECT user_id2 FROM Friends WHERE user_id1 = '{0}'".format(getUserIdFromEmail(flask_login.current_user.id)))
	friendsv = cursor.fetchall()
	friends_list = []
	for i in range(len(friendsv)):
		cursor.execute("SELECT email FROM Users WHERE user_id = '{0}'".format(friendsv[i][0]))
		result = cursor.fetchall()
		if result:
			friends_list.append(result[0][0])
	return render_template('friends.html', friends=friends_list)

@app.route('/friends', methods=['POST'])
@flask_login.login_required
def add_friend():
	addfriend = request.form.get('addfriend')
	print("XXX_DATA_XXX:", addfriend)
	if cursor.execute("SELECT email FROM Users WHERE email = '{0}'".format(addfriend)) and cursor.execute("SELECT * FROM Friends WHERE user_id2 = '{0}' AND user_id1 = '{1}'".format(getUserIdFromEmail(addfriend), getUserIdFromEmail(flask_login.current_user.id))) == 0:
		print(1)
		friend_id = getUserIdFromEmail(addfriend)
		cursor.execute("INSERT INTO Friends (user_id1, user_id2) VALUES ('{0}', '{1}')".format(getUserIdFromEmail(flask_login.current_user.id), friend_id))
		conn.commit()
		cursor.execute("INSERT INTO Friends (user_id1, user_id2) VALUES ('{0}', '{1}')".format(friend_id, getUserIdFromEmail(flask_login.current_user.id)))
		conn.commit()
		cursor.execute("SELECT user_id2 FROM Friends WHERE user_id1 = '{0}'".format(getUserIdFromEmail(flask_login.current_user.id)))
		friendsv = cursor.fetchall()
		friends_list = []
		for i in range(len(friendsv)):
			cursor.execute("SELECT email FROM Users WHERE user_id = '{0}'".format(friendsv[i][0]))
			result = cursor.fetchall()
			if result:
				friends_list.append(result[0][0])
		return render_template('friends.html', friends=friends_list)
	else:
		print(2)
		cursor.execute("SELECT user_id2 FROM Friends WHERE user_id1 = '{0}'".format(getUserIdFromEmail(flask_login.current_user.id)))
		friendsv = cursor.fetchall()
		friends_list = []
		for i in range(len(friendsv)):
			cursor.execute("SELECT email FROM Users WHERE user_id = '{0}'".format(friendsv[i][0]))
			result = cursor.fetchall()
			if result:
				friends_list.append(result[0][0])
		return render_template('friends.html', friends=friends_list)

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		photo_data =imgfile.read()
		cursor = conn.cursor()
		selected_album = request.form.get('album')
		print(selected_album)
		cursor.execute("INSERT INTO Pictures (imgdata, user_id, caption) VALUES (%s, %s, %s )", (photo_data, uid, caption))
		conn.commit()
		cursor.execute("SELECT album_id FROM Albums WHERE albumname = '{0}'".format(selected_album))
		aid = cursor.fetchall()
		cursor.execute("SELECT picture_id FROM Pictures WHERE user_id = '{0}'".format(getUserIdFromEmail(flask_login.current_user.id)))
		pid = cursor.fetchall()
		print("aid: ", aid)
		print("pid: ", pid)
		cursor.execute('''INSERT INTO Contains (album_id, picture_id) VALUES (%s, %s)''', (aid[0][0], pid[-1][0]))
		conn.commit()
		return render_template('photos.html', photos=getAlbumPhotos(aid[0][0]), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		print("oo")
		cursor = conn.cursor()
		cursor.execute("SELECT album_id, albumname FROM Albums WHERE user_id = '{0}'".format(getUserIdFromEmail(flask_login.current_user.id)))
		albumsv = cursor.fetchall()
		albums_list = [row[1] for row in albumsv]
		print(albums_list)
		return render_template('upload.html', albums=albums_list)
#end photo uploading code

@app.route('/albums', methods=['GET'])
def display_albums():
	cursor = conn.cursor()
	cursor.execute("SELECT album_id, albumname FROM Albums")
	albumsv = cursor.fetchall()
	albums_list = [(row[1], "albums/" + str(row[0])) for row in albumsv]
	return render_template('albums.html', albums=albums_list)


#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welecome to Photoshare')

@app.route("/utils/test.html", methods=['Get'])
def test():
	return render_template('test.html')

@app.route("/utils/script.js", methods=['Get'])
def javascript():
	return render_template('script.js')


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
