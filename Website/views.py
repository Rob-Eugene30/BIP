from flask import Blueprint, render_template, request, flash, jsonify, session, url_for, redirect, send_from_directory, current_app
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user
from .models import Note, User, Document, Comment, AuditTrail, Announcement
from . import db
import json
import os

views = Blueprint('views', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'png', 'jpg', 'jpeg'}

@views.route('/')
def welcome():
    session.clear() 
    return render_template("welcome.html")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@views.route('/upload', methods=['POST'])
@login_required
def upload_document():
    if not current_user.is_admin:  # Only allow admins
        flash("You are not authorized to upload documents!", "error")
        return redirect(url_for('views.admin_panel'))

    file = request.files.get('file')
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_folder = current_app.config['UPLOAD_FOLDER']

        # Ensure the uploads directory exists
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)

        new_document = Document(title=filename, filename=filename)
        db.session.add(new_document)
        db.session.commit()
        flash("Document uploaded successfully!", "success")
    else:
        flash("Invalid file type!", "error")

    return redirect(url_for('views.admin_panel'))

@views.route('/documents')
@login_required
def documents():
    docs = Document.query.all()
    return render_template('documents.html', documents=docs)

@views.route('/documents/<int:doc_id>')
@login_required
def view_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    comments = Comment.query.filter_by(document_id=doc_id).all()
    return render_template('view_document.html', document=doc, comments=comments, user=current_user)

@views.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@views.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    documents = Document.query.all()
    return render_template("home.html", documents=documents, user=current_user)

@views.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        return render_template("home.html", user=current_user)  # Redirect non-admin users to home page

    users = User.query.all()
    return render_template('/admin_panel.html', users=users, user=current_user)

@views.route('/documents/<int:doc_id>/comment', methods=['POST'])
@login_required
def add_comment(doc_id):
    content = request.form.get('comment_text')  # Ensure this matches the form input name
    if not content:
        flash('Comment text is required.', 'error')
        return redirect(url_for('views.view_document', doc_id=doc_id))  # Fixed `url_for`

    new_comment = Comment(user_id=current_user.id, document_id=doc_id, content=content)
    db.session.add(new_comment)
    db.session.commit()
    return redirect(url_for('views.view_document', doc_id=doc_id))  # Fixed `url_for`

@views.route('/comments/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.user_id != current_user.id:
        flash("You can only delete your own comments.")
        return redirect(url_for('views.view_document', doc_id=comment.document_id))  # Fixed `url_for`

    db.session.delete(comment)
    db.session.commit()
    return redirect(url_for('views.view_document', doc_id=comment.document_id))  # Fixed `url_for`

@views.route('/announcements')
@login_required
def announcements():
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template('announcements.html', announcements=announcements, user=current_user)

@views.route('/add_announcement', methods=['GET', 'POST'])
@login_required
def add_announcement():
    if not current_user.is_admin:  # Only allow admins to add announcements
        flash("You are not authorized to add announcements!", "error")
        return redirect(url_for('views.home'))

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')

        if not title or not content:
            flash('Title and content are required!', 'error')
            return redirect(url_for('views.add_announcement'))

        new_announcement = Announcement(title=title, content=content, user_id=current_user.id)
        db.session.add(new_announcement)
        db.session.commit()
        flash('Announcement added successfully!', 'success')
        return redirect(url_for('views.announcements'))

    return render_template('add_announcement.html', user=current_user)

@views.route('/delete_announcement/<int:announcement_id>', methods=['POST'])
@login_required
def delete_announcement(announcement_id):
    announcement = Announcement.query.get_or_404(announcement_id)

    if announcement.user_id != current_user.id and not current_user.is_admin:
        flash("You can only delete your own announcements!", "error")
        return redirect(url_for('views.announcements'))

    db.session.delete(announcement)
    db.session.commit()
    flash('Announcement deleted successfully!', 'success')
    return redirect(url_for('views.announcements'))