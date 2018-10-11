# !/user/bin/env python
# -*- coding:utf-8 -*- 
# time: 2018/3/7--19:52
__author__ = 'Henry'


from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FileField, SelectField,SelectMultipleField
from wtforms.validators import DataRequired, ValidationError,EqualTo,Email,Regexp
from app.models import Admin, Tag,Auth,Role,User
from flask import session


class RegistForm(FlaskForm):
    '''会员注册表单'''
    name = StringField(
        label='昵称',
        validators=[
            DataRequired('请输入昵称!')
        ],
        description='昵称',
        render_kw={
            'class' :'form-control input-lg',
            'placeholder':'昵称',
            # 'required':'required'
        }
    )
    email = StringField(
        label='邮箱',
        validators=[
            DataRequired('请输入邮箱!'),
            Email('邮箱格式不正确!')   #Email模块验证邮箱格式
        ],
        description='邮箱',
        render_kw={
            'class': 'form-control input-lg',
            'placeholder': '邮箱',
            # 'required': 'required'
        }
    )
    phone = StringField(
        label='手机',
        validators=[
            DataRequired('请输入手机号!'),
            Regexp('1[3458]\\d{9}',message='手机格式不正确!')   #Regexp正则模块验证手机格式(第一位:1;第二位:3或4或5或8;加上后面9位数)
        ],
        description='手机',
        render_kw={
            'class': 'form-control input-lg',
            'placeholder': '手机',
            # 'required': 'required'
        }
    )
    pwd = PasswordField(
        label='密码',
        validators=[
            DataRequired('请输入密码!')
        ],
        description='密码',
        render_kw={
            'class': 'form-control input-lg',
            'placeholder': '密码',
            # 'required': 'required'
        }
    )
    repwd = PasswordField(
        label='确认密码',
        validators=[
            DataRequired('请输入确认密码!'),
            EqualTo('pwd','两次密码输入不一致!')
        ],
        description='确认密码',
        render_kw={
            'class': 'form-control input-lg',
            'placeholder': '确认密码',
            # 'required': 'required'
        }
    )
    submit = SubmitField(
        '注册',
        render_kw={
            'class': 'btn btn-lg btn-success btn-block'
        }
    )
    #通过下面的验证函数不好使,还是放在views中验证比较好!
    def validata_name(self,field):
        '''查询用户名是否存在'''
        name = field.data
        user = User.query.filter_by(name=name).count()
        if user == 1:
            raise ValidationError('此昵称已存在!')


    def validata_email(self,field):
        '''查询邮箱是否存在'''
        email = field.data
        user = User.query.filter_by(email=email).count()
        if user == 1:
            raise ValidationError('此邮箱已存在!')

    def validata_phone(self,field):
        '''查询手机是否存在'''
        phone = field.data
        user = User.query.filter_by(phone=phone).count()
        if user == 1:
            raise ValidationError('此手机号已存在!')


class LoginForm(FlaskForm):
    '''会员登录表单'''
    name = StringField(
        label='账号',
        validators=[
            DataRequired('请输入账号!')
        ],
        description='账号',
        render_kw={
            'class': 'form-control input-lg',
            'placeholder': '用户名',
            'required': 'required'
        }
    )
    pwd = PasswordField(
        label='密码',
        validators=[
            DataRequired('请输入密码!')
        ],
        description='密码',
        render_kw={
            'class': 'form-control input-lg',
            'placeholder': '密码',
            'required': 'required'
        }
    )
    submit = SubmitField(
        '登录',
        render_kw={
            'class': 'btn btn-lg btn-success btn-block'
        }
    )


class UserdetailForm(FlaskForm):
    '''会员修改资料表单'''
    name = StringField(
        label='昵称',
        validators=[
            DataRequired('请输入昵称!'),
        ],
        description='昵称',
        render_kw={
            'class': 'form-control'
        }
    )
    email = StringField(
        label='邮箱',
        validators=[
            DataRequired('请输入邮箱!'),
            Email('邮箱格式不正确!')  # Email模块验证邮箱格式
        ],
        description='邮箱',
        render_kw={
            'class': 'form-control'
        }
    )
    phone = StringField(
        label='手机',
        validators=[
            DataRequired('请输入手机号!'),
            Regexp('1[3458]\\d{9}', message='手机格式不正确!')  # Regexp正则模块验证手机格式(第一位:1;第二位:3或4或5或8;加上后面9位数)
        ],
        description='手机',
        render_kw={
            'class': 'form-control'
        }
    )
    face = FileField(
        label='头像',
        description='头像',
    )
    info = TextAreaField(
        label='简介',
        description='简介',
        render_kw={
            'class': 'form-control',
            'rows':10
        }
    )
    submit = SubmitField(
        '保存修改',
        render_kw={
            'class': 'btn btn-success'
        }
    )


class PwdForm(FlaskForm):
    '''修改用户密码表单'''
    old_pwd = PasswordField(
        label='旧密码',
        validators=[
            DataRequired('请输入旧密码!'),
        ],
        description='旧密码',
        render_kw={
            'class': 'form-control',
            'placeholder':'旧密码',
            'required':'required'
        }
    )
    new_pwd = PasswordField(
        label='新密码',
        validators=[
            DataRequired('请输入新密码!'),
        ],
        description='新密码',
        render_kw={
            'class': 'form-control',
            'placeholder': '新密码',
            'required': 'required'
        }
    )
    submit = SubmitField(
        '修改密码',
        render_kw={
            'class': 'btn btn-success'
        }
    )


class CommentForm(FlaskForm):
    '''提交电影评论表单'''
    content = TextAreaField(
        label='评论内容',
        description='内容',
        validators=[
            DataRequired('请输入评论内容!')
        ],
        render_kw={
            # 'id':'input_content',   #原版:带表情的评论框
            'id':'comment',
            'rows': 5
        }
    )
    submit = SubmitField(
        '提交评论',
        render_kw={
            'class': 'btn btn-success',
            'id': 'btn-sub',
        }
    )


