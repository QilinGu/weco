# coding:utf-8

from flask import *
from weco import app
from weco import connectdb,closedb
import random
from hashlib import md5
import time

# 随机码生成器
def genKey():
	key = ''
	for x in xrange(0, 10):
		key = key + str(random.randint(0, 9))
	key = unicode(md5(key + str(int(time.time()))).hexdigest().upper())
	return key

# 存储当前页面
@app.route('/storeCurrentUrl',methods=['POST'])
def storeCurrentUrl():
	session['url'] = request.form['url']
	return json.dumps({"ok": True})

# 登陆
@app.route('/login', methods=['GET','POST'])
def login():
	error = None
	if request.method == 'GET':
		if not session.get('username') == None:
			return redirect(url_for('index'))
		else:
			return render_template('user/login.html', error=error)
	elif request.method == 'POST':
		username = request.form['username']
		if username == '':
			error = u"请输入账号或手机号"
			return render_template('user/login.html', error=error)
		password = request.form['password']
		if password == '':
			error = u"请输入密码"
			return render_template('user/login.html', error=error)
		(db,cursor) = connectdb()
		if cursor.execute("select id from user where username=%s or email=%s", [username,username]) == 0:
			error = u"账号或手机号不存在"
			closedb(db,cursor)
			return render_template('user/login.html', error=error)
		elif cursor.execute("select id from user where username=%s and password=%s", [username,unicode(md5(password).hexdigest().upper())]) + cursor.execute("select id from user where email=%s and password=%s", [username,unicode(md5(password).hexdigest().upper())]) == 0:
			error = u"账号或密码错误"
			closedb(db,cursor)
			return render_template('user/login.html', error=error)
		else:
			cursor.execute("update user set lastActive=%s,token=%s where username=%s or email=%s",[str(int(time.time())),genKey(),username,username])
			cursor.execute("select username,lastActive,token from user where username=%s or email=%s",[username,username])
			user = cursor.fetchone()
			session['username'] = user['username']
			session['token'] =  user['token']
			session['lastActive'] = user['lastActive']

			closedb(db,cursor)
			
			if not session.get('url') == None:
				url = session.get('url')
				session.pop('url', None)
				return redirect(url)
			else:
				return redirect(url_for('index'))

# 注销
@app.route('/logout')
def logout():
	if not session.get('username') == None:
		session.pop('username', None)
		session.pop('token', None)
		session.pop('lastActive', None)

		return redirect(url_for('login'))
	else:
		return redirect(url_for('login')) 

# 注册
@app.route('/', methods=['GET','POST'])
def register():
	if request.method == 'GET':
		if not session.get('username') == None:
			return redirect(url_for('index'))
		else:
			return render_template('user/register.html')
	elif request.method == 'POST':
		username = request.form['username']
		password = request.form['password']
		email = request.form['email']
		(db,cursor) = connectdb()
		cursor.execute("insert into user(username,nickname,password,email) values(%s,%s,%s,%s)", [username,username,unicode(md5(password).hexdigest().upper()),email])

		# 注册完毕，直接登录
		cursor.execute("update user set lastActive=%s, token=%s, TTL=100 where username=%s and email=%s",[str(int(time.time())),genKey(),username,email])
		cursor.execute("select username, token, lastActive from user where username=%s and email=%s", [username,email])
		user = cursor.fetchone()
		closedb(db,cursor)
		session['username'] = user['username']
		session['token'] =  user['token']
		session['lastActive'] = user['lastActive']
		if not session.get('url') == None:
			url = session.get('url')
			session.pop('url', None)
			return redirect(url)
		else:
			return redirect(url_for('index'))

# 更改密码
@app.route('/changePwd', methods=['GET','POST'])
def changePwd():
	if request.method == 'GET':
		if not session.get('username') == None:
			return render_template('user/changePwd.html',error='')
		else:
			return redirect(url_for('login'))
	elif request.method == 'POST':
		if not session.get('username') == None:
			username = session.get('username')
			oldpassword = request.form['oldpassword']
			newpassword = request.form['newpassword']
			newpassword1 = request.form['newpassword1']
			(db,cursor) = connectdb()
			if cursor.execute('select id from user where username=%s and password=%s',[username,unicode(md5(oldpassword).hexdigest().upper())]) == 0:
				closedb(db,cursor)
				return render_template('user/changePwd.html',error='原始密码错误')
			elif not newpassword == newpassword1:
				closedb(db,cursor)
				return render_template('user/changePwd.html',error='两次密码输入不一致')
			else:
				cursor.execute('update user set password=%s where username=%s',[unicode(md5(newpassword).hexdigest().upper()),username])
				closedb(db,cursor)
				return redirect(url_for('logout'))
		else:
			return redirect(url_for('login'))
		
