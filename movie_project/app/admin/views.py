# !/user/bin/env python
# -*- coding:utf-8 -*- 
# time: 2018/3/7--19:52
__author__ = 'Henry'

from . import admin
from flask import render_template, url_for, redirect, flash, session, request, abort
from app.admin.forms import LoginForm, TagForm, MovieForm, PreviewForm, PwdForm, AuthForm, RoleForm, AdminForm
from app.models import Admin, Tag, Movie, Preview, User, Comment, Moviecol, Oplog, Adminlog, Userlog, Auth, Role
from functools import wraps  # 装饰器(用于访问控制)
from werkzeug.utils import secure_filename  # 将filename转化成安全的名称
from app import db, app
import os, stat
import uuid  # 生成唯一标志符
import datetime
from werkzeug.security import generate_password_hash


# 上下应用处理器(封装全局变量,展现到模板里)
@admin.context_processor
def tpl_extra():
    data = dict(
        online_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 登录在线时间
    )
    return data


# 后台访问控制装饰器(只能登录后才能访问,不能直接敲网址就可以访问)
def admin_login_req(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin' not in session:  # if session['admin'] is None:
            return redirect(url_for('admin.login', next=request.url))
        return f(*args, **kwargs)

    return decorated_function


# 管理员角色访问控制装饰器(电影管理员只能访问电影模块的网址)
def admin_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin = Admin.query.join(
            Role
        ).filter(
            Role.id == Admin.role_id,
            Admin.id == session['admin_id']
        ).first()
        auths = admin.role.auths
        auths = list(map(lambda v: int(v), auths.split(',')))
        auth_list = Auth.query.all()
        urls = [v.url for v in auth_list for val in auths if val == v.id]
        rule = request.url_rule
        if str(rule) not in urls:
            abort(404)  # 角色没有权限,就抛出异常,返回404页面
        return f(*args, **kwargs)

    return decorated_function


# 修改上传的文件名称 (注意:不能上传带中文的文件!!!!!!)
def change_filename(filename):
    # fileinfo = os.path.splitext(filename)  # 取出上传的文件名的后缀(.MP4)
    fileinfo = filename.split('.')  # 取出上传的文件名的后缀(.MP4)
    filename = datetime.datetime.now().strftime('%Y%m%d%H%M%S') + str(uuid.uuid4().hex) + '.' + fileinfo[-1]
    return filename


# 后台首页
@admin.route('/')
@admin_login_req
@admin_auth
def index():
    return render_template('admin/index.html')


# 后台登录
@admin.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        data = form.data
        admin = Admin.query.filter_by(name=data['account']).first()
        if not admin.check_pwd(data['pwd']):
            flash('密码错误!', 'err')
            return redirect(url_for('admin.login'))
        # 保存session会话
        session['admin'] = data['account']  # 如果密码正确,登录成功后添加保持会话,保存管理员账号 # session['admin'] = request.form['account']
        session['admin_id'] = admin.id  # 保存管理员ID(用作日志)
        # 将登录操作添加到管理员登录日志列表
        adminlog = Adminlog(
            admin_id=session['admin_id'],
            ip=request.remote_addr
        )
        db.session.add(adminlog)
        db.session.commit()
        return redirect(request.args.get('next') or url_for('admin.tag_add'))

    return render_template('admin/login.html', form=form)


# 登出
@admin.route('/logout/')
@admin_login_req
def logout():
    session.pop('admin', None)  # 删除会话,删管理员账号
    session.pop('admin_id', None)  # 删除管理员ID
    return redirect(url_for('admin.login'))


# 修改密码
@admin.route('/pwd/', methods=['GET', 'POST'])
@admin_login_req
def pwd():
    form = PwdForm()
    if form.validate_on_submit():
        data = form.data
        admin = Admin.query.filter_by(name=session['admin']).first()
        admin.pwd = generate_password_hash(data['new_pwd'])
        db.session.add(admin)
        db.session.commit()
        flash('修改密码成功!请重新登录!', 'ok')
        return redirect(url_for('admin.logout'))
    return render_template('admin/pwd.html', form=form)


# 标签管理
# 1.添加标签
@admin.route('/tag/add/', methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def tag_add():
    form = TagForm()
    if form.validate_on_submit():
        data = form.data
        tag = Tag.query.filter_by(name=data['name']).count()
        if tag == 1:
            flash('标签名已存在!', 'err')  # 'err':表示错误信息
            return redirect(url_for('admin.tag_add'))
        # 添加新标签名入库
        tag = Tag(
            name=data['name']
        )
        db.session.add(tag)
        db.session.commit()
        flash('添加标签成功!', 'ok')  # 'ok':表示成功信息
        # 添加管理员对标签的操作到操作日志列表
        oplog = Oplog(
            admin_id=session['admin_id'],
            ip=request.remote_addr,  # 获取ip地址
            reason='添加标签:' + data['name']
        )
        db.session.add(oplog)
        db.session.commit()
        return redirect(url_for('admin.tag_add'))
    return render_template('admin/tag_add.html', form=form)


# 2.标签列表
@admin.route('/tag/list/<int:page>/', methods=['GET'])
@admin_login_req
@admin_auth
def tag_list(page=None):
    if page == None:
        page = 1
    # 按标签添加的时间排序显示
    page_data = Tag.query.order_by(
        Tag.addtime.desc()
    ).paginate(page=page, per_page=10)  # (传入要显示的页码,每页显示的标签个数)
    return render_template('admin/tag_list.html', page_data=page_data)


# 3.标签删除
@admin.route('/tag/del/<int:id>/', methods=['GET'])
@admin_login_req
@admin_auth
def tag_del(id=None):
    tag = Tag.query.filter_by(id=id).first_or_404()  # 查询失败直接返回404
    db.session.delete(tag)
    db.session.commit()
    flash('删除标签成功!', 'ok')

    # 添加删除标签操作到操作日志列表
    oplog = Oplog(
        admin_id=session['admin_id'],
        ip=request.remote_addr,
        reason='删除标签:' + tag.name
    )
    db.session.add(oplog)
    db.session.commit()
    return redirect(url_for('admin.tag_list', page=1))


# 4.编辑标签
@admin.route('/tag/edit/<int:id>/', methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def tag_edit(id=None):
    form = TagForm()
    tag = Tag.query.get_or_404(id)
    if form.validate_on_submit():
        data = form.data
        tag_count = Tag.query.filter_by(name=data['name']).count()
        if tag.name != data['name'] and tag_count == 1:
            flash('标签名已存在!', 'err')  # 'err':表示错误信息
            return redirect(url_for('admin.tag_edit', id=id))
        # 编辑(更改)标签名
        tag.name = data['name']
        db.session.add(tag)
        db.session.commit()
        flash('修改标签成功!', 'ok')  # 'ok':表示成功信息
        return redirect(url_for('admin.tag_edit', id=id))
    return render_template('admin/tag_edit.html', form=form, tag=tag)


# 电影管理
# 1.添加电影
@admin.route('/movie/add/', methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def movie_add():
    form = MovieForm()
    if form.validate_on_submit():
        data = form.data
        movie = Movie.query.filter_by(title=data['title']).count()
        if movie == 1:
            flash('该电影已存在!', 'err')  # 'err':表示错误信息
            return redirect(url_for('admin.movie_add'))
        # 保存上传的电影视频及封面
        file_url = secure_filename(form.url.data.filename)  # 生成上传的电影视频的文件名,并安全加密
        file_logo = secure_filename(form.logo.data.filename)  # 生成上传的电影封面的文件名,并安全加密
        if not os.path.exists(app.config['UP_DIR']):  # 没有就创建文件夹
            os.makedirs(app.config['UP_DIR'])
            # os.chmod(app.config['UP_DIR'], 'rw')  # 给文件夹可读可写的权限,这样才能保存文件呀
            os.chmod(app.config['UP_DIR'], stat.S_IRWXU)  # 给文件夹可读可写的权限,这样才能保存文件呀 'rw'
        # 修改为固定格式的文件名
        url = change_filename(file_url)
        logo = change_filename(file_logo)
        # 保存文件
        form.url.data.save(app.config['UP_DIR'] + url)
        form.logo.data.save(app.config['UP_DIR'] + logo)
        # 添加新电影入库
        movie = Movie(
            title=data['title'],
            url=url,
            info=data['info'],
            logo=logo,
            star=int(data['star']),
            playnum=0,
            commentnum=0,
            tag_id=int(data['tag_id']),
            area=data['area'],
            release_time=data['release_time'],
            length=data['length']
        )
        db.session.add(movie)
        db.session.commit()
        flash('添加新电影成功!', 'ok')  # 'ok':表示成功信息

        # 将添加电影操作保存到操作日志列表
        oplog = Oplog(
            admin_id=session['admin_id'],
            ip=request.remote_addr,
            reason='添加电影:《' + movie.title + '》'
        )
        db.session.add(oplog)
        db.session.commit()
        return redirect(url_for('admin.movie_add'))

    return render_template('admin/movie_add.html', form=form)


# 2.电影列表
@admin.route('/movie/list/<int:page>/', methods=['GET'])
@admin_login_req
@admin_auth
def movie_list(page=None):
    if page == None:
        page = 1
    # 按标签添加的时间排序显示
    page_data = Movie.query.join(Tag).filter(  # .join(Tag):因为要通过标签id查询标签名称;filter():关联连个模型
        Tag.id == Movie.tag_id
    ).order_by(
        Movie.addtime.desc()
    ).paginate(page=page, per_page=10)  # (传入要显示的页码,每页显示的标签个数)
    return render_template('admin/movie_list.html', page_data=page_data)


# 3.删除电影
@admin.route('/movie/del/<int:id>/', methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def movie_del(id=None):
    movie = Movie.query.filter_by(id=id).first_or_404()  # 查询失败直接返回404
    db.session.delete(movie)
    db.session.commit()
    flash('删除电影成功!', 'ok')

    # 将删除电影操作保存到操作日志列表
    oplog = Oplog(
        admin_id=session['admin_id'],
        ip=request.remote_addr,
        reason='删除电影:《' + movie.title + '》'
    )
    db.session.add(oplog)
    db.session.commit()
    return redirect(url_for('admin.movie_list', page=1))


# 4.编辑电影
@admin.route('/movie/edit/<int:id>/', methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def movie_edit(id=None):
    form = MovieForm()
    form.url.validators = []
    form.logo.validators = []
    movie = Movie.query.get_or_404(id)
    if request.method == 'GET':
        # 这三个用value传不进去,所以用这种方法
        form.info.data = movie.info
        form.tag_id.data = movie.tag_id
        form.star.data = movie.star

    # 修改电影信息
    if form.validate_on_submit():
        data = form.data
        # 如果片名以存在,则修改失败
        movie_count = Movie.query.filter_by(title=data['title']).count()
        if movie_count == 1 and movie.title != data['title']:
            flash('片名以存在,请重新输入!', 'err')
            return redirect(url_for('admin.movie_edit', id=id))

        # 修改电影的视频及封面
        if not os.path.exists(app.config['UP_DIR']):  # 没有就创建文件夹
            os.makedirs(app.config['UP_DIR'])
            # os.chmod(app.config['UP_DIR'], 'rw')  # 给文件夹可读可写的权限,这样才能保存文件呀
            os.chmod(app.config['UP_DIR'], stat.S_IRWXU)  # 给文件夹可读可写的权限,这样才能保存文件呀 'rw'
        # 如果URL不为空,即为修改了视频地址,要重新保存
        if form.url.data != '':
            file_url = secure_filename(form.url.data.filename)  # 生成上传的电影视频的文件名,并安全加密
            movie.url = change_filename(file_url)
            form.url.data.save(app.config['UP_DIR'] + movie.url)
        # 如果logo不为空,即为修改了视频封面地址,要重新保存
        if form.logo.data != '':
            file_logo = secure_filename(form.logo.data.filename)  # 生成上传的电影封面的文件名,并安全加密
            movie.logo = change_filename(file_logo)
            form.logo.data.save(app.config['UP_DIR'] + movie.logo)

        movie.info = data['info']
        movie.star = data['star']
        movie.tag_id = data['tag_id']
        movie.title = data['title']
        movie.area = data['area']
        movie.length = data['length']
        movie.release_time = data['release_time']
        db.session.add(movie)
        db.session.commit()

        flash('修改电影成功!', 'ok')  # 'ok':表示成功信息
        return redirect(url_for('admin.movie_edit', id=movie.id))
    return render_template('admin/movie_edit.html', form=form, movie=movie)  # 传movie是为了赋予初值,因为是修改电影,标签上面会显示之前的电影信息


# 上映预告管理
# 1.添加预告
@admin.route('/preview/add/', methods=['GET', 'POST'])
@admin_login_req
#@admin_auth
def preview_add():
    form = PreviewForm()
    if form.validate_on_submit():
        data = form.data
        preview_count = Preview.query.filter_by(title=data['title']).count()
        if preview_count == 1:
            flash('该预告已存在!', 'err')
            return redirect(url_for('admin.preview_add'))
        # 保存上传的预告封面
        file_logo = secure_filename(form.logo.data.filename)
        if not os.path.exists(app.config['UP_DIR']):
            os.makedirs(app.config['UP_DIR'])
            os.chmod(app.config['UP_DIR'], stat.S_IRWXU)
        logo = change_filename(file_logo)
        form.logo.data.save(app.config['UP_DIR'] + logo)
        # 添加预告信息入库
        preview = Preview(
            title=data['title'],
            logo=logo
        )
        db.session.add(preview)
        db.session.commit()
        flash('添加新预告成功!', 'ok')

        # 将添加预告操作保存到操作日志列表
        oplog = Oplog(
            admin_id=session['admin_id'],
            ip=request.remote_addr,
            reason='添加预告:' + preview.title
        )
        db.session.add(oplog)
        db.session.commit()
        return redirect(url_for('admin.preview_add'))

    return render_template('admin/preview_add.html', form=form)


# 2.预告列表
@admin.route('/preview/list/<int:page>/', methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def preview_list(page=None):
    if page == None:
        page = 1
    page_data = Preview.query.order_by(
        Preview.addtime.desc()
    ).paginate(page=page, per_page=10)

    return render_template('admin/preview_list.html', page_data=page_data)


# 3.删除预告
@admin.route('/preview/del/<int:id>/', methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def preview_del(id=None):
    preview = Preview.query.filter_by(id=id).first_or_404()
    db.session.delete(preview)
    db.session.commit()
    flash('删除预告成功', 'ok')

    # 将删除预告操作保存到操作日志列表
    oplog = Oplog(
        admin_id=session['admin_id'],
        ip=request.remote_addr,
        reason='删除预告:' + preview.title
    )
    db.session.add(oplog)
    db.session.commit()
    return redirect(url_for('admin.preview_list', page=1))


# 4.编辑预告
@admin.route('/preview/edit/<int:id>/', methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def preview_edit(id=None):
    form = PreviewForm()
    form.logo.validators = []
    preview = Preview.query.get_or_404(id)
    if request.method == 'GET':
        form.title.data = preview.title
        form.logo.data = preview.logo
    if form.validate_on_submit():
        data = form.data
        preview_count = Preview.query.filter_by(title=data['title']).count()
        if preview_count == 1 and preview.title != data['title']:
            flash('预告标题已存在,请重新输入!', 'err')
            return redirect(url_for('admin.preview_edit', id=id))

        if not os.path.exists(app.config['UP_DIR']):  # 没有就创建文件夹
            os.makedirs(app.config['UP_DIR'])
            # os.chmod(app.config['UP_DIR'], 'rw')  # 给文件夹可读可写的权限,这样才能保存文件呀
            os.chmod(app.config['UP_DIR'], stat.S_IRWXU)

        # 如果logo不为空,即为修改了预告封面地址,要重新保存
        if form.logo.data != '':
            file_logo = secure_filename(form.logo.data.filename)  # 生成上传的电影封面的文件名,并安全加密
            preview.logo = change_filename(file_logo)
            form.logo.data.save(app.config['UP_DIR'] + preview.logo)

        preview.title = data['title']
        db.session.add(preview)
        db.session.commit()
        flash('修改预告成功!', 'ok')
        return redirect(url_for('admin.preview_edit', id=preview.id))

    return render_template('admin/preview_edit.html', form=form, preview=preview)


# 会员管理
# 1.会员列表
@admin.route('/user/list/<int:page>/', methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def user_list(page=None):
    if page == None:
        page = 1
    page_data = User.query.order_by(
        User.addtime.desc()
    ).paginate(page=page, per_page=10)

    return render_template('admin/user_list.html', page_data=page_data)


# 2.查看会员详情
@admin.route('/user/view/<int:id>/', methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def user_view(id=None):
    user = User.query.get_or_404(id)
    return render_template('admin/user_view.html', user=user)


# 3.删除会员
# 命令行插入会员操作:insert into user(name,pwd,email,phone,info,face,uuid,addtime) values('李茄豪','123','123@qq.com','1388888888','python','1.png','d32Zqwedfsafgfgs',now());
# 清空表后使之ID从1开始递增:ALTER TABLE comment auto_increment=1;
@admin.route('/user/del/<int:id>/', methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def user_del(id=None):
    user = User.query.filter_by(id=id).first_or_404()
    db.session.delete(user)
    db.session.commit()
    flash('删除会员成功!', 'ok')

    # 将删除会员操作保存到操作日志列表
    oplog = Oplog(
        admin_id=session['admin_id'],
        ip=request.remote_addr,
        reason='删除会员:' + user.name
    )
    db.session.add(oplog)
    db.session.commit()
    return redirect(url_for('admin.user_list', page=1))


# 评论管理列表
# 命令行插入评论操作:insert into comment(movie_id,user_id,content,addtime) values(1,2,'哈哈,真好看!',now());
@admin.route('/comment/list/<int:page>/', methods=['GET'])
@admin_login_req
@admin_auth
def comment_list(page=None):
    if page == None:
        page = 1
    page_data = Comment.query.join(  # join:关联其他表
        Movie
    ).join(
        User
    ).filter(  # filter:过滤查询条件(可以填几个); 而filter_by:只能填一个条件
        Movie.id == Comment.movie_id,
        User.id == Comment.user_id
    ).order_by(  # order_by:排序
        Comment.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template('admin/comment_list.html', page_data=page_data)


# 删除评论
@admin.route('/comment/del/<int:id>/', methods=['GET'])
@admin_login_req
@admin_auth
def comment_del(id=None):
    comment = Comment.query.filter_by(id=id).first_or_404()
    db.session.delete(comment)
    db.session.commit()
    flash('删除评论成功!', 'ok')

    # 将删除评论操作保存到操作日志列表
    oplog = Oplog(
        admin_id=session['admin_id'],
        ip=request.remote_addr,
        reason='删除评论:' + comment.content
    )
    db.session.add(oplog)
    db.session.commit()
    return redirect(url_for('admin.comment_list', page=1))


# 收藏管理列表
# 命令行插入收藏操作:insert into moviecol(movie_id,user_id,addtime) values(1,2,now());
@admin.route('/moviecol/list/<int:page>/', methods=['GET'])
@admin_login_req
@admin_auth
def moviecol_list(page=None):
    if page == None:
        page = 1
    page_data = Moviecol.query.join(
        Movie
    ).join(
        User
    ).filter(
        Movie.id == Moviecol.movie_id,
        User.id == Moviecol.user_id
    ).order_by(
        Moviecol.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template('admin/moviecol_list.html', page_data=page_data)


# 删除收藏
@admin.route('/moviecol/del/<int:id>/', methods=['GET'])
@admin_login_req
@admin_auth
def moviecol_del(id=None):
    moviecol = Moviecol.query.filter_by(id=id).first_or_404()
    db.session.delete(moviecol)
    db.session.commit()
    flash('删除收藏成功!', 'ok')
    return redirect(url_for('admin.moviecol_list', page=1))


# 日志管理
# 命令行插日志操作:insert into oplog(admin_id,ip,reason,addtime) values(1,'192.108.0.1','添加一个电影:python',now());
# 1.管理员操作日志列表
@admin.route('/oplog/list/<int:page>/', methods=['GET'])
@admin_login_req
@admin_auth
def oplog_list(page=None):
    if page == None:
        page = 1
    page_data = Oplog.query.join(
        Admin
    ).filter(
        Admin.id == Oplog.admin_id
    ).order_by(
        Oplog.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template('admin/oplog_list.html', page_data=page_data)


# 2.管理员登录日志列表
# 命令行插管理员登录日志操作:insert into adminlog(admin_id,ip,addtime) values(1,'192.108.0.1',now());
@admin.route('/adminloginlog/list/<int:page>/', methods=['GET'])
@admin_login_req
@admin_auth
def adminloginlog_list(page=None):
    if page == None:
        page = 1
    page_data = Adminlog.query.join(
        Admin
    ).filter(
        Admin.id == Adminlog.admin_id
    ).order_by(
        Adminlog.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template('admin/adminloginlog_list.html', page_data=page_data)


# 3.会员登录日志列表
# 命令行插会员登录日志操作:insert into userlog(user_id,ip,addtime) values(2,'192.108.0.1',now());
@admin.route('/userloginlog/list/<int:page>/', methods=['GET'])
@admin_login_req
@admin_auth
def userloginlog_list(page=None):
    if page == None:
        page = 1
    page_data = Userlog.query.join(
        User
    ).filter(
        User.id == Userlog.user_id
    ).order_by(
        Userlog.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template('admin/userloginlog_list.html', page_data=page_data)


# 权限管理
# 权限:就是管理员可以操作的路由地址,例如添加电影:/movie/add/
# 1.添加权限
@admin.route('/auth/add/', methods=['GET', 'POST'])
@admin_login_req
# @admin_auth
def auth_add():
    form = AuthForm()
    if form.validate_on_submit():
        data = form.data
        auth_count = Auth.query.filter_by(name=data['name']).count()
        if auth_count == 1:
            flash('该权限名已存在!请重新添加!', 'err')
            return redirect(url_for('admin.auth_add'))
        auth = Auth(
            name=data['name'],
            url=data['url']
        )
        db.session.add(auth)
        db.session.commit()
        flash('添加新权限成功!', 'ok')
        return redirect(url_for('admin.auth_add'))
    return render_template('admin/auth_add.html', form=form)


# 2.权限列表
@admin.route('/auth/list/<int:page>/', methods=['GET'])
@admin_login_req
# @admin_auth
def auth_list(page=None):
    if page == None:
        page = 1
    page_data = Auth.query.order_by(
        Auth.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template('admin/auth_list.html', page_data=page_data)


# 3.删除权限
@admin.route('/auth/del/<int:id>', methods=['GET'])
@admin_login_req
@admin_auth
def auth_del(id=None):
    auth = Auth.query.filter_by(id=id).first_or_404()
    db.session.delete(auth)
    db.session.commit()
    flash('删除权限成功!', 'ok')
    return redirect(url_for('admin.auth_list', page=1))


# 4. 编辑权限
@admin.route('/auth/edit/<int:id>/', methods=['GET', 'POST'])
@admin_login_req
# @admin_auth
def auth_edit(id=None):
    form = AuthForm()
    auth = Auth.query.get_or_404(id)
    if request.method == 'GET':
        form.name.data = auth.name
        form.url.data = auth.url
    if form.validate_on_submit():
        data = form.data
        auth_count = Auth.query.filter_by(name=data['name']).count()
        if auth_count == 1 and auth.name != data['name']:
            flash('权限名称已存在,请重新输入!', 'err')
            return redirect(url_for('admin.auth_edit', id=id))
        auth.name = data['name']
        auth.url = data['url']
        db.session.add(auth)
        db.session.commit()
        flash('修改权限成功!', 'ok')
        return redirect(url_for('admin.auth_edit', id=auth.id))

    return render_template('admin/auth_edit.html', form=form)


# 角色管理
# 角色:就是管理员的不同分类,有专门管理电影模块的,也有专门管理会员的...(管理员所属什么角色,角色又包括几个权限)
# 1.添加角色
@admin.route('/role/add/', methods=['GET', 'POST'])
@admin_login_req
# @admin_auth
def role_add():
    form = RoleForm()
    if form.validate_on_submit():
        data = form.data
        role_count = Role.query.filter_by(name=data['name']).count()
        if role_count == 1:
            flash('该角色名已存在!请重新添加!', 'err')
            return redirect(url_for('admin.role_add'))
        role = Role(
            name=data['name'],
            auths=','.join(map(lambda v: str(v), data['auths']))
            # 将[1,2,3]转化成'1,2,3';因为auths是一个权限ID列表[1,2,3],所以要拼接成一个字符串;而ID又是整形,所以要转化成str
        )
        db.session.add(role)
        db.session.commit()
        flash('添加新角色成功!', 'ok')
        return redirect(url_for('admin.role_add'))
    return render_template('admin/role_add.html', form=form)


# 2.角色列表
@admin.route('/role/list/<int:page>/', methods=['GET'])
@admin_login_req
# @admin_auth
def role_list(page=None):
    if page == None:
        page = 1
    page_data = Role.query.order_by(
        Role.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template('admin/role_list.html', page_data=page_data)


# 3.删除角色
@admin.route('/role/del/<int:id>', methods=['GET'])
@admin_login_req
@admin_auth
def role_del(id=None):
    role = Role.query.filter_by(id=id).first_or_404()
    db.session.delete(role)
    db.session.commit()
    flash('删除角色成功!', 'ok')
    return redirect(url_for('admin.role_list', page=1))


# 4.编辑角色
@admin.route('/role/edit/<int:id>/', methods=['GET', 'POST'])
@admin_login_req
# @admin_auth
def role_edit(id=None):
    form = RoleForm()
    role = Role.query.get_or_404(id)
    if request.method == 'GET':
        if role.auths == '':  # 有的管理员没有权限就是空的,就不返回他的权限列表了
            form.name.data = role.name
        else:
            form.name.data = role.name
            form.auths.data = list(map(lambda v: int(v), role.auths.split(',')))  # 将字符串'1,2,3'转化成[1,2,3]
    if form.validate_on_submit():
        data = form.data
        role_count = Role.query.filter_by(name=data['name']).count()
        if role_count == 1 and role.name != data['name']:
            flash('角色名称已存在,请重新输入!', 'err')
            return redirect(url_for('admin.role_edit', id=id))
        role.name = data['name']
        role.auths = ','.join(map(lambda v: str(v), data['auths']))
        db.session.add(role)
        db.session.commit()
        flash('修改角色成功!', 'ok')
        return redirect(url_for('admin.role_edit', id=role.id))

    return render_template('admin/role_edit.html', form=form)


# 管理员管理
# 1.添加管理员
@admin.route('/admin/add/', methods=['GET', 'POST'])
@admin_login_req
@admin_auth
def admin_add():
    form = AdminForm()
    from werkzeug.security import generate_password_hash
    if form.validate_on_submit():
        data = form.data
        admin_count = Admin.query.filter_by(name=data['name']).count()
        if admin_count == 1:
            flash('该管理员名已存在!请重新添加!', 'err')
            return redirect(url_for('admin.admin_add'))
        admin = Admin(
            name=data['name'],
            pwd=generate_password_hash(data['pwd']),
            role_id=data['role_id'],
            is_super=1  # 普通管理员(0:超级管理员)
        )
        db.session.add(admin)
        db.session.commit()
        flash('添加新管理员成功!', 'ok')
        return redirect(url_for('admin.admin_add'))
    return render_template('admin/admin_add.html', form=form)


# 2.管理员列表
@admin.route('/admin/list/<int:page>/', methods=['GET'])
@admin_login_req
@admin_auth
def admin_list(page=None):
    if page == None:
        page = 1
    page_data = Admin.query.join(
        Role
    ).filter(
        Role.id == Admin.role_id
    ).order_by(
        Admin.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template('admin/admin_list.html', page_data=page_data)
