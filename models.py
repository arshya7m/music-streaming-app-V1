from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from app import db,app



class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    is_creator = db.Column(db.Boolean,nullable=False, default=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)
    is_blacklisted = db.Column(db.Boolean,nullable=False, default=False)

    # relationships
    albums = db.relationship('Album', backref='creator', lazy=True)
    playlists = db.relationship('Playlist', backref='playlist_creator', lazy=True)

class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # relationships
    songs = db.relationship('Song', secondary='playlist_song', backref='playlistsforsong')

playlist_song = db.Table(
    'playlist_song',
    db.Column('playlist_id', db.Integer, db.ForeignKey('playlist.id'), primary_key=True),
    db.Column('song_id', db.Integer, db.ForeignKey('song.id'), primary_key=True)
)

class Song(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    lyrics = db.Column(db.Text)
    duration = db.Column(db.Integer)
    date_created = db.Column(db.DateTime, nullable=False)
    rating = db.Column(db.Integer)
    album_id = db.Column(db.Integer, db.ForeignKey('album.id'), nullable=False)


class Album(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    genre = db.Column(db.String(50))
    artist = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # relationship
    songs = db.relationship('Song', backref='album', lazy=True)

with app.app_context():
    db.create_all()

    admin = User.query.filter_by(is_admin=True).first()
    if not admin:
        admin = User(username='admin', password='admin', name='admin', is_admin=True)
        db.session.add(admin)
        db.session.commit()
