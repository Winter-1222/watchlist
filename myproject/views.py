from myproject import app, db
from myproject.models import Movie, User
from flask import render_template, request, flash, redirect, url_for
from flask_login import current_user, login_required, logout_user, login_user


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