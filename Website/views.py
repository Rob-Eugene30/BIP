from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
from .models import Note, User
from . import db
import json

views = Blueprint('views', __name__)

@views.route('/')
def welcome():
    return render_template("Welcome.html")

@views.route('/home.html', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST': 
        note = request.form.get('note')#Gets the note from the HTML 

        if len(note) < 1:
            flash('Note is too short!', category='error') 
        else:
            new_note = Note(data=note, user_id=current_user.id)  #providing the schema for the note 
            db.session.add(new_note) #adding the note to the database 
            db.session.commit()
            flash('Note added!', category='success')
            
     # Fetch all notes for the logged-in user
    user_notes = Note.query.filter_by(user_id=current_user.id).all()

    return render_template("home.html", user=current_user, notes=user_notes)


@views.route('/delete-note', methods=['POST'])
@login_required
def delete_note():
    note_id = request.json.get('noteId')  # Get the noteId from the request
    note = Note.query.get(note_id)  # Get the note from the database

    if note and note.user_id == current_user.id:  # Ensure the note belongs to the logged-in user
        db.session.delete(note)
        db.session.commit()  # Commit the deletion to the database
        flash('Note deleted successfully!', category='success')
        return jsonify({"message": "Note deleted"}), 200  # Return JSON response
    else:
        flash('You do not have permission to delete this note.', category='error')
        return jsonify({"message": "Failed to delete"}), 403  # Return error response
    
@views.route('/admin')
@login_required
def admin_panel():
    # Check if the current user is an admin
    if not current_user.is_admin:
        return render_template("home.html", user=current_user,)  # Redirect non-admin users to home page


    # Retrieve all users and notes from the database
    users = User.query.all()
    notes = Note.query.all()

    return render_template('/admin_panel.html', users=users, notes=notes, user=current_user)
