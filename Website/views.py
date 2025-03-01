from flask import Blueprint, render_template, request, flash, jsonify, session, url_for, redirect, send_file, current_app, send_from_directory
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user
from .models import Note, User, Document, Comment, AuditTrail, Announcement, ForumPost, ForumComment
from . import db
import json
import io
from datetime import datetime

views = Blueprint('views', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'png', 'jpg', 'jpeg'}

# Logging for audit trail function:
def log_action(user_email, action):
    audit_entry = AuditTrail(user_email=user_email, action=action)
    db.session.add(audit_entry)
    db.session.commit()

@views.route('/')
def welcome():
    session.clear() 
    return render_template("welcome.html")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@views.route('/upload', methods=['POST'])
@login_required
def upload_document():
    if not current_user.is_admin:  # Only admins can upload
        flash("You are not authorized to upload documents!", "error")
        return redirect(url_for('views.admin_panel'))

    file = request.files.get('file')
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_data = file.read()  # Read file content as binary

        # Store file metadata in the database
        new_document = Document(title=filename, filename=filename, data=file_data)
        db.session.add(new_document)
        db.session.commit()
        
        log_action(current_user.email, "Uploaded a document")
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

@views.route('/documents/<int:doc_id>/view')
@login_required
def get_document(doc_id):
    document = Document.query.get_or_404(doc_id)
    
    return send_file(
        io.BytesIO(document.data),
        mimetype="application/pdf",  # Change this if you store other file types
        as_attachment=False,
        download_name=document.filename
    )



@views.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    documents = Document.query.all()
    return render_template("home.html", documents=documents, user=current_user)

@views.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_panel():
    if not current_user.is_admin:
        return render_template("home.html", user=current_user)  # Redirect non-admin users to home page

    users = User.query.all()
    return render_template('/admin_panel.html', users=users, user=current_user)

@views.route('/documents/<int:doc_id>/comment', methods=['POST'])
@login_required
def add_comment(doc_id):
    content = request.form.get('comment_text')
    if not content:
        flash('Comment text is required.', 'error')
        return redirect(url_for('views.view_document', doc_id=doc_id))

    new_comment = Comment(user_id=current_user.id, document_id=doc_id, content=content)
    db.session.add(new_comment)
    db.session.commit()
    return redirect(url_for('views.view_document', doc_id=doc_id))

@views.route('/comments/<int:comment_id>/delete', methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.user_id != current_user.id:
        flash("You can only delete your own comments.")
        return redirect(url_for('views.view_document', doc_id=comment.document_id))

    db.session.delete(comment)
    db.session.commit()
    return redirect(url_for('views.view_document', doc_id=comment.document_id))


#Audit Trail:
@views.route('/admin/audit-report')
@login_required
def audit_report():
    if not current_user.is_admin:
        flash("Access denied!", "error")
        return redirect(url_for('views.home'))
    
    logs = AuditTrail.query.order_by(AuditTrail.timestamp.desc()).all()
    return render_template('audit_report.html', audit_logs=logs, user=current_user)

#Download Document:
@views.route('/documents/<int:doc_id>/download')
@login_required
def download_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    return send_file(
        io.BytesIO(doc.data),  
        mimetype="application/octet-stream",
        as_attachment=True,
        download_name=doc.filename  # Uses stored filename
    )


#Announcements:
@views.route('/announcements')
@login_required
def announcements():
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template('announcements.html', announcements=announcements, user=current_user)

@views.route('/add_announcement', methods=['POST'])
@login_required
def add_announcement():
    if not current_user.is_admin:  # Only allow admins to add announcements
        flash("You are not authorized to add announcements!", "error")
        return redirect(url_for('views.home'))

    # if request.method == 'POST':
    title = request.form.get('title')
    content = request.form.get('content')

    if not title or not content:
        flash('Title and content are required!', 'error')
        return redirect(url_for('views.admin_panel'))

    new_announcement = Announcement(title=title, content=content, user_id=current_user.id)
    db.session.add(new_announcement)
    db.session.commit()
    log_action(current_user.email, f"Added announcement: '{title}'")
    flash('Announcement added successfully!', 'success')
    return redirect(url_for('views.admin_panel'))



@views.route('/delete_announcement/<int:announcement_id>', methods=['POST'])
@login_required
def delete_announcement(announcement_id):
    announcement = Announcement.query.get_or_404(announcement_id)

    if announcement.user_id != current_user.id and not current_user.is_admin:
        flash("You can only delete your own announcements!", "error")
        return redirect(url_for('views.announcements'))

    db.session.delete(announcement)
    db.session.log_action(current_user.email, f"Deleted announcement: '{announcement.title}'")
    db.session.commit()
    flash('Announcement deleted successfully!', 'success')
    return redirect(url_for('views.announcements'))

#Forums:
@views.route('/forums')
@login_required
def forums():
    posts = ForumPost.query.order_by(ForumPost.created_at.desc()).all()
    return render_template("forums.html", posts=posts, user=current_user)

@views.route('/add_forum_post', methods=['POST'])
@login_required
def add_forum_post():
    title = request.form.get('title')
    content = request.form.get('content')

    if not title or not content:
        flash("Title and content are required!", "error")
        return redirect(url_for('views.forums'))

    new_post = ForumPost(title=title, content=content, user_id=current_user.id, created_at=datetime.utcnow())
    db.session.add(new_post)
    db.session.commit()

    log_action(current_user.email, f"Created a new forum discussion: '{title}'")
    flash("Discussion posted successfully!", "success")
    return redirect(url_for('views.forums'))

@views.route('/forums/<int:post_id>', methods=['GET', 'POST'])
@login_required
def forum_post(post_id):
    post = ForumPost.query.get_or_404(post_id)
    comments = ForumComment.query.filter_by(post_id=post.id).order_by(ForumComment.created_at).all()

    if request.method == 'POST':
        content = request.form.get('content')
        if not content:
            flash("Comment cannot be empty!", "error")
        else:
            new_comment = ForumComment(content=content, user_id=current_user.id, post_id=post.id)
            db.session.add(new_comment)
            db.session.commit()
            log_action(current_user.email, f"Commented on forum post: '{post.title}'")
            flash("Comment added!", "success")
            return redirect(url_for('views.forum_post', post_id=post.id))

    return render_template("forum_post.html", post=post, comments=comments, user=current_user)