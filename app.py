import sys

from flask import Flask, render_template, request, flash, redirect
from markupsafe import escape
from flask import url_for
from flask_sqlalchemy import SQLAlchemy
import os
import click
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, current_user
from flask_login import UserMixin
from flask_login import login_user
from flask_login import login_required, logout_user

WIN = sys.platform.startswith('win')
if WIN:  # 如果是 Windows 系统，使用三个斜线
    prefix = 'sqlite:///'
else:  # 否则使用四个斜线
    prefix = 'sqlite:////'

app = Flask(__name__)
# 设置密钥
app.secret_key = 'my_secret_key'
# 在扩展类实例化前加载配置
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(app.root_path, 'data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控
# 初始化扩展，传入程序实例 app
db = SQLAlchemy(app)


# 创建数据库模型
class User(db.Model, UserMixin):  # 表名将会是user 自动生成
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    username = db.Column(db.String(20))
    password_hash = db.Column(db.String(128))  # 密码散列值

    def set_password(self, password):  # 用来设置密码的方法，接受密码作为参数
        self.password_hash = generate_password_hash(password)  # 将生成的密码保持到对应字段

    def validate_password(self, password):  # 用于验证密码的方法，接受密码作为参数
        return check_password_hash(self.password_hash, password)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(60))
    year = db.Column(db.String(4))


@app.cli.command()  # 注册为命令，可以传入 name 参数来自定义命令
@click.option('--drop', is_flag=True, help='Create after drop.')  # 设置选项
def initdb(drop):
    """Initialize the database."""
    if drop:  # 判断是否输入了选项
        db.drop_all()
    db.create_all()
    click.echo('Initialized database.')  # 输出提示信息


@app.cli.command()
def forge():
    db.create_all()
    movies = [
        {'title': 'My Neighbor Totoro', 'year': '1988'},
        {'title': 'Dead Poets Society', 'year': '1989'},
        {'title': 'A Perfect World', 'year': '1993'},
        {'title': 'Leon', 'year': '1994'},
        {'title': 'Mahjong', 'year': '1996'},
        {'title': 'Swallowtail Butterfly', 'year': '1996'},
        {'title': 'King of Comedy', 'year': '1999'},
        {'title': 'Devils on the Doorstep', 'year': '1999'},
        {'title': 'WALL-E', 'year': '2008'},
        {'title': 'The Pork of Music', 'year': '2012'},
    ]
    for m in movies:
        movie = Movie(title=m['title'], year=m['year'])
        db.session.add(movie)
    db.session.commit()
    click.echo('添加完毕~')


@app.context_processor
def inject_user():
    user = User.query.first()
    return dict(user=user)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if not current_user.is_authenticated:  # 如果当前用户未认证
            return redirect(url_for('index'))  # 重定向到主页
        title = request.form.get('title')
        year = request.form.get('year')

        if not title or not year or len(year) > 4 or len(title) > 60:
            flash('不合法的输入')
            return redirect(url_for('index'))

        movie = Movie(title=title, year=year)
        db.session.add(movie)
        db.session.commit()
        flash('添加成功！')
        return redirect(url_for('index'))
    movies = Movie.query.all()
    return render_template('index.html', movies=movies)


@app.errorhandler(404)  # 传入要处理的错误代码
def page_not_found(e):  # 接受异常对象作为参数
    return render_template('404.html'), 404  # 返回模板和状态码


@app.route('/movie/edit/<int:movie_id>', methods=['GET', 'POST'])
@login_required
def edit(movie_id):  # 传入的参数是当点击编辑按钮时带过来的，用于查找到当前的操作对象movie
    movie = Movie.query.get_or_404(movie_id)
    if request.method == 'POST':  # 如果是post请求，是进行修改
        title = request.form['title']
        year = request.form['year']
        if not title or not year or len(year) > 4 or len(title) > 60:
            flash('不合法的输入')
            return redirect(url_for('edit', movie_id=movie_id))  # 重定向回对应的编辑页面
        movie.title = title
        movie.year = year
        db.session.commit()
        flash('修改成功！')
        return redirect(url_for('index'))
    # get请求，返回编辑的渲染页面，并将movie带过去回显数据
    return render_template('edit.html', movie=movie)


@app.route('/movie/delete/<int:movie_id>', methods=['POST'])
@login_required  # 登录保护
def delete(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)  # 删除对应的记录
    db.session.commit()  # 提交数据库会话
    flash('删除成功')
    return redirect(url_for('index'))  # 重定向回主页


@app.cli.command()
@click.option('--username', prompt=True)
@click.option('--password', prompt=True, hide_input=True)
def admin(username, password):
    db.create_all()
    user = User.query.first()
    if user is not None:
        click.echo('更改信息中....')
        user.username = username
        user.set_password(password)
    else:
        click.echo('创建用户中....')
        user = User(username=username, name='Admin')
        user.set_password(password)
        db.session.add(user)
    db.session.commit()
    click.echo('完成！')


login_manager = LoginManager(app)  # 实例化扩展类
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):  # 创建用户加载回调函数，接受用户 ID 作为参数
    user = User.query.get(int(user_id))  # 用 ID 作为 User 模型的主键查询对应的用户
    return user  # 返回用户对象


@app.route('/login', methods=['GET', 'POST'])
def login():
    # 如果是post请求，验证表单提交的数据
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if not username or not password:
            flash('请输入用户名或密码！')
            return redirect(url_for('login'))
        # 获取user表中的第一个数据，也就是管理员
        user = User.query.first()
        # 验证用户名和密码是否一致
        if username == user.username and user.validate_password(password):
            # 登入用户 记录下来
            login_user(user)
            flash('登录成功!')
            return redirect(url_for('index'))  # 转到主页
        # 未通过验证
        flash('用户名或密码错误')
        return redirect(url_for('login'))  # 重新回到登录页面
    # get请求 渲染页面
    return render_template('login.html')


@app.route('/logout')
@login_required  # 用于视图保护
def logout():
    logout_user()  # 登出用户
    flash('Goodbye.')
    return redirect(url_for('index'))  # 重定向回首页


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        name = request.form['name']
        if not name or len(name) > 20:
            flash('用户名不合法！')
            return redirect(url_for('settings'))
        current_user.name = name
        # current_user 会返回当前登录用户的数据库记录对象
        # 等同于下面的用法
        # user = User.query.first()
        # user.name = name
        db.session.commit()
        flash('修改成功！')
        return redirect(url_for('index'))
    return render_template('settings.html')