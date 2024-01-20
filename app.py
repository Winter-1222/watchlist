from flask import Flask
from markupsafe import escape
from flask import url_for

app = Flask(__name__)

@app.route('/')
def hello():
    return '<h1>Hello Totoro!</h1><img src="http://helloflask.com/totoro.gif">'

@app.route('/user/<name>')
def user_page(name):
    return f'User:{escape(name)}'

@app.route('/test_url_for')
def test_url_for():
    print(url_for('hello'))
    print(url_for('user_page', name='wangdong'))
    print(url_for('test_url_for', num=2))
    return '<h1>Test url_for!</h1><img src="http://helloflask.com/totoro.gif">'