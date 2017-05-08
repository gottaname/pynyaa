
import os
from urllib.parse import urlencode

from flask import current_app

from .. import db


class Torrent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1024), nullable=False)
    hash = db.Column(db.String(40), index=True, nullable=False)

    is_sqlite_import = db.Column(db.Boolean, default=False)
    upload_hash = db.Column(db.String(21))

    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    uploader = db.relationship('User', backref='uploads')

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)

    sub_category_id = db.Column(db.Integer, db.ForeignKey('sub_category.id'), nullable=False)
    
    status_id = db.Column(db.Integer, db.ForeignKey('status.id'))

    date = db.Column(db.DateTime(True), index=True)
    downloads = db.Column(db.Integer, index=True)
    stardom = db.Column(db.Integer, index=True)
    filesize = db.Column(db.BigInteger, index=True)

    description = db.Column(db.Text)
    website_link = db.Column(db.String(1024))

    t_creation_date = db.Column(db.DateTime(True))
    t_created_by = db.Column(db.String(255))
    t_comment = db.Column(db.Text)
    t_announce = db.Column(db.ARRAY(db.String(100)))

    file_paths = db.Column(db.ARRAY(db.String(1024)))
    file_sizes = db.Column(db.ARRAY(db.BigInteger))

    @property
    def cat_url_param(self):
        return f'{self.category_id}_{self.sub_category_id}'

    @property
    def file_exists(self):
        path = os.path.join(current_app.static_folder, '..', 'uploads',
                            'torrents', f'{self.hash}.torrent')
        if os.path.exists(path):
            return True
        return False

    @property
    def magnet(self):
        magnet_query = dict(
            xt=f'urn:btih:{self.hash.lower()}',
            dn=self.name
        )
        if self.t_announce:
            magnet_query['tr'] = self.t_announce
        return f'magnet:?{urlencode(magnet_query)}'


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1024))
    torrents = db.relationship('Torrent', backref='category')
    sub_categories = db.relationship('SubCategory', backref='category')


class SubCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1024))

    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    torrents = db.relationship('Torrent', backref='sub_category')

    @property
    def image_url(self):
        return f'img/torrents/{self.id}.png'


class Status(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    label = db.Column(db.String(50))
    torrents = db.relationship('Torrent', backref='status')
    
    @property
    def css_class(self):
        if self.name == 'a+':
            return 'aplus'
        return self.name


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text)
    date = db.Column(db.DateTime(True))
    av = db.Column(db.String(255))

    old_user_name = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='comments')

    torrent_id = db.Column(db.Integer, db.ForeignKey('torrent.id'))
    torrent = db.relationship('Torrent', backref='comments')

    __table_args__ = (
        db.CheckConstraint(
            'old_user_name IS NULL AND user_id IS NOT NULL OR '
            'old_user_name IS NOT NULL AND user_id IS NULL',
            'chk_user_old_name'),
    )
