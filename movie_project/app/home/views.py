# !/user/bin/env python
# -*- coding:utf-8 -*- 
# time: 2018/3/7--19:52
__author__ = 'Henry'

from . import home
from flask import render_template, url_for, redirect, flash, session, request
from app.home.forms import RegistForm, LoginForm, UserdetailForm, PwdForm,CommentForm
from app.models import User, Userlog, Comment, Movie,Preview,Tag,Moviecol
from app import db, app
import uuid  # 添加唯一标志符
from werkzeug.security import generate_password_hash
from functools import wraps  # 装饰器(用于访问控制)
from werkzeug.utils import secure_filename
import os, stat, datetime

# 修改上传的文件名称
def change_filename(filename):
    # fileinfo = os.path.splitext(filename)  # 取出上传的文件名的后缀(.MP4)
    fileinfo = filename.split('.')  # 取出上传的文件名的后缀(.MP4)
    filename = datetime.datetime.now().strftime('%Y%m%d%H%M%S') + str(uuid.uuid4().hex) + '.' + fileinfo[-1]
    return filename


# 前台登录装饰器(只能登录后才能访问会员中心)
def user_login_req(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:  # if session['user'] is None:
            return redirect(url_for('home.login', next=request.url))
        return f(*args, **kwargs)

    return decorated_function


# 首页重定向
@home.route('/',methods=['GET'])
def index_1():
    return redirect('/1/')

# 首页
@home.route('/<int:page>/',methods=['GET'])
def index(page=None):
    #电影筛选 (默认按视频上传时间排,最新上传的在最前面)
    tags = Tag.query.all()
    page_data = Movie.query.order_by(
        Movie.addtime.desc()
    )
    # 1.电影标签(国产,动漫,科技...)
    tid = request.args.get('tid',0)
    if int(tid) != 0:
        page_data = page_data.filter_by(tag_id=int(tid))

    # 2.电影星级(一星到五星)
    star = request.args.get('star',0)
    if int(star) != 0:
        page_data = page_data.filter_by(star=int(star))

    # 3.添加时间(最近,最早)
    time = request.args.get('time',0)
    if int(time) != 0:
        if int(time) == 1: #降序(最近)
            page_data = Movie.query.order_by(
                Movie.addtime.desc()
            )
        else: #升序(最早) if int(time) == 2
            page_data = Movie.query.order_by(
                Movie.addtime.asc()
            )

    # 4.播放数量(从高到低,从低到高)
    pm = request.args.get('pm',0)
    if int(pm) != 0:
        if int(pm) == 1:
            page_data = Movie.query.order_by(
                Movie.playnum.desc()
            )
        else:
            page_data = Movie.query.order_by(
                Movie.playnum.asc()
            )

    # 5.评论数量(从高到低,从低到高)
    cm = request.args.get('cm',0)
    if int(cm) != 0:
        if int(cm) == 1:
            page_data = Movie.query.order_by(
                Movie.commentnum.desc()
            )
        else:
            page_data = Movie.query.order_by(
                Movie.commentnum.asc()
            )

    if page == None:
        page =1
    page_data = page_data.paginate(page=page,per_page=10)
    #将上面接受到的参数组成一个字典p
    p = dict(
        tid=tid,
        star=star,
        time=time,
        pm=pm,
        cm=cm
    )
    return render_template('home/index.html',tags=tags,p=p,page_data=page_data)


# 登录
@home.route('/login/', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        data = form.data
        user = User.query.filter_by(name=data['name']).first()
        if not user:
            flash('没有此用户名!','err')
            return redirect(url_for('home.login'))
        if user.check_pwd(data['pwd']) ==False:  # 验证密码是否正确
            flash('密码错误!', 'err')
            return redirect(url_for('home.login'))
        # 登录成功则保存会话:
        session['user'] = user.name  # 用户名
        session['user_id'] = user.id  # 用户ID
        # 将登录操作存入会员登陆日志
        userlog = Userlog(
            user_id=session['user_id'],
            ip=request.remote_addr
        )
        db.session.add(userlog)
        db.session.commit()
        return redirect(url_for('home.user'))  # 登录成功跳到会员中心
    return render_template('home/login.html', form=form)


# 登出
@home.route('/logout/')
def logout():
    # 删除会话
    session.pop('user', None)
    session.pop('user_id', None)
    return redirect(url_for('home.login'))


# 注册
@home.route('/regist/', methods=['GET', 'POST'])
def regist():
    form = RegistForm()
    if form.validate_on_submit():
        data = form.data
        #查询用户名是否存在
        name = data['name']
        user = User.query.filter_by(name=name).count()
        if user == 1:
            flash('此昵称已存在!','err')
            return render_template('home/regist.html', form=form)

        email = data['email']
        user = User.query.filter_by(email=email).count()
        if user == 1:
            flash('此邮箱已存在!','err')
            return render_template('home/regist.html', form=form)

        phone = data['phone']
        user = User.query.filter_by(phone=phone).count()
        if user == 1:
            flash('此手机号已存在!','err')
            return render_template('home/regist.html', form=form)

        user = User(
            name=data['name'],
            email=data['email'],
            phone=data['phone'],
            pwd=generate_password_hash(data['pwd']),  # 加密用户的密码
            uuid=uuid.uuid4().hex  # 生成用户的唯一标志符
        )
        db.session.add(user)
        db.session.commit()
        flash('恭喜您,注册成功!', 'ok')
        return redirect(url_for('home.login'))
    return render_template('home/regist.html', form=form)


# 会员中心(可修改会员资料)
@home.route('/user/', methods=['GET', 'POST'])
@user_login_req  # 只有登录后才能访问会员中心
def user():
    form = UserdetailForm()
    user = User.query.get_or_404(session['user_id'])
    form.face.validators = []
    # 获取用户现在的会员信息(get)
    if request.method == 'GET':
        form.name.data = user.name
        form.email.data = user.email
        form.phone.data = user.phone
        form.info.data = user.info
    # 修改会员信息(post)
    if form.validate_on_submit():
        data = form.data
        # 如果用户名以存在,则修改失败
        user_name = User.query.filter_by(name=data['name']).count()
        if user_name == 1 and user.name != data['name']:
            flash('用户昵称已存在,请重新输入!', 'err')
            return redirect(url_for('home.user'))
        # 如果邮箱以存在,则修改失败
        user_email = User.query.filter_by(email=data['email']).count()
        if user_email == 1 and user.email != data['email']:
            flash('邮箱已存在,请重新输入!', 'err')
            return redirect(url_for('home.user'))
        # 如果手机号以存在,则修改失败
        user_phone = User.query.filter_by(phone=data['phone']).count()
        if user_phone == 1 and user.phone != data['phone']:
            flash('手机号已存在,请重新输入!', 'err')
            return redirect(url_for('home.user'))

        # 修改头像
        if not os.path.exists(app.config['FC_DIR']):  # 没有就创建文件夹
            os.makedirs(app.config['FC_DIR'])
            # os.chmod(app.config['FC_DIR'], 'rw')  # 给文件夹可读可写的权限,这样才能保存文件呀
            os.chmod(app.config['FC_DIR'], stat.S_IRWXU)  # 给文件夹可读可写的权限,这样才能保存文件呀 'rw'
        # 如果face不为空,即为修改了头像地址,要重新保存
        # 上传头像文件,一定要加上enctype="multipart/form-data"
        if form.face.data != '':
            file_face = secure_filename(form.face.data.filename)  # 生成上传的电影封面的文件名,并安全加密
            user.face = change_filename(file_face)
            form.face.data.save(app.config['FC_DIR'] + user.face)
        # 修改入库
        user.name = data['name'],
        user.email = data['email'],
        user.phone = data['phone'],
        user.info = data['info'],
        db.session.add(user)
        db.session.commit()
        flash('修改资料成功!', 'ok')
        return redirect(url_for('home.user'))
    return render_template('home/user.html', form=form, user=user)


# 1.修改密码
@home.route('/pwd/', methods=['GET', 'POST'])
@user_login_req
def pwd():
    form = PwdForm()
    user = User.query.filter_by(id=session['user_id']).first()
    if form.validate_on_submit():
        data = form.data
        if not user.check_pwd(data['old_pwd']):
            flash('旧密码错误!请重新输入!', 'err')
            return redirect(url_for('home.pwd'))
        user.pwd = generate_password_hash(data['new_pwd'])
        db.session.add(user)
        db.session.commit()
        flash('修改密码成功!', 'ok')
        return redirect(url_for('home.logout'))
    return render_template('home/pwd.html', form=form)


# 2.评论记录
@home.route('/comments/<int:page>/', methods=['GET'])
@user_login_req
def comments(page=None):
    if page == None:
        page = 1
    page_data = Comment.query.join(
        User
    ).join(
        Movie
    ).filter(
        Comment.user_id == session['user_id'],
        User.id == Comment.user_id,
        Movie.id == Comment.movie_id
    ).order_by(
        Comment.addtime.desc()
    ).paginate(page=page, per_page=6)
    return render_template('home/comments.html', page_data=page_data)


# 3.登录日志
@home.route('/loginlog/<int:page>/', methods=['GET'])
@user_login_req
def loginlog(page=None):
    if page == None:
        page = 1
    page_data = Userlog.query.filter_by(
        user_id=session['user_id']
    ).order_by(
        Userlog.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template('home/loginlog.html', page_data=page_data)


# 4.电影收藏
@home.route('/moviecol/<int:page>/',methods=['GET'])
@user_login_req
def moviecol(page=None):
    if page == None:
        page = 1
    page_data = Moviecol.query.join(
        Movie
    ).filter(
        Moviecol.user_id == session['user_id']
    ).order_by(
        Moviecol.addtime.desc()
    ).paginate(page=page,per_page=10)
    return render_template('home/moviecol.html',page_data=page_data)


#添加电影收藏(AJAX异步方法)
@home.route('/moviecol/add/',methods=['GET'])
@user_login_req
def moviecol_add():
    #接受uid用户ID和mid电影ID
    uid = request.args.get("uid","")
    mid = request.args.get("mid","")
    moviecol = Moviecol.query.filter_by(
        # user_id = int(uid),
        # movie_id = int(mid)
        movie_id = mid,
        user_id = uid
    ).count()
    if moviecol == 1:  #如果该用户已经收藏了该电影
        data = dict(ok=0)
    # if moviecol == 0:  #没有收藏就要收藏
    else:
        moviecol = Moviecol(
            movie_id=mid,
            user_id=uid
        )
        db.session.add(moviecol)
        db.session.commit()
        data = dict(ok=1)
    import json
    return json.dumps(data) #浏览器返回一个json:{"ok": 1}
    # return json.dumps(dict(ok=1))


# 电影上映预告轮播图
@home.route('/animation/')
def animation():
    data = Preview.query.all()

    return render_template('home/animation.html',data=data)


# 搜索页面
@home.route('/search/<int:page>/')
def search(page=None):
    if page ==None:
        page = 1
    key = request.args.get('key','') #接受填入的key值,没有就是空
    #电影信息
    page_data = Movie.query.filter(
        Movie.title.ilike('%' + key + '%')     #模糊匹配
    ).order_by(
        Movie.addtime.desc()
    ).paginate(page=page,per_page=10)
    #搜索个数
    movie_count = Movie.query.filter(
        Movie.title.ilike('%' + key + '%')  # 模糊匹配
    ).count()
    page_data.key = key #把搜索的关键字key传入翻译的模板ui/search.html

    return render_template('home/search.html',key=key,page_data=page_data,movie_count=movie_count)


# 电影详情页
@home.route('/play/<int:id>/<int:page>/',methods=['GET','POST'])
def play(id=None,page=None):
    form = CommentForm()
    movie = Movie.query.get_or_404(id)
    movie.playnum = movie.playnum + 1 #点开一次,播放数+1
    tag = Tag.query.filter_by(id=movie.tag_id).first()
    #获取评论列表
    if page == None:
        page = 1
    page_data = Comment.query.join(
        User
    ).filter(
        User.id == Comment.user_id,
        Comment.movie_id ==id
    ).order_by(
        Comment.addtime.desc()
    ).paginate(page=page,per_page=6)
    #提交评论
    if 'user' in session and form.validate_on_submit():
        data = form.data
        comment = Comment(
            content=data['content'],
            movie_id=id,
            user_id=session['user_id']
        )
        db.session.add(comment)
        db.session.commit()
        flash('评论成功!','ok')
        #评论成功,则该电影评论数+1
        movie.commentnum = movie.commentnum + 1
        db.session.add(movie)
        db.session.commit()
        return redirect(url_for('home.play',id=id,page=1))
    #修改movie
    db.session.add(movie)
    db.session.commit()

    return render_template('home/play.html',movie=movie,tag=tag,form=form,page_data=page_data)

# 404页面 (去蓝图__init__.py中定义,而不是在这个视图中)
