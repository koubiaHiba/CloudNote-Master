from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timezone
import bcrypt

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    notes = db.relationship('Note', backref='author', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

class Note(db.Model):
    __tablename__ = 'notes'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_favorite = db.Column(db.Boolean, default=False)  # ⭐ Note favorite
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    media = db.relationship('Media', backref='note', lazy=True, cascade='all, delete-orphan')
    tags = db.relationship('Tag', backref='note', lazy=True, cascade='all, delete-orphan')

class Media(db.Model):
    __tablename__ = 'media'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # 'image', 'video', 'document'
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)  # taille en bytes
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    note_id = db.Column(db.Integer, db.ForeignKey('notes.id'), nullable=False)

class Tag(db.Model):
    __tablename__ = 'tags'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    note_id = db.Column(db.Integer, db.ForeignKey('notes.id'), nullable=False)
    
class SharedNote(db.Model):
    __tablename__ = 'shared_notes'
    id = db.Column(db.Integer, primary_key=True)
    share_id = db.Column(db.String(100), unique=True, nullable=False)
    note_id = db.Column(db.Integer, db.ForeignKey('notes.id'), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    
# ========== FONCTIONS NOTE ==========
import uuid
import markdown
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO
import bleach
  
# ========== get_user_notes pour inclure les tags ==========

def get_user_notes(user_id, search_query=None, favorite_only=False):
    query = Note.query.filter_by(user_id=user_id)
    
    if favorite_only:
        query = query.filter_by(is_favorite=True)
    
    if search_query:
        # Rechercher dans titre, contenu ET tags
        tag_search = search_query.startswith('#')
        if tag_search:
            tag_name = search_query[1:]
            query = query.join(Tag).filter(Tag.name == tag_name)
        else:
            query = query.filter(
                db.or_(
                    Note.title.ilike(f'%{search_query}%'),
                    Note.content.ilike(f'%{search_query}%')
                )
            )
    
    return query.order_by(Note.is_favorite.desc(), Note.updated_at.desc()).all()


def get_note(note_id, user_id):
    return Note.query.filter_by(id=note_id, user_id=user_id).first()

def create_note(title, content, user_id):
    note = Note(title=title, content=content, user_id=user_id)
    db.session.add(note)
    db.session.commit()
    return note

def update_note(note_id, user_id, title=None, content=None, is_favorite=None):
    note = get_note(note_id, user_id)
    if note:
        if title is not None:
            note.title = title
        if content is not None:
            note.content = content
        if is_favorite is not None:
            note.is_favorite = is_favorite
        note.updated_at = datetime.now(timezone.utc)
        db.session.commit()
    return note

def delete_note(note_id, user_id):
    note = get_note(note_id, user_id)
    if note:
        # Supprimer les fichiers physiques
        import os
        for media in note.media:
            if os.path.exists(media.file_path):
                os.remove(media.file_path)
        db.session.delete(note)
        db.session.commit()
        return True
    return False

def toggle_favorite(note_id, user_id):
    note = get_note(note_id, user_id)
    if note:
        note.is_favorite = not note.is_favorite
        db.session.commit()
        return note.is_favorite
    return None

# ========== FONCTIONS MEDIA ==========
def add_media_to_note(note_id, user_id, filename, original_filename, file_type, file_path, file_size):
    """Ajoute un fichier média à une note"""
    note = get_note(note_id, user_id)
    if not note:
        return None
    
    media = Media(
        filename=filename,
        original_filename=original_filename,
        file_type=file_type,
        file_path=file_path,
        file_size=file_size,
        note_id=note_id
    )
    db.session.add(media)
    db.session.commit()
    return media

def get_note_media(note_id, user_id):
    """Récupère tous les médias d'une note"""
    note = get_note(note_id, user_id)
    if note:
        return note.media
    return []

def delete_media(media_id, user_id):
    """Supprime un média spécifique"""
    media = Media.query.get(media_id)
    if media and media.note.user_id == user_id:
        import os
        if os.path.exists(media.file_path):
            os.remove(media.file_path)
        db.session.delete(media)
        db.session.commit()
        return True
    return False