
from datetime import datetime

from flask import Blueprint, redirect, abort, render_template, flash, url_for
from flask_login import login_user, logout_user, current_user
import pytz

from .. import db, models, forms

userbp = Blueprint('user', __name__)


@userbp.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    form = forms.SignUpForm()
    if form.validate_on_submit():
        user = models.User.query\
            .filter(db.or_(
                db.func.lower(models.User.name) == db.func.lower(form.data['username']),
                db.func.lower(models.User.email) == db.func.lower(form.data['email']),
            )).first()
        if user is None:
            user = models.User()
            user.name = form.data['username']
            user.email = form.data['email']
            user.password = form.data['password']
            user.status = models.UserStatus.query.filter_by(name='User').first()
            user.signed_up_date = datetime.now(pytz.utc)
            db.session.add(user)
            db.session.commit()
            return redirect(url_for('main.home'))
        flash('A user with that email or username already exists.', 'error')

    return render_template('user/sign-up.html', form=form)


@userbp.route('/user/<int:user_id>')
def user_view(user_id):
    user = models.User.query.filter_by(id=user_id).first()
    if user is None:
        return abort(404, 'No such user.')
    return render_template('user/view.html', user=user)


@userbp.route('/login', methods=['GET', 'POST'])
def login():
    form = forms.LoginForm()
    if form.validate_on_submit():
        fail_message = 'Incorrect user credentials.'
        user = models.User.query.filter(
            db.func.lower(models.User.email) == db.func.lower(form.data['email'])
        ).first()
        if user is None:
            flash(fail_message, 'error')
        elif not user.check_password(form.data['password']):
            flash(fail_message, 'error')
        else:
            flash('Login successful')
            login_user(user)
            return redirect(url_for('main.home'))
    return render_template('user/login.html', form=form)


@userbp.route('/logout')
def logout():
    if current_user.is_authenticated:
        logout_user()
    return redirect(url_for('main.home'))
