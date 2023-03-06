######################################
# author ben lawson <balawson@bu.edu>
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
import re

#for getting current date
from datetime import date

#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__, static_folder='static')
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

login_status = False

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
	print("REQUEST:", request.form['password'], "PWD:", pwd)
	if login_status == False:
		return
	else:
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

def getPhotoDetails(pid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE picture_id = '{0}'".format(pid))
	return cursor.fetchall()

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
	login_status = True
	return render_template('register.html', suppress=False)

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
		login_status = False
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO Users (email, password, firstname, lastname, gender, hometown, birthday, score) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}')".format(email, password, firstname, lastname, gender, hometown, birthday, 0)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		login_status = True
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		print("couldn't find all tokens")
		print('oof')
		login_status = False
		return render_template('register.html', suppress=True)

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE return a list of tuples, [(imgdata, pid, caption), ...]

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def getEmailFromUserID(user_id):
    cursor = conn.cursor()
    cursor.execute("SELECT email FROM Users WHERE user_id = '{0}'".format(user_id))
    return cursor.fetchone()[0]

def getCommentId(comment):
	cursor = conn.cursor()
	cursor.execute("SELECT comment_id FROM Comments WHERE comment_id = '{0}'".format(comment))

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
@app.route('/albums/<path:subpath>/add_comment', methods=['POST'])
def add_comment(subpath):
		if "photo" in subpath:
			print("gggggggg")
			picture_id = request.form.get('picture_id')
			uid = getUserIdFromEmail(flask_login.current_user.id)
			addcomment = request.form.get('addcomment')
			cursor = conn.cursor()
			cursor.execute("INSERT INTO Comments (text) VALUES ('{0}')".format(addcomment))
			conn.commit()
			cursor.execute("SELECT comment_id FROM Comments WHERE text = '{0}'".format(addcomment))
			cid = cursor.fetchall()
			cursor.execute("INSERT INTO Has (comment_id, picture_id) VALUES ('{0}', '{1}')".format(cid[0][0], picture_id))
			conn.commit()
			cursor.execute("UPDATE Users Set score = score + 1 WHERE user_id = '{0}'".format(uid))
			conn.commit()
			cursor.execute("SELECT text FROM Comments WHERE comment_id IN (SELECT comment_id FROM Has WHERE picture_id = '{0}')".format(picture_id))
			commentsv = cursor.fetchall()
			comments_list = [(row[0]) for row in commentsv]

			cursor.execute("SELECT user_id, picture_id FROM Likes WHERE user_id = '{0}' AND picture_id = '{1}'".format(getUserIdFromEmail(flask_login.current_user.id), picture_id))
			studd = cursor.fetchall()
			if len(studd) == 0:
				liked = False
			else:
				liked = True

			cursor.execute("SELECT SUM(1) FROM Likes WHERE picture_id = '{0}'".format(picture_id))
			totalLikes = cursor.fetchall()[0][0]
			return render_template('photo.html', photo=getPhotoDetails(picture_id), comments=comments_list, notsame=True, liked=liked, totalLikes=totalLikes, base64=base64)
		else:
			#for albums
			print("<><><><><>><")
			return render_template('photos.html', photos=getAlbumPhotos(subpath), base64=base64)

@app.route('/albums/<path:subpath>/add_like', methods=['POST'])
def add_like(subpath):
		if "photo" in subpath:
			picture_id = request.form.get('picture_id')
			cursor = conn.cursor()
			cursor.execute("INSERT INTO Likes (user_id, picture_id) VALUES ('{0}', '{1}')".format(getUserIdFromEmail(flask_login.current_user.id), picture_id))
			conn.commit()
			cursor.execute("SELECT text FROM Comments WHERE comment_id IN (SELECT comment_id FROM Has WHERE picture_id = '{0}')".format(picture_id))
			commentsv = cursor.fetchall()
			comments_list = [(row[0]) for row in commentsv]
			liked=True

			cursor.execute("SELECT user_id FROM Pictures WHERE picture_id = '{0}'".format(picture_id))
			userv = cursor.fetchall()
			if userv[0][0] == getUserIdFromEmail(flask_login.current_user.id):
				nosame = False
			else:
				nosame = True

			cursor.execute("SELECT SUM(1) FROM Likes WHERE picture_id = '{0}'".format(picture_id))
			totalLikes = cursor.fetchall()[0][0]
			return render_template('photo.html', photo=getPhotoDetails(picture_id), comments=comments_list, notsame=nosame, liked=liked, totalLikes=totalLikes, base64=base64)
		else:
			#for albums
			print("<><><><><>><")
			return render_template('photos.html', photos=getAlbumPhotos(subpath), base64=base64)
		
