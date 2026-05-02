import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging
import platform
import traceback
import uuid
from datetime import datetime, timezone, timedelta
from time import time

import psutil
from flask import Flask, g, jsonify, render_template, request, send_from_directory, redirect, url_for, send_file
from werkzeug.utils import secure_filename
from pythonjsonlogger.json import JsonFormatter

# ========== INITIALISATION ==========
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
logging.root.setLevel(logging.INFO)
logging.root.handlers = [_handler]
logger = logging.getLogger("cloudnotes")

app = Flask(__name__)
APP_VERSION = "1.0.0"

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-prod')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///notes.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# CORRECTION: Utilisez un chemin absolu
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# Créer le dossier d'upload
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ========== EXTENSIONS ==========
from app.models import db, User, Note, Media, Tag, SharedNote
from app.models import (
    get_user_notes, get_note, create_note, update_note, 
    delete_note, toggle_favorite, add_media_to_note, delete_media
)
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=int(user_id)).first()

# Créer les tables
with app.app_context():
    db.create_all()

# ========== LOGGING MIDDLEWARE ==========
@app.before_request
def before_request():
    g.start_time = time()
    g.request_id = str(uuid.uuid4())

@app.after_request
def after_request(response):
    elapsed_ms = (time() - g.start_time) * 1000
    response.headers["X-Request-ID"] = g.request_id
    logger.info(
        "request",
        extra={
            "request_id": g.request_id,
            "method": request.method,
            "path": request.path,
            "status": response.status_code,
            "response_time_ms": round(elapsed_ms, 2),
        },
    )
    return response

# ========== ROUTES PUBLIQUES ==========
@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/health")
def health():
    proc = psutil.Process()
    mem_mb = proc.memory_info().rss / (1024 * 1024)
    in_container = os.path.exists("/.dockerenv")
    on_azure = bool(os.environ.get("WEBSITE_SITE_NAME"))
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": APP_VERSION,
        "environment": {
            "python_version": platform.python_version(),
            "container": in_container,
            "azure": on_azure,
        },
    })

# ========== AUTHENTIFICATION ==========
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        data = request.get_json() or request.form
        user = User.query.filter_by(username=data.get('username')).first()
        if user and user.check_password(data.get('password')):
            login_user(user)
            return jsonify({'message': 'logged in', 'username': user.username}), 200
        return jsonify({'error': 'invalid credentials'}), 401
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        data = request.get_json() or request.form
        if User.query.filter_by(username=data.get('username')).first():
            return jsonify({'error': 'username exists'}), 400
        user = User(username=data.get('username'))
        user.set_password(data.get('password'))
        db.session.add(user)
        db.session.commit()
        return jsonify({'message': 'user created'}), 201
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# ========== API NOTES ==========
@app.route("/api/notes", methods=["GET"])
@login_required
def get_notes_list():
    search = request.args.get('search', '')
    favorite_only = request.args.get('favorite_only', 'false').lower() == 'true'
    notes = get_user_notes(current_user.id, search, favorite_only)
    return jsonify([{
        'id': n.id,
        'title': n.title,
        'content': n.content[:200] if n.content else '',
        'is_favorite': n.is_favorite,
        'created_at': n.created_at.isoformat(),
        'updated_at': n.updated_at.isoformat(),
        'media_count': len(n.media),
        'tags': [tag.name for tag in n.tags]
    } for n in notes])

@app.route("/api/notes/<int:note_id>", methods=["GET"])
@login_required
def get_note_detail(note_id):
    note = get_note(note_id, current_user.id)
    if not note:
        return jsonify({"error": "note not found"}), 404
    return jsonify({
        'id': note.id,
        'title': note.title,
        'content': note.content,
        'is_favorite': note.is_favorite,
        'created_at': note.created_at.isoformat(),
        'updated_at': note.updated_at.isoformat(),
        'tags': [tag.name for tag in note.tags],
        'media': [{
            'id': m.id,
            'filename': m.original_filename,
            'file_type': m.file_type,
            'url': f'/uploads/{m.filename}',
            'size': m.file_size
        } for m in note.media]
    })

@app.route("/api/notes", methods=["POST"])
@login_required
def create_new_note():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()
    if not title:
        return jsonify({"error": "title is required"}), 400
    note = create_note(title, content, current_user.id)
    return jsonify({'id': note.id, 'title': note.title}), 201

@app.route("/api/notes/<int:note_id>", methods=["PUT"])
@login_required
def update_existing_note(note_id):
    data = request.get_json(silent=True) or {}
    title = data.get("title")
    content = data.get("content")
    is_favorite = data.get("is_favorite")
    tags = data.get("tags", [])
    
    note = update_note(note_id, current_user.id, title, content, is_favorite)
    if not note:
        return jsonify({"error": "note not found"}), 404
    
    if tags is not None:
        Tag.query.filter_by(note_id=note_id).delete()
        for tag_name in tags:
            if tag_name:
                tag = Tag(name=tag_name, note_id=note_id)
                db.session.add(tag)
        db.session.commit()
    
    return jsonify({'message': 'note updated'}), 200

