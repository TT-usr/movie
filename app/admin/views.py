# -*- coding: utf-8 -*-
from . import admin
from flask import render_template, redirect, url_for, Response, flash, session, request
import json
from app.admin.forms import LoginForm, TagForm, MovieForm, PreviewForm, PwdForm, AuthForm, RoleForm, AdminForm
from app.models import Admin, Tag, Movie, Preview, User, Comment, Moviecol, Oplog, Adminlog, Userlog, Auth, Role
from functools import wraps
from app import db, app
from sqlalchemy import func
from werkzeug.utils import secure_filename
import os, uuid, datetime


# 上下文处理器
# 可以理解为模版内可以使用的全局变量
# 使用方法为 : 直接 {{ key }} 即可
@admin.context_processor
def tpl_extra():
    data = dict(
        online_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    return data


# 权限控制的装饰器
def admin_login_req(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin' not in session:
            return redirect(url_for('admin.login', next=request.url))
        return f(*args, **kwargs)

    return decorated_function


# 修改文件名称
def change_filename(filename):
    fileinfo = os.path.splitext(filename)
    filename = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + str(uuid.uuid4().hex) + fileinfo[-1]
    return filename


@admin.route("/")
@admin_login_req
def index():
    return render_template('admin/index.html')


@admin.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        data = form.data
        admin = Admin.query.filter_by(name=data['account']).first()
        if not admin:
            flash("输入的账户不存在!", 'err')
            return redirect(url_for('admin.login'))
        if not admin.check_pwd(data['pwd']):
            flash("用户名与密码不匹配!", 'err')
            return redirect(url_for('admin.login'))
        session['admin'] = data['account']
        session['admin_id'] = admin.id
        add_admin_loginlog()
        return redirect(request.args.get('next') or url_for('admin.index'))
    return render_template('admin/login.html', form=form)


@admin.route('/logout')
@admin_login_req
def logout():
    session.pop('admin', None)
    session.pop('admin_id', None)
    return redirect(url_for('admin.login'))


@admin.route("/pwd", methods=['GET', 'POST'])
@admin_login_req
def pwd():
    form = PwdForm()
    if form.validate_on_submit():
        data = form.data
        admin = Admin.query.filter_by(
            name=session['admin']
        ).first()
        from werkzeug.security import generate_password_hash
        admin.pwd = generate_password_hash(data['new_pwd'])
        db.session.add(admin)
        db.session.commit()
        flash('修改密码成功', 'ok')
        return redirect(url_for('admin.pwd'))
    return render_template('admin/pwd.html', form=form)


def add_admin_loginlog():
    loginlog = Adminlog(
        admin_id=session['admin_id'],
        ip=request.remote_addr,
    )
    db.session.add(loginlog)
    db.session.commit()


def add_admin_oplog(reason):
    oplog = Oplog(
        admin_id=session['admin_id'],
        ip=request.remote_addr,
        reason=reason,
    )
    db.session.add(oplog)
    db.session.commit()


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
        add_admin_oplog("添加标签%s" % data['name'])
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
        # db.session.add(tag)
        db.session.commit()
        # db.session.query(Tag.id == tag.id).update({'name': data['name']})
        return redirect(url_for('admin.tag_list', page=1))
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


def save_path():
    if not os.path.exists(app.config["UP_DIR"]):
        os.makedirs(app.config["UP_DIR"])
        os.chmod(app.config["UP_DIR"], "rw")


def save_url(form):
    logo = save_photo(form)
    url = save_video(form)
    return [url, logo]


def save_photo(form):
    save_path()
    file_logo = secure_filename(form.logo.data.filename)
    logo = change_filename(file_logo)
    form.logo.data.save(app.config["UP_DIR"] + logo)
    return logo


def save_video(form):
    save_path()
    file_url = secure_filename(form.url.data.filename)
    url = change_filename(file_url)
    form.url.data.save(app.config["UP_DIR"] + url)
    return url


@admin.route('/movie/add', methods=['POST', 'GET'])
@admin_login_req
def movie_add():
    form = MovieForm()
    if form.validate_on_submit():
        data = form.data
        source = save_url(form)
        movie = Movie(
            title=data['title'],
            url=source[0],
            info=data['info'],
            star=int(data['star']),
            logo=source[-1],
            playnum=0,
            commentnum=0,
            tag_id=int(data['tag_id']),
            area=data['area'],
            release_time=data['release_time'],
            length=data["length"],
        )
        db.session.add(movie)
        db.session.commit()
        flash('添加电影成功', 'ok')
        return redirect(url_for('admin.movie_add'))
    return render_template('admin/movie_add.html', form=form)


@admin.route("/movie/list/<int:page>", methods=['GET'])
@admin_login_req
def movie_list(page=None):
    if page == None:
        page = 1
    page_data = Movie.query.join(Tag).filter(
        Tag.id == Movie.tag_id
    ).order_by(
        Movie.addtime.desc()
    ).paginate(page=page, per_page=10)
    print(page_data)
    return render_template('admin/movie_list.html', page_data=page_data)


@admin.route('/movie/del/<int:id>', methods=["GET"])
@admin_login_req
def movie_del(id=None):
    if id == None:
        pass
    try:
        movie = Movie.query.get_or_404(int(id))
    except:
        add_admin_oplog('删除<movie_id = %s>电影失败! 原因:电影不存在' % id)
    db.session.delete(movie)
    db.session.commit()
    flash("删除电影成功!", 'ok')
    add_admin_oplog('删除<movie_id = %s>电影成功!' % id)
    return redirect(url_for("admin.movie_list", page=1))


@admin.route('movie/edit/<int:id>', methods=['GET', 'POST'])
@admin_login_req
def movie_edit(id=None):
    form = MovieForm()
    form.url.validators = []
    form.logo.validators = []
    if id == None:
        pass
    try:
        movie = Movie.query.get_or_404(int(id))
    except:
        add_admin_oplog('编辑<movie_id = %s>电影失败! 原因:电影不存在' % id)
        flash('编辑电影失败,找不到您想编辑的电影信息!', 'err')
        return redirect(url_for('admin.movie_list', page=1))

    if request.method == 'GET':
        form.info.data = movie.info
        form.tag_id.data = movie.tag_id
        form.star.data = movie.star
    if form.validate_on_submit():
        data = form.data
        movie_count = Movie.query.filter_by(title=data['title']).count
        if movie_count == 1 and movie.title != data['title']:
            flash('片名已经存在', 'err')
            add_admin_oplog('修改<movie_id = %s>预告失败,片名已存在!' % id)
            return redirect(url_for('admin.movie.edit', id=id))
        # 判断是否更改了图片/视频
        if form.url.data.filename != "":
            movie.url = save_url(form)
        if form.logo.data.filename != "":
            movie.log = save_photo(form)

        movie.title = data['title'],
        movie.info = data['info'],
        movie.star = int(data['star']),
        movie.playnum = 0,
        movie.commentnum = 0,
        movie.tag_id = int(data['tag_id']),
        movie.area = data['area'],
        movie.release_time = data['release_time'],
        movie.length = data["length"],
        db.session.add(movie)
        db.session.commit()
        flash('修改电影信息成功!', 'ok')
    return render_template('admin/movie_edit.html', form=form, movie=movie)


@admin.route('/preview/add', methods=['GET', 'POST'])
@admin_login_req
def preview_add():
    form = PreviewForm()
    if form.validate_on_submit():
        data = form.data
        logo = save_photo(form)
        title = data['title']
        preview = Preview(
            title=title,
            logo=logo
        )
        db.session.add(preview)
        db.session.commit()
        flash('添加预告成功!', 'ok')
        add_admin_oplog('添加<name = %s>预告成功!' % preview.name)
    return render_template('admin/preview_add.html', form=form)


@admin.route('/preview/edit/<int:id>', methods=['GET', 'POST'])
@admin_login_req
def preview_edit(id=None):
    if id == None:
        pass
    form = PreviewForm()
    form.logo.validators = []
    preview = Preview.query.get_or_404(int(id))
    if request.method == 'GET':
        form.title.data = preview.title
        form.logo.data = preview.logo
    if form.validate_on_submit():
        data = form.data
        if form.logo.data.filename != '':
            preview.logo = save_photo(form)
        preview.title = data['title']
        db.session.add(preview)
        db.session.commit()
        flash('修改预告成功!', 'ok')
        add_admin_oplog('修改<name = %s>预告成功!' % preview.name)
        return redirect(url_for('admin.preview_edit', id=id))

    return render_template('admin/preview_edit.html', form=form, preview=preview)


@admin.route('/preview/del/<int:id>', methods=["GET"])
@admin_login_req
def preview_del(id=None):
    if id == None:
        pass
    preview = Preview.query.get_or_404(int(id))
    db.session.delete(preview)
    db.session.commit()
    flash("删除预告成功!", 'ok')
    add_admin_oplog('删除<name = %s>预告成功!' % preview.name)
    return redirect(url_for("admin.preview_list", page=1))


@admin.route("/preview/list/<int:page>", methods=['GET'])
@admin_login_req
def preview_list(page=None):
    if page == None:
        page = 1
    page_data = Preview.query.order_by(Preview.addtime.desc()).paginate(page, 10)
    return render_template('admin/preview_list.html', page_data=page_data)


@admin.route('/user/view/<int:id>', methods=['GET'])
@admin_login_req
def user_view(id=None):
    if id == None:
        pass
    user = User.query.get_or_404(int(id))
    return render_template('admin/user_view.html', user=user)


@admin.route('/user/del/<int:id>', methods=['GET'])
@admin_login_req
def user_del(id=None):
    if id == None:
        pass
    user = User.query.get_or_404(int(id))
    db.session.delete(user)
    db.session.commit()
    flash('删除用户成功!', 'ok')
    add_admin_oplog('删除<name = %s>用户成功!' % user.name)
    return redirect(url_for('admin.user_list', page=1))


@admin.route("/user/list/<int:page>", methods=['GET'])
@admin_login_req
def user_list(page=None):
    if page == None:
        page = 1
    page_data = User.query.order_by(User.addtime.desc()).paginate(page, 10)
    return render_template('admin/user_list.html', page_data=page_data)


@admin.route("/comment/list/<int:page>", methods=['GET'])
@admin_login_req
def comment_list(page=None):
    if page == None:
        page = 1
    page_data = Comment.query.join(
        Movie
    ).join(
        User
    ).filter(
        Movie.id == Comment.movie_id,
        User.id == Comment.user_id
    ).order_by(
        Comment.addtime.desc()
    ).paginate(page, 10)
    return render_template('admin/comment_list.html', page_data=page_data)


@admin.route('/comment/del/<int:id>', methods=['GET'])
@admin_login_req
def comment_del(id=None):
    if id == None:
        pass
    comment = Comment.query.get_or_404(int(id))
    db.session.delete(comment)
    db.session.commit()
    flash('删除评论成功!', 'ok')
    add_admin_oplog('删除<%s>评论成功!' % comment.name)
    return redirect(url_for('admin.comment_list', page=1))


@admin.route("/moviecol/list/<int:page>", methods=['GET'])
@admin_login_req
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
    ).paginate(page, 10)
    return render_template('admin/moviecol_list.html', page_data=page_data)


@admin.route('/moviecol/del/<int:id>', methods=['GET'])
@admin_login_req
def moviecol_del(id=None):
    if id == None:
        pass
    moviecol = Moviecol.query.get_or_404(int(id))
    db.session.delete(moviecol)
    db.session.commit()
    flash('删除收藏成功!', 'ok')
    add_admin_oplog('删除<movie_id = %s>的收藏记录成功!' % moviecol.movie_id)
    return redirect(url_for('admin.moviecol_list', page=1))


@admin.route("/log_list/option/<int:page>", methods=['GET'])
@admin_login_req
def optionlog_list(page=None):
    if page == None:
        page = 1
    page_data = Oplog.query.join(
        Admin
    ).filter(
        Admin.id == Oplog.admin_id,
    ).order_by(
        Oplog.addtime.desc()
    ).paginate(page=page, per_page=2)

    return render_template('admin/log_option_list.html', page_data=page_data)


@admin.route("/log_list/admin/<int:page>", methods=['GET'])
@admin_login_req
def adminlog_list(page=None):
    if page == None:
        page = 1
    page_data = Adminlog.query.join(
        Admin
    ).filter(
        Admin.id == Adminlog.admin_id,
    ).order_by(
        Adminlog.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template('admin/log_admin_list.html', page_data=page_data)


@admin.route("/log_list/user/<int:page>", methods=['GET'])
@admin_login_req
def userlog_list(page=None):
    if page == None:
        page = 1
    page_data = Userlog.query.join(
        User
    ).filter(
        User.id == Userlog.user_id,
    ).order_by(
        Userlog.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template('admin/log_user_list.html', page_data=page_data)


@admin.route("/auth/list/<int:page>", methods=['GET'])
@admin_login_req
def auth_list(page=None):
    if page == None:
        page = 1
    page_data = Auth.query.order_by(
        Auth.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template('admin/auth_list.html', page_data=page_data)


@admin.route("/auth/add", methods=['GET', 'POST'])
@admin_login_req
def auth_add():
    form = AuthForm()
    if form.validate_on_submit():
        data = form.data
        auth = Auth(
            name=data['name'],
            url=data['url']
        )
        db.session.add(auth)
        db.session.commit()
        flash('添加权限成功!', 'ok')
        add_admin_oplog('添加<%s>权限成功!' % auth.name)
        return redirect(url_for('admin.auth_list', page=1))
    return render_template('admin/auth_add.html', form=form)


@admin.route('/auth/del/<int:id>', methods=['GET'])
@admin_login_req
def auth_del(id=None):
    auth = Auth.query.get_or_404(int(id))
    db.session.delete(auth)
    db.session.commit()
    flash('删除权限成功!', 'ok')
    add_admin_oplog('删除<%s>权限成功!' % auth.name)
    return redirect(url_for('admin.auth_list', page=1))


@admin.route("/auth/edit/<int:id>", methods=['GET', 'POST'])
@admin_login_req
def auth_edit(id=None):
    form = AuthForm()
    auth = Auth.query.get_or_404(int(id))
    if request.method == 'GET':
        form.name.data = auth.name
        form.url.data = auth.url
    if form.validate_on_submit():
        data = form.data
        print(form.data)
        auth.name = data['name']
        auth.url = data['url']
        db.session.add(auth)
        db.session.commit()
        flash('修改权限成功!', 'ok')
        add_admin_oplog('编辑<%s>权限成功!' % auth.name)
        return redirect(url_for('admin.auth_list', page=1))
    return render_template('admin/auth_edit.html', form=form)


@admin.route("/role/list/<int:page>")
@admin_login_req
def role_list(page):
    if page == None:
        page = 1
    page_data = Role.query.order_by(
        Role.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template('admin/role_list.html', page_data=page_data)


@admin.route("/role/edit/<int:id>", methods=['GET', 'POST'])
@admin_login_req
def role_edit(id=None):
    form = RoleForm()
    role = Role.query.get_or_404(int(id))
    if request.method == 'GET':
        form.auths.data = list(map(lambda v: int(v), role.auths.split(",")))
    if form.validate_on_submit():
        data = form.data
        role.name = data["name"]
        role.auths = ",".join(map(lambda v: str(v), data["auths"]))
        db.session.add(role)
        db.session.commit()
        flash("编辑角色成功", "ok")
        return redirect(url_for('admin.role_list', page=1))
    return render_template('admin/role_edit.html', form=form, role=role)


@admin.route("/role/add", methods=['POST', 'GET'])
@admin_login_req
def role_add():
    form = RoleForm()
    if form.validate_on_submit():
        data = form.data
        print(data)
        role = Role(
            name=data['name'],
            auths=",".join(map(lambda v: str(v), data["auths"]))
        )
        db.session.add(role)
        db.session.commit()
        flash("添加角色成功!", "ok")
        return redirect(url_for('admin.role_add'))
    return render_template('admin/role_add.html', form=form)


@admin.route("/admin_add", methods=['GET', 'POST'])
@admin_login_req
def admin_add():
    form = AdminForm()
    from werkzeug.security import generate_password_hash
    if form.validate_on_submit():
        data = form.data
        admin = Admin(
            name=data["account"],
            pwd=generate_password_hash(data["pwd"]),
            role_id=data["role_id"],
            is_super=1
        )
        db.session.add(admin)
        db.session.commit()
        flash("添加管理员成功", "ok")
    return render_template('admin/admin_add.html', form=form)


@admin.route("/admin_list/<int:page>")
@admin_login_req
def admin_list(page):
    if page == None:
        page = 1
    #     关联查询
    page_data = Admin.query.join(Role).filter(
        Role.id == Admin.role_id
    ).order_by(
        Admin.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template('admin/admin_list.html', page_data=page_data)
