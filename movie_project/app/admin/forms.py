# !/user/bin/env python
# -*- coding:utf-8 -*- 
# time: 2018/3/7--19:52
__author__ = 'Henry'

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, FileField, SelectField,SelectMultipleField
from wtforms.validators import DataRequired, ValidationError,EqualTo
from app.models import Admin, Tag,Auth,Role
from flask import session

# 查询所有电影标签,用于添加电影标签
tags = Tag.query.all()
auth_list = Auth.query.all()
role_list = Role.query.all()

class LoginForm(FlaskForm):  # 继承FlaskForm这个类
    '''管理员登录表单'''
    account = StringField(
        label='账号',
        validators=[
            DataRequired('请输入账号!')
        ],
        description='账号',
        render_kw={
            'class': 'form-control',
            'placeholder': '请输入账号!',
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
            'class': 'form-control',
            'placeholder': '请输入密码!',
            'required': 'required'
        }
    )

    submit = SubmitField(
        '登录',
        render_kw={
            'class': 'btn btn-primary btn-block btn-flat'
        }
    )

    def validate_account(self, field):
        '''验证账号是否存在'''
        account = field.data
        admin = Admin.query.filter_by(name=account).count()
        if admin == 0:
            raise ValidationError('此账号不存在!')


class TagForm(FlaskForm):
    '''电影标签表单'''
    name = StringField(
        label='标签名称',
        validators=[
            DataRequired('请输入标签名称！')
        ],
        description='标签',
        render_kw={
            'class': 'form-control',
            'placeholder': '请输入标签名称！',
            'required': 'required'
        }
    )

    submit = SubmitField(
        '提交',
        render_kw={
            'class': 'btn btn-primary'
        }
    )


class MovieForm(FlaskForm):
    '''电影管理表单'''
    title = StringField(
        label='片名',
        validators=[
            DataRequired('请输入片名!')
        ],
        description='片名',
        render_kw={
            'class': 'form-control',
            'placeholder': '请输入片名！',
            'required': 'required'
        }
    )
    # FileField:文件上传框
    url = FileField(
        label='文件',
        validators=[
            DataRequired('请上传文件!')
        ],
        description='文件'
        # 上传文件不需要render_kw了
    )

    info = TextAreaField(
        label='介绍',
        validators=[
            DataRequired('请输入介绍!')
        ],
        description='介绍',
        render_kw={
            'class': 'form-control',
            'rows': '10'
        }
    )

    logo = FileField(
        label='封面',
        validators=[
            DataRequired('请上传封面!')
        ],
        description='封面',
    )
    # 下拉选择框
    star = SelectField(
        label='星级',
        validators=[
            DataRequired('请选择星级!')
        ],
        coerce=int,
        choices=[(1, '1星'), (2, '2星'), (3, '3星'), (4, '4星'), (5, '5星')],
        description='星级',
        render_kw={
            'class': 'form-control',
        }
    )

    tag_id = SelectField(
        label='标签',
        validators=[
            DataRequired('请选择标签!')
        ],
        coerce=int,
        # 查询遍历出所有的标签
        choices=[(v.id, v.name) for v in tags], #需要重启服务器后才会显示出新添加的标签,光刷新没用
        description='标签',
        render_kw={
            'class': 'form-control',
        }
    )

    area = StringField(
        label='地区',
        validators=[
            DataRequired('请输入地区!')
        ],
        description='地区',
        render_kw={
            'class': 'form-control',
            'placeholder': '请输入地区！',
            'required': 'required'
        }
    )

    length = StringField(
        label='片长',
        validators=[
            DataRequired('请输入片长!')
        ],
        description='片长',
        render_kw={
            'class': 'form-control',
            'placeholder': '请输入片长！(分钟)',
            'required': 'required'
        }
    )

    release_time = StringField(
        label='上映时间',
        validators=[
            DataRequired('请选择上映时间!')
        ],
        description='上映时间',
        render_kw={
            'class': 'form-control',
            'id': 'input_release_time',
            'placeholder': '请选择上映时间！',
            'required': 'required'
        }
    )

    submit = SubmitField(
        '提交',
        render_kw={
            'class': 'btn btn-primary',
        }
    )