@app.route("/api/notes/<int:note_id>/favorite", methods=["POST"])
@login_required
def favorite_note(note_id):
    is_favorite = toggle_favorite(note_id, current_user.id)
    if is_favorite is None:
        return jsonify({"error": "note not found"}), 404
    return jsonify({'is_favorite': is_favorite}), 200

@app.route("/api/notes/<int:note_id>", methods=["DELETE"])
@login_required
def delete_existing_note(note_id):
    if delete_note(note_id, current_user.id):
        return jsonify({"message": "note deleted"}), 200
    return jsonify({"error": "note not found"}), 404

# ========== PARTAGE ==========
@app.route("/api/notes/<int:note_id>/share", methods=["POST"])
@login_required
def share_note(note_id):
    note = get_note(note_id, current_user.id)
    if not note:
        return jsonify({"error": "note not found"}), 404
    
    share_id = str(uuid.uuid4())[:8]
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    shared = SharedNote(share_id=share_id, note_id=note_id, expires_at=expires_at)
    db.session.add(shared)
    db.session.commit()
    
    return jsonify({"share_id": share_id}), 200

@app.route("/shared/<share_id>")
def view_shared_note(share_id):
    shared = SharedNote.query.filter_by(share_id=share_id).first()
    if not shared or shared.expires_at < datetime.now(timezone.utc):
        return "Lien expiré ou invalide", 404
    
    note = Note.query.get(shared.note_id)
    return render_template("shared_note.html", note=note)

# ========== EXPORT PDF ==========
@app.route("/api/notes/<int:note_id>/export")
@login_required
def export_note_pdf(note_id):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from io import BytesIO
    from bs4 import BeautifulSoup
    
    note = get_note(note_id, current_user.id)
    if not note:
        return jsonify({"error": "note not found"}), 404
    
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height - 50, note.title[:80])
    
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 80, f"Créé le: {note.created_at.strftime('%d/%m/%Y %H:%M')}")
    
    clean_text = BeautifulSoup(note.content or '', 'html.parser').get_text()
    c.setFont("Helvetica", 12)
    y = height - 120
    for line in clean_text.split('\n'):
        if y < 50:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 12)
        for i in range(0, len(line), 80):
            c.drawString(50, y, line[i:i+80])
            y -= 20
    
    c.save()
    buffer.seek(0)
    
    return send_file(buffer, as_attachment=True, download_name=f"{note.title}.pdf", mimetype='application/pdf')

# ========== API MEDIA ==========
@app.route("/api/notes/<int:note_id>/media", methods=["POST"])
@login_required
def upload_media_file(note_id):
    note = get_note(note_id, current_user.id)
    if not note:
        return jsonify({"error": "note not found"}), 404
    if 'file' not in request.files:
        return jsonify({"error": "no file provided"}), 400
    file = request.files['file']
    file_type = request.form.get('type', 'document')
    if file.filename == '':
        return jsonify({"error": "empty filename"}), 400
    
    allowed_extensions = {
        'image': {'png', 'jpg', 'jpeg', 'gif', 'webp'},
        'video': {'mp4', 'webm', 'avi', 'mov'},
        'document': {'pdf', 'doc', 'docx', 'txt', 'md', 'xlsx', 'pptx'}
    }
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if ext not in allowed_extensions.get(file_type, set()):
        return jsonify({"error": f"file type not allowed for {file_type}"}), 400
    
    filename = secure_filename(file.filename)
    unique_filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(filepath)
    file_size = os.path.getsize(filepath)
    media = add_media_to_note(note_id, current_user.id, unique_filename, filename, file_type, filepath, file_size)
    return jsonify({'id': media.id, 'filename': filename, 'file_type': file_type, 'url': f'/uploads/{unique_filename}'}), 201

# ========== ROUTE POUR AFFICHER LES FICHIERS UPLOADES ==========
@app.route("/uploads/<filename>")
@login_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ========== SUPPRESSION DE MEDIA ==========
@app.route("/api/media/<int:media_id>", methods=["DELETE"])
@login_required
def delete_media_file(media_id):
    if delete_media(media_id, current_user.id):
        return jsonify({"message": "media deleted"}), 200
    return jsonify({"error": "media not found"}), 404

# ========== ERROR HANDLERS ==========
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "not found", "path": request.path}), 404

@app.errorhandler(500)
def internal_error(e):
    logger.error("500_internal_error", extra={"traceback": traceback.format_exc()})
    return jsonify({"error": "internal server error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)