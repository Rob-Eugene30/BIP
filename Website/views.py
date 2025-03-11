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
def log_action(user_email, action, link=None):
    audit_entry = AuditTrail(user_email=user_email, action=action, link=link)
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
def upload():
    if not current_user.is_verified or (current_user.position is None and not current_user.is_admin):
        flash("Access denied! Only admins and verified officials can upload documents.", "error")
        return redirect(url_for('views.home'))

    if 'file' not in request.files:
        flash('No file part', 'error')
        return redirect(request.referrer)

    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(request.referrer)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        new_document = Document(title=filename, filename=filename, data=file.read())
        db.session.add(new_document)
        db.session.commit()
        
        document_link = url_for('views.documents', document_id=new_document.id, _external=True)
        log_action(current_user.email, f"Uploaded a document: {file.filename}", document_link)
        flash('Document uploaded successfully!', 'success')
    else:
        flash('Invalid file format!', 'error')

    return redirect(request.referrer)


@views.route('/documents')
@login_required
def documents():
    docs = Document.query.all()
    return render_template('Documents.html', documents=docs, user=current_user)

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
        mimetype="application/pdf",  # Change this to store other file types
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

@views.route('/announcement/<int:announcement_id>')
@login_required
def view_announcement(announcement_id):
    announcement = Announcement.query.get_or_404(announcement_id)  
    return render_template('view_announcement.html', announcement=announcement, user=current_user)

@views.route('/add_announcement', methods=['POST'])
@login_required
def add_announcement():
    if not current_user.is_verified or (current_user.position is None and not current_user.is_admin):
        flash("Access denied!", "error")
        return redirect(url_for('views.home'))

    title = request.form.get('title')
    content = request.form.get('content')

    if title and content:
        new_announcement = Announcement(title=title, content=content, user_id=current_user.id)
        db.session.add(new_announcement)
        db.session.commit()

        # ✅ Log action with a clickable link
        announcement_link = url_for('views.view_announcement', announcement_id=new_announcement.id, _external=True)
        log_action(current_user.email, f"Posted a new announcement: {title}", announcement_link)

        flash('Announcement posted successfully!', 'success')

    return redirect(url_for('views.announcements'))


@views.route('/FAQ')
@login_required
def FAQ():
    return render_template("FAQ.html", user=current_user)

@views.route('/delete_announcement/<int:announcement_id>', methods=['POST'])
@login_required
def delete_announcement(announcement_id):
    announcement = Announcement.query.get_or_404(announcement_id)

    if announcement.user_id != current_user.id and not current_user.is_admin:
        flash("You can only delete your own announcements!", "error")
        return redirect(url_for('views.announcements'))

    db.session.delete(announcement)
    log_action(current_user.email, f"Deleted announcement: '{announcement.title}'")
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

    forum_link = url_for('views.forum_post', post_id=new_post.id, _external=True)
    log_action(current_user.email, f"Created a new forum discussion: '{title}'", forum_link)
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

#Verification of officials
@views.route('/admin/verify_officials', methods=['GET', 'POST'])
@login_required
def verify_officials():
    if not current_user.is_admin:
        flash("Access denied!", "error")
        return redirect(url_for('views.home'))
    
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        user = User.query.get(user_id)
        if user:
            user.is_verified = True
            db.session.commit()
            log_action(current_user.email, f"Verified official: {user.email}")

            flash(f"User {user.email} has been verified!", "success")
        else:
            flash("User not found!", "error")
    
    pending_officials = User.query.filter(User.is_verified == False, User.position.isnot(None)).all()
    return render_template('verify_officials.html', pending_officials=pending_officials, user=current_user)


#official_Panel
@views.route('/official_panel')
@login_required
def official_panel():
    if not current_user.is_verified or current_user.position is None:
        flash("Access denied! Only verified officials can access this page.", "error")
        return redirect(url_for('views.home'))

    return render_template("official_panel.html", user=current_user)
