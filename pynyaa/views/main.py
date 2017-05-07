
from datetime import datetime
import os

from flask import (
    Blueprint, render_template, abort, request, Response, g, redirect, url_for,
    current_app, flash
)
from flask.helpers import send_from_directory
from flask_login import current_user
import pytz

from .. import models, db, forms
from .. import utils

main = Blueprint('main', __name__)


@main.route('/')
@main.route('/page/<int:page>')
@main.route('/search', endpoint='search')
@main.route('/search/<int:page>', endpoint='search')
@main.route('/feed.xml', endpoint='feed')
def home(page=1):
    query = models.Torrent.query\
        .options(
            db.joinedload(models.Torrent.category),
            db.joinedload(models.Torrent.sub_category),
            db.joinedload(models.Torrent.status),
        )

    # no point in listing torrents that don't have hashes or filesizes
    query = query.filter(db.and_(
        models.Torrent.hash.isnot(None),
        models.Torrent.hash != '',
        models.Torrent.filesize != 0,
        models.Torrent.upload_hash.is_(None)
    ))

    search = g.search
    if search['category'] and '_' in search['category']:
        cat, subcat = search['category'].split('_', 1)
        if cat and cat.isdigit():
            query = query.filter(models.Torrent.category_id == int(cat))
        if subcat and subcat.isdigit():
            query = query.filter(models.Torrent.sub_category_id == int(subcat))

    if search['status'] and search['status'].isdigit():
        query = query.filter(models.Torrent.status_id == int(search['status']))

    if search['query']:
        if len(search['query']) == 40 and all(char in '0123456789abcdef'
                                              for char in search['query'].lower()):
            query = query.filter(models.Torrent.hash == search['query'].lower())
        else:
            words = search['query'].split()
            for word in words:
                query = query.filter(models.Torrent.name.ilike(f'%{word}%'))

    if search['sort'] and search['sort'] in ('id', 'name', 'date', 'downloads'):
        sort_column = getattr(models.Torrent, search['sort'])
    else:
        sort_column = models.Torrent.id
        search['sort'] = 'id'

    ordering = 'desc'
    if search['order'] and search['order'] in ('asc', 'desc'):
        ordering = search['order']
    search['order'] = ordering

    sort_and_ordering = getattr(sort_column, ordering)()
    query = query.order_by(sort_and_ordering)

    pagination = query.paginate(page=page, per_page=search['max'])
    if request.endpoint == 'main.feed':
        return Response(
            render_template('feed.xml', torrents_pagination=pagination),
            mimetype='application/xml')
    else:
        return render_template('home.html', torrents_pagination=pagination)


@main.route('/faq')
def faq():
    return render_template('faq.html')


@main.route('/view/<int:torrent_id>')
def torrent_view(torrent_id):
    torrent = models.Torrent.query\
        .options(
            db.joinedload(models.Torrent.category),
            db.joinedload(models.Torrent.sub_category),
            db.joinedload(models.Torrent.status),
            db.joinedload(models.Torrent.comments).joinedload(models.Comment.user),
        ).filter_by(id=torrent_id).first()
    if torrent is None:
        return abort(404)
    return render_template('view.html', torrent=torrent)


@main.route('/upload', methods=['GET', 'POST'])
def upload():
    """Upload torrent file.

    Possibly requires some more sanity checks.
    """
    if not current_user.is_authenticated:
        flash('You need to login to upload files.')
        return redirect(url_for('user.login'))

    upload_form = forms.UploadTorrentForm()

    categories = models.Category.query \
        .options(db.joinedload(models.Category.sub_categories)) \
        .order_by(models.Category.name).all()

    cats = {}
    for cat in categories:
        for subcat in cat.sub_categories:
            cats[f'{cat.id}_{subcat.id}'] = f'{cat.name} - {subcat.name}'
    upload_form.category.choices = cats.items()

    if not upload_form.validate_on_submit():
        return render_template('upload/upload.html', categories=categories, form=upload_form)

    torrent_file = upload_form.data['torrent']

    torrent_info = utils.torrent.get_info(torrent_file.stream)
    torrent_folder = os.path.join(current_app.static_folder, '..', 'uploads', 'torrents')
    torrent_file.save(os.path.join(torrent_folder, f'{torrent_info.hash}.torrent'))

    torrent = models.Torrent()
    torrent.is_sqlite_import = False
    torrent.upload_hash = utils.random_string(21)
    torrent.uploader = current_user
    torrent.name = torrent_info.name
    torrent.hash = torrent_info.hash
    torrent.filesize = torrent_info.length

    cat, subcat = upload_form.category.data.split('_', 1)
    torrent.category_id = cat
    torrent.sub_category_id = subcat

    torrent.downloads = 0
    torrent.stardom = 0
    torrent.date = datetime.now(pytz.utc)

    torrent.t_announce = torrent_info.trackers
    torrent.t_comment = torrent_info.comment
    torrent.t_created_by = torrent_info.created_by
    torrent.t_creation_date = torrent_info.creation_date

    file_paths = []
    file_sizes = []
    for path, size in torrent_info.files:
        file_paths.append(path)
        file_sizes.append(size)

    torrent.file_paths = file_paths
    torrent.file_sizes = file_sizes
    db.session.add(torrent)
    db.session.commit()

    return redirect(url_for('main.upload_more', upload_hash=torrent.upload_hash))


@main.route('/upload/<upload_hash>', methods=['GET', 'POST'])
def upload_more(upload_hash):
    torrent = models.Torrent.query.filter_by(upload_hash=upload_hash).first()
    if torrent is None:
        return abort(404)
    detail_form = forms.UploadDetailForm()

    if detail_form.validate_on_submit():
        torrent.upload_hash = None

        torrent.description = detail_form.data.get('description')
        torrent.website_link = detail_form.data.get('website')
        db.session.commit()
        return redirect(url_for('main.torrent_view', torrent_id=torrent.id))

    return render_template('upload/details.html', torrent=torrent, form=detail_form)


@main.route('/download/<int:torrent_id>')
def download_torrent(torrent_id):
    torrent = models.Torrent.query.filter_by(id=torrent_id).first()
    if torrent is None:
        return abort(404)

    torrents_folder = os.path.abspath(os.path.join(
        current_app.static_folder, '..', 'uploads', 'torrents'
    ))

    filename = f'{torrent.hash}.torrent'
    absolute_filename = os.path.join(torrents_folder, filename)
    if not os.path.exists(absolute_filename):
        return abort(404)

    return send_from_directory(
        torrents_folder,
        filename,
        as_attachment=True,
        attachment_filename=f'{torrent.name}.torrent',
    )