@app.route('/albums/<path:subpath>/add_unlike', methods=['POST'])
def add_unlike(subpath):
		if "photo" in subpath:
			picture_id = request.form.get('picture_id')
			cursor = conn.cursor()
			cursor.execute("DELETE FROM Likes WHERE user_id = '{0}' AND picture_id = '{1}'".format(getUserIdFromEmail(flask_login.current_user.id), picture_id))
			conn.commit()
			cursor.execute("SELECT text FROM Comments WHERE comment_id IN (SELECT comment_id FROM Has WHERE picture_id = '{0}')".format(picture_id))
			commentsv = cursor.fetchall()
			comments_list = [(row[0]) for row in commentsv]
			liked=False

			cursor.execute("SELECT user_id FROM Pictures WHERE picture_id = '{0}'".format(picture_id))
			userv = cursor.fetchall()
			if userv[0][0] == getUserIdFromEmail(flask_login.current_user.id):
				nosame = False
			else:
				nosame = True

			cursor.execute("SELECT SUM(1) FROM Likes WHERE picture_id = '{0}'".format(picture_id))
			totalLikes = cursor.fetchall()[0][0]
			return render_template('photo.html', photo=getPhotoDetails(picture_id), comments=comments_list, notsame=nosame, liked=liked, totalLikes=totalLikes, base64=base64)
		else:
			#for albums
			print("<><><><><>><")
			return render_template('photos.html', photos=getAlbumPhotos(subpath), base64=base64)


@app.route('/albums/<path:subpath>', methods=['GET'])
def display_photos(subpath):
	print(subpath)
	if "likes" in subpath:
		ns = re.findall('\d+', subpath)
		cursor.execute("SELECT email FROM Users WHERE user_id IN (SELECT user_id FROM Likes WHERE picture_id = '{0}')".format(ns[0]))
		likesv = cursor.fetchall()
		likes_list = [(row[0]) for row in likesv]
		print(likes_list)
		return render_template('likes.html', likesby = likes_list)
	elif "photo" in subpath:
		ns = re.findall('\d+', subpath)
		nosame = True
		#for individual photos
		cursor.execute("SELECT user_id FROM Pictures WHERE picture_id = '{0}'".format(ns[0]))
		userv = cursor.fetchall()
		if userv[0][0] == getUserIdFromEmail(flask_login.current_user.id):
				nosame = False
		cursor.execute("SELECT text FROM Comments WHERE comment_id IN (SELECT comment_id FROM Has WHERE picture_id = '{0}')".format(ns[0]))
		commentsv = cursor.fetchall()
		comments_list = [(row[0]) for row in commentsv]
		cursor.execute("SELECT user_id, picture_id FROM Likes WHERE user_id = '{0}' AND picture_id = '{1}'".format(getUserIdFromEmail(flask_login.current_user.id), ns[0]))
		studd = cursor.fetchall()
		if len(studd) == 0:
			liked = False
		else:
			liked = True

		cursor.execute("SELECT SUM(1) FROM Likes WHERE picture_id = '{0}'".format(ns[0]))
		totalLikes = cursor.fetchall()[0][0]
		return render_template('photo.html', photo=getPhotoDetails(ns[0]), comments=comments_list, notsame=nosame,liked=liked, totalLikes=totalLikes, base64=base64)
	else:
		#for albums
		return render_template('photos.html', photos=getAlbumPhotos(subpath), base64=base64)

@app.route('/userAlbums', methods=['GET'])
@flask_login.login_required
def userAlbums():
	cursor = conn.cursor()
	cursor.execute("SELECT album_id, albumname FROM Albums WHERE user_id = '{0}'".format(getUserIdFromEmail(flask_login.current_user.id)))
	albumsv = cursor.fetchall()
	albums_list = [(row[1], "albums/" + str(row[0])) for row in albumsv]
	return render_template('userAlbums.html', albums=albums_list)

@app.route('/userAlbums', methods=['POST'])
@flask_login.login_required
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

@app.route('/modifyAlbums', methods=['GET'])
@flask_login.login_required
def modifyAlbums():
	cursor = conn.cursor()
	cursor.execute("SELECT album_id, albumname FROM Albums WHERE user_id = '{0}'".format(getUserIdFromEmail(flask_login.current_user.id)))
	albumsv = cursor.fetchall()
	albums_list = [(row[1], row[0]) for row in albumsv]
	return render_template('modifyAlbums.html', albums=albums_list)

@app.route('/modifyAlbums', methods=['POST'])
@flask_login.login_required
def delete_album():
	cursor = conn.cursor()
	selected_album = request.form.get('delete_album')
	cursor.execute("SELECT picture_id FROM Contains WHERE album_id = '{0}'".format(selected_album))
	picture_ids = cursor.fetchall()
	for picture_id in picture_ids:
		cursor.execute("DELETE FROM Likes WHERE picture_id = '{0}'".format(picture_id[0]))
		cursor.execute("DELETE FROM Associate WHERE picture_id = '{0}'".format(picture_id[0]))
		cursor.execute("DELETE FROM Contains WHERE picture_id = '{0}'".format(picture_id[0]))
		cursor.execute("DELETE FROM Pictures WHERE picture_id = '{0}'".format(picture_id[0]))
	cursor.execute("DELETE FROM Contains WHERE album_id = '{0}'".format(selected_album))
	cursor.execute("DELETE FROM Albums WHERE album_id = '{0}'".format(selected_album))
	conn.commit()
	cursor.execute("SELECT album_id, albumname FROM Albums WHERE user_id = '{0}'".format(getUserIdFromEmail(flask_login.current_user.id)))
	albumsv = cursor.fetchall()
	albums_list = [(row[1], row[0]) for row in albumsv]
	return render_template('modifyAlbums.html', albums=albums_list)