class PreviewForm(FlaskForm):
    '''电影预告管理表单'''
    title = StringField(
        label='预告标题',
        validators=[
            DataRequired('请输入预告标题!')
        ],
        description='预告标题',
        render_kw={
            'class' :'form-control' ,
            'placeholder':'请输入预告标题！',
            'required':'required'
        }
    )

    logo = FileField(
        label='预告封面',
        validators=[
            DataRequired('请上传封面!')
        ],
        description='预告封面'
    )

    submit = SubmitField(
        '提交',
        render_kw={
            'class':'btn btn-primary'
        }
    )


class PwdForm(FlaskForm):
    '''修改管理员密码表单'''
    old_pwd = PasswordField(
        label='旧密码',
        validators=[
            DataRequired('请输入旧密码!')
        ],
        description='旧密码',
        render_kw={
            'class' :'form-control',
            'placeholder':'请输入旧密码!',
            'required':'required'
        }
    )

    new_pwd = PasswordField(
        label='新密码',
        validators=[
            DataRequired('请输入新密码!')
        ],
        description='新密码',
        render_kw={
            'class': 'form-control',
            'placeholder': '请输入新密码!',
            'required': 'required'
        }
    )

    submit = SubmitField(
        '修改',
        render_kw={
            'class' :'btn btn-primary'
        }
    )

    def validate_old_pwd(self,field):
        '''验证旧密码是否填写正确'''
        pwd = field.data
        name = session['admin']
        admin = Admin.query.filter_by(
            name=name
        ).first()
        admin.check_pwd(pwd)
        if not admin.check_pwd(pwd):
            raise ValidationError('旧密码错误!请重新输入!')


class AuthForm(FlaskForm):
    '''权限表单'''
    name = StringField(
        label='权限名称',
        validators=[
            DataRequired('请输入权限名称!')
        ],
        description='权限名称',
        render_kw={
            'class':'form-control',
            'placeholder' : '请输入权限名称！',
            'required': 'required'
        }
    )
    url = StringField(
        label='权限地址',
        validators=[
            DataRequired('请输入权限地址!')
        ],
        description='权限地址',
        render_kw={
            'class': 'form-control',
            'placeholder': '请输入权限地址！',
            'required': 'required'
        }
    )
    submit = SubmitField(
        '提交',
        render_kw={
            'class': 'btn btn-primary'
        }
    )


class RoleForm(FlaskForm):
    '''角色表单'''
    name = StringField(
        label='角色名称',
        validators=[
            DataRequired('请输入角色名称!')
        ],
        description='角色名称',
        render_kw={
            'class' :'form-control',
            'placeholder' : '请输入角色名称！',
            'required': 'required'
        }
    )
    auths = SelectMultipleField(   #多选框
        label='权限列表',
        validators=[
            DataRequired('请勾选操作权限!')
        ],
        coerce=int,
        choices=[(v.id,v.name) for v in auth_list],
        description='权限列表',
        render_kw={
            'class': 'form-control',
            'required': 'required'
        }
    )
    submit = SubmitField(
        '提交',
        render_kw={
            'class': 'btn btn-primary'
        }
    )


class AdminForm(FlaskForm):
    '''管路员注册表单'''
    name = StringField(
        label='管理员名称',
        validators=[
            DataRequired('请输入管理员名称!')
        ],
        description='管理员名称',
        render_kw={
            'class': 'form-control',
            'placeholder': '请输入管理员名称！',
            'required': 'required'
        }
    )
    pwd = PasswordField(
        label='管理员密码',
        validators=[
            DataRequired('请输入管理员密码!')
        ],
        description='管理员密码',
        render_kw={
            'class': 'form-control',
            'placeholder': '请输入管理员密码！',
            'required': 'required'
        }
    )
    repwd = PasswordField(
        label='管理员重复密码',
        validators=[
            DataRequired('请输入管理员重复密码!'),
            EqualTo('pwd',message='两次密码输入不一致!')  #验证两次密码是否一致!
        ],
        description='管理员重复密码',
        render_kw={
            'class': 'form-control',
            'placeholder': '请输入管理员重复密码！',
            'required': 'required'
        }
    )
    role_id = SelectField(
        label='所属角色',
        validators=[
            DataRequired('请勾选所属角色!')
        ],
        coerce=int,
        choices=[(v.id, v.name) for v in role_list],
        description='所属角色',
        render_kw={
            'class': 'form-control',
            'required': 'required'
        }
    )
    submit = SubmitField(
        '提交',
        render_kw={
            'class': 'btn btn-primary'
        }
    )




