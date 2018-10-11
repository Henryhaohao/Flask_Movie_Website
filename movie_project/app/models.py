# !/user/bin/env python
# -*- coding:utf-8 -*- 
# time: 2018/3/7--19:50
__author__ = 'Henry'

from app import db
from datetime import datetime


# 会员模型
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)  # 编号
    name = db.Column(db.String(100), unique=True)  # 用户名
    pwd = db.Column(db.String(100))  # 密码
    email = db.Column(db.String(100), unique=True)  # 邮箱
    phone = db.Column(db.String(11), unique=True)  # 手机号
    info = db.Column(db.Text)  # 个性简介
    face = db.Column(db.String(255), unique=True)  # 头像
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)  # 注册时间
    uuid = db.Column(db.String(255), unique=True)  # 唯一标识符

    userlogs = db.relationship('Userlog', backref='user')  # 会员日志外键关系关联
    comments = db.relationship('Comment', backref='user')  # 电影评论外键关系关联
    moviecols = db.relationship('Moviecol', backref='user')  # 电影收藏外键关系关联

    def __repr__(self):
        return '<User %r>' % self.name

    def check_pwd(self,pwd):
        '''加密并验证用户的密码是否正确'''
        from werkzeug.security import check_password_hash
        return check_password_hash(self.pwd,pwd)


# 会员登录日志
class Userlog(db.Model):
    __tablename__ = 'userlog'
    id = db.Column(db.Integer, primary_key=True)  # 编号
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 用户ID
    ip = db.Column(db.String(100))  # 用户IP地址
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)  # 登录时间

    def __repr__(self):
        return '<Userlog %r>' % self.id


# 标签
class Tag(db.Model):
    __tablename__ = 'tag'
    id = db.Column(db.Integer, primary_key=True)  # 编号
    name = db.Column(db.String(100), unique=True)  # 标签名
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)  # 标签的添加时间

    movies = db.relationship('Movie', backref='tag')  # 电影外键关系关联

    def __repr__(self):
        return '<Tag %r>' % self.name


# 电影
class Movie(db.Model):
    __tablename__ = 'movie'
    id = db.Column(db.Integer, primary_key=True)  # 编号
    title = db.Column(db.String(255), unique=True)  # 电影名
    url = db.Column(db.String(255), unique=True)  # 电影地址
    info = db.Column(db.Text)  # 电影简介
    logo = db.Column(db.String(255), unique=True)  # 电影封面
    star = db.Column(db.SmallInteger)  # 星级
    playnum = db.Column(db.BigInteger)  # 播放数
    commentnum = db.Column(db.BigInteger)  # 评论数
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'))  # 标签ID
    area = db.Column(db.String(255))  # 上映地区
    release_time = db.Column(db.Date)  # 上映时间
    length = db.Column(db.String(100))  # 电影长度
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)  # 添加时间

    comments = db.relationship('Comment', backref='movie')  # 电影评论外键关系关联
    moviecols = db.relationship('Moviecol', backref='movie')  # 电影收藏外键关系关联

    def __repr__(self):
        return '<Movie %r>' % self.title


# 电影上映预告
class Preview(db.Model):
    __tablename__ = 'preview'
    id = db.Column(db.Integer, primary_key=True)  # 编号
    title = db.Column(db.String(255), unique=True)  # 预告片名
    logo = db.Column(db.String(255), unique=True)  # 封面
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)  # 添加时间

    def __repr__(self):
        return '<Preview %r>' % self.title


# 电影评论
class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)  # 编号
    content = db.Column(db.Text)  # 评论内容
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'))  # 所属电影
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 所属用户
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)  # 评论时间

    def __repr__(self):
        return '<Comment %r>' % self.id


# 收藏电影
class Moviecol(db.Model):
    __tablename__ = 'moviecol'
    id = db.Column(db.Integer, primary_key=True)  # 编号
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'))  # 所属电影
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # 所属用户
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)  # 添加时间

    def __repr__(self):
        return '<Moviecol %r>' % self.id


# 定义角色的权限
class Auth(db.Model):
    __tablename__ = 'auth'
    id = db.Column(db.Integer, primary_key=True)  # 编号
    name = db.Column(db.String(100), unique=True)  # 权限名
    url = db.Column(db.String(255), unique=True)  # 权限url地址
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)  # 创建时间

    def __repr__(self):
        return '<Auth %r>' % self.name


# 角色创建
class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column(db.Integer, primary_key=True)  # 编号
    name = db.Column(db.String(100), unique=True)  # 角色名
    auths = db.Column(db.String(600))  # 角色的权限列表
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)  # 创建时间

    admins = db.relationship('Admin', backref='role')  # 管理员创建外键关系关联

    def __repr__(self):
        return '<Role %r>' % self.name


# 管理员创建
class Admin(db.Model):
    __table__name = 'admin'
    id = db.Column(db.Integer, primary_key=True)  # 编号
    name = db.Column(db.String(100), unique=True)  # 管理员账号
    pwd = db.Column(db.String(100))  # 管理员密码
    is_super = db.Column(db.SmallInteger)  # 是否为超级管理员,0为超级管理员
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))  # 所属角色
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)  # 创建时间

    adminlogs = db.relationship('Adminlog', backref='admin')  # 管理员登陆日志外键关联
    oplogs = db.relationship('Oplog', backref='admin')  # 管理员操作日志外键关联

    def __repr__(self):
        return '<Admin %r>' % self.name

    def check_pwd(self, pwd):
        '''检验密码是否正确'''
        from werkzeug.security import check_password_hash
        return check_password_hash(self.pwd, pwd)


# 管理员登录日志
class Adminlog(db.Model):
    __tablename__ = 'adminlog'
    id = db.Column(db.Integer, primary_key=True)  # 编号
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'))  # 所属管理员编号
    ip = db.Column(db.String(100))  # 登录IP
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)  # 登录时间

    def __repr__(self):
        return '<Adminlog %r>' % self.id


# 管理员操作日志
class Oplog(db.Model):
    __tablename__ = 'oplog'
    id = db.Column(db.Integer, primary_key=True)  # 编号
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'))  # 所属管理员编号
    ip = db.Column(db.String(100))  # 操作IP
    reason = db.Column(db.String(600))  # 操作原因
    addtime = db.Column(db.DateTime, index=True, default=datetime.now)  # 操作时间

    def __repr__(self):
        return '<Oplog %r>' % self.id


'''
if __name__ == '__main__':
    #1.创建出所有数据模型(第一次运行后就不用了,可以注释掉)
    #db.create_all()

    
    #2.创建一个超级管理员角色:
    role = Role(
        name='超级管理员',
        auths=''
    )
    db.session.add(role)  # 添加
    db.session.commit()  # 提交
    

    #3.创建超级管理员的账号密码
    #导入Hash加密密码模块
    from werkzeug.security import generate_password_hash
    admin = Admin(
        name='Henry',
        pwd=generate_password_hash('Henry'),
        is_super=0, #是超级管理员
        role_id=1
    )
    db.session.add(admin)
    db.session.commit()
'''
