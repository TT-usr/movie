# -*- coding: utf-8 -*-
from . import admin
from flask import render_template, redirect, url_for, Response, flash, session, request
import json
from app.admin.forms import LoginForm, TagForm
from app.models import Admin, Tag
from functools import wraps
from app import db
from sqlalchemy import func


def admin_login_req(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin' not in session:
            return redirect(url_for('admin.login', next=request.url))
        return f(*args, **kwargs)

    return decorated_function


@admin.route("/")
@admin_login_req
def index():
    return render_template('admin/index.html')


@admin.route('/getName')
@admin_login_req
def name():
    return Response(json.dumps({'name': 'jack'}), mimetype='application/json')


@admin.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        data = form.data
        admin = Admin.query.filter_by(name=data['account']).first()
        if not admin:
            flash("输入的账户不存在!")
            return redirect(url_for('admin.login'))
        if not admin.check_pwd(data['pwd']):
            flash("用户名与密码不匹配!")
            return redirect(url_for('admin.login'))
        session['admin'] = data['account']
        print(request.args)
        return redirect(request.args.get('next') or url_for('admin.index'))
    return render_template('admin/login.html', form=form)


@admin.route('/logout')
@admin_login_req
def logout():
    session.pop('admin', None)
    return redirect(url_for('admin.login'))


@admin.route("/pwd")
@admin_login_req
def pwd():
    return render_template('admin/pwd.html')


@admin.route('/tag/add', methods=['POST', 'GET'])
@admin_login_req
def tag_add():
    form = TagForm()
    if form.validate_on_submit():
        data = form.data
        tagcount = Tag.query.filter_by(name=data['name']).count()
        if tagcount == 1:
            flash('名称已经存在', "err")
            return redirect(url_for('admin.tag_add'))
        tag = Tag(
            name=data['name']
        )
        db.session.add(tag)
        db.session.commit()
        flash('添加标签成功!', 'ok')
        # return redirect(url_for('admin.tag_list', page=1))
    return render_template('admin/tag_add.html', form=form)


@admin.route('/tag/edit/<int:id>', methods=['GET', 'POST'])
@admin_login_req
def tag_edit(id=None):
    # if id == None:
    #     return redirect(url_for('admin.tag_list', page=1))
    form = TagForm()
    tag = Tag.query.get_or_404(id)
    if form.validate_on_submit():
        data = form.data
        tagcount = Tag.query.filter_by(name=data['name']).count()
        if tagcount == 1 and tag.name == data['name']:
            flash('名称已经存在', "err")
            return redirect(url_for('admin.tag_edit', id=id))
        tag.name = data['name']
        db.session.add(tag)
        db.session.commit()
        # db.session.query(Tag.id == tag.id).update({Tag.name: data['name']})
        return redirect(url_for('admin.list', page=1))
    return render_template('admin/tag_edit.html', tag=tag, form=form)


@admin.route("/tag/list/<int:page>", methods=["get"])
@admin_login_req
def tag_list(page=None):
    if page is None or page == 0:
        return redirect(url_for('admin.tag_list', page=1))
    # 查询数量
    count = db.session.query(func.count('Tag.id')).scalar()
    # 这里判断是否大于页数
    per_page = 10
    if page > int(count / per_page) + 1:
        return redirect(url_for('admin.tag_list', page=int(count / 10) + 1))
    page_data = Tag.query.order_by(
        Tag.addtime.desc()
    ).paginate(page=page, per_page=per_page)
    return render_template('admin/tag_list.html', page_data=page_data)


@admin.route("/tag/del/<int:id>", methods=["get"])
@admin_login_req
def tag_del(id=None):
    if id == None:
        return redirect(url_for('admin.tag_list', page=1))
    tag = Tag.query.filter_by(id=id).first_or_404()
    db.session.delete(tag)
    db.session.commit()
    flash("删除标签成功!", 'ok')
    return redirect(url_for('admin.tag_list', page=1))


@admin.route('/movie/add')
@admin_login_req
def movie_add():
    return render_template('admin/movie_add.html')


@admin.route("/movie/list")
@admin_login_req
def movie_list():
    return render_template('admin/movie_list.html')


@admin.route('/preview/add')
@admin_login_req
def preview_add():
    return render_template('admin/preview_add.html')


@admin.route("/preview/list")
@admin_login_req
def preview_list():
    return render_template('admin/preview_list.html')


@admin.route('/user/view')
@admin_login_req
def user_view():
    return render_template('admin/user_view.html')


@admin.route("/user/list")
@admin_login_req
def user_list():
    return render_template('admin/user_list.html')


@admin.route("/comment/list")
@admin_login_req
def comment_list():
    return render_template('admin/comment_list.html')


@admin.route("/moviecol/list")
@admin_login_req
def moviecol_list():
    return render_template('admin/moviecol_list.html')


@admin.route("/log_list/option")
@admin_login_req
def optionlog_list():
    return render_template('admin/log_option_list.html')


@admin.route("/log_list/admin")
@admin_login_req
def adminlog_list():
    return render_template('admin/log_admin_list.html')


@admin.route("/log_list/user")
@admin_login_req
def userlog_list():
    return render_template('admin/log_user_list.html')


@admin.route("/auth/list")
@admin_login_req
def auth_list():
    return render_template('admin/auth_list.html')


@admin.route("/auth/add")
@admin_login_req
def auth_add():
    return render_template('admin/auth_add.html')


@admin.route("/role/list")
@admin_login_req
def role_list():
    return render_template('admin/role_list.html')


@admin.route("/role/add")
@admin_login_req
def role_add():
    return render_template('admin/role_add.html')


@admin.route("/admin_add")
@admin_login_req
def admin_add():
    return render_template('admin/admin_add.html')


@admin.route("/admin_list")
@admin_login_req
def admin_list():
    return render_template('admin/admin_list.html')