@app.route('/modifyPhoto/<path:subpath>', methods=['GET'])
@flask_login.login_required
def modifyPictures(subpath):
	return render_template('modifyPictures.html', photos=getAlbumPhotos(subpath), base64=base64, album_id=subpath)

@app.route('/modifyPhoto/<path:subpath>', methods=['POST'])
@flask_login.login_required
def delete_photo(subpath):
	pid = request.form.get('picture_id')
	cursor = conn.cursor()
	cursor.execute("DELETE FROM Has WHERE picture_id = '{0}'".format(pid))
	cursor.execute("DELETE FROM Comments WHERE comment_id IN (SELECT comment_id FROM Has WHERE picture_id = '{0}')".format(pid))
	cursor.execute("DELETE FROM Likes WHERE picture_id = '{0}'".format(pid))
	cursor.execute("DELETE FROM Associate WHERE picture_id = '{0}'".format(pid))
	cursor.execute("DELETE FROM Contains WHERE picture_id = '{0}'".format(pid))
	cursor.execute("DELETE FROM Pictures WHERE picture_id = '{0}'".format(pid))
	conn.commit()
	return render_template('modifyPictures.html', photos=getAlbumPhotos(subpath), base64=base64, album_id=subpath)


@app.route("/friends", methods=['GET'])
@flask_login.login_required
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
	
@app.route('/friendRecs', methods=['GET'])
@flask_login.login_required
def display_recs():
	user_id = getUserIdFromEmail(flask_login.current_user.id)
	cursor.execute("SELECT user_id2 FROM Friends WHERE user_id1 = '{0}'".format(user_id))
	friendsv = cursor.fetchall()
	friends_list = []
	for i in range(len(friendsv)):
		cursor.execute("SELECT email FROM Users WHERE user_id = '{0}'".format(friendsv[i][0]))
		result = cursor.fetchall()
		if result:
			friends_list.append(result[0][0])
	recommendations = {}
	for friend in friends_list:
		cursor.execute("SELECT user_id2 FROM Friends WHERE user_id1 = '{0}'".format(getUserIdFromEmail(friend)))
		friend_friends = cursor.fetchall()
		for friend_friend in friend_friends:
			friend_email = getEmailFromUserID(friend_friend[0])
			if friend_email != user_id and friend_email not in friends_list:
				if friend_email not in recommendations:
					recommendations[friend_email] = 1
				else:
					recommendations[friend_email] += 1
	sorted_recommendations = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)
	recommendations_list = [x[0] for x in sorted_recommendations]
	for i in range(len(recommendations_list)):
		if recommendations_list[i] == getEmailFromUserID(user_id):
			recommendations_list.pop(i)
			break
	print("DONE")
	print(recommendations_list)
	return render_template('friendRecs.html', users=recommendations_list)

@app.route('/friendRecs', methods=['POST'])
@flask_login.login_required
def friendRecs():
	#code here

	return render_template('friendRecs.html')

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
		cursor.execute("UPDATE Users Set score = score + 1 WHERE user_id = '{0}'".format(uid))
		conn.commit()
		tag_num = 1
		added_words = []
		while True:
			try:
				tag_val = request.form.get("tag" + str(tag_num))
				if tag_val == None:
					break
				tag_num += 1
				if tag_val != "":
					if tag_val not in added_words:
						added_words.append(tag_val)
						if cursor.execute("SELECT word FROM Tag WHERE word = '{0}'".format(tag_val)) == 0:
							cursor.execute("INSERT INTO Tag (word) VALUES ('{0}')".format(tag_val))
							conn.commit()
							cursor.execute("INSERT INTO Associate (picture_id, word) VALUES ('{0}', '{1}')".format(pid[-1][0], tag_val))
							conn.commit()
						else:
							cursor.execute("INSERT INTO Associate (picture_id, word) VALUES ('{0}', '{1}')".format(pid[-1][0], tag_val))
							conn.commit()
				elif tag_val == None:
					break
			except:
				break
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

@app.route('/leaderboard', methods=['GET'])
def display_leaderboard():
	cursor = conn.cursor()
	cursor.execute("SELECT email,score FROM USERS ORDER BY score DESC LIMIT 10")
	leaderboardv = cursor.fetchall()
	leaderboard_list = [(row[0], row[1]) for row in leaderboardv]
	cursor.execute("SELECT Tag.word, COUNT(*) AS count FROM Tag JOIN Associate ON Tag.word = Associate.word GROUP BY Tag.word ORDER BY count DESC LIMIT 3")
	tagleaderboardv = cursor.fetchall()
	tagleaderboard_list = [(row[0], row[1]) for row in tagleaderboardv]
	return render_template('leaderboard.html', leaderboard=leaderboard_list, tagleaderboard=tagleaderboard_list)


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

@app.route("/minimal-table.css", methods=['Get'])
def tableDesign():
	return render_template('minimal-table.css')


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
