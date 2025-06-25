import os
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.utils import secure_filename

from app import db
from app.forms import RegisterForm, LoginForm, QuestionForm, AnswerForm, UpdateProfileForm
from app.models import User, Question, Answer, Upvote

main = Blueprint('main', __name__)

# ====================== Home ======================
@main.route('/')
def home():
    questions = Question.query.order_by(Question.created_at.desc()).all()
    return render_template('home.html', questions=questions)

# ====================== Ask a Question ======================
@main.route('/ask', methods=['GET', 'POST'])
@login_required
def ask_question():
    form = QuestionForm()
    if form.validate_on_submit():
        question = Question(
            title=form.title.data,
            body=form.body.data,
            tag=form.tag.data,
            user_id=current_user.id
        )
        db.session.add(question)
        db.session.commit()
        flash('Your question has been posted!', 'success')
        return redirect(url_for('main.view_question', question_id=question.id))
    return render_template('ask.html', form=form)

# ====================== View Question & Answer ======================
@main.route('/question/<int:question_id>', methods=['GET', 'POST'])
def view_question(question_id):
    question = Question.query.get_or_404(question_id)
    form = AnswerForm()

    if form.validate_on_submit() and current_user.is_authenticated:
        answer = Answer(
            body=form.body.data,
            question_id=question.id,
            user_id=current_user.id
        )
        db.session.add(answer)
        db.session.commit()
        flash('Answer submitted!', 'success')
        return redirect(url_for('main.view_question', question_id=question.id))

    return render_template('question.html', question=question, form=form)

# ====================== Register ======================
@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegisterForm()
    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already registered.', 'danger')
            return redirect(url_for('main.register'))
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data  # ⚠️ Hashing should be added
        )
        db.session.add(user)
        db.session.commit()
        flash('Account created! Please login.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', form=form)

# ====================== Login ======================
@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.password == form.password.data:
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('main.home'))
        else:
            flash('Invalid email or password.', 'danger')
    return render_template('login.html', form=form)

# ====================== Logout ======================
@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))

# ====================== Upvote ======================
@main.route('/upvote/<int:answer_id>')
@login_required
def upvote(answer_id):
    answer = Answer.query.get_or_404(answer_id)
    existing_upvote = Upvote.query.filter_by(user_id=current_user.id, answer_id=answer_id).first()
    if not existing_upvote:
        upvote = Upvote(user_id=current_user.id, answer_id=answer_id)
        db.session.add(upvote)
        db.session.commit()
        flash('Upvoted!', 'success')
    else:
        flash('You already upvoted this answer.', 'info')
    return redirect(url_for('main.view_question', question_id=answer.question.id))

# ====================== Profile ======================
@main.route('/profile/<string:username>', methods=['GET', 'POST'])
@login_required
def profile(username):
    user = User.query.filter_by(username=username).first_or_404()
    form = UpdateProfileForm()

    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        if form.photo.data:
            photo_file = secure_filename(form.photo.data.filename)
            photo_path = os.path.join('app', 'static', 'profile_photos', photo_file)
            form.photo.data.save(photo_path)
            user.photo = photo_file
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('main.profile', username=user.username))

    form.username.data = user.username
    form.email.data = user.email

    return render_template('profile.html', user=user, form=form)

# ====================== Search ======================
@main.route('/search')
def search():
    query = request.args.get('q')
    results = []
    if query:
        results = Question.query.filter(Question.title.contains(query)).all()
    return render_template('search_results.html', query=query, results=results)

# ====================== Edit Answer ======================
@main.route('/answer/<int:answer_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_answer(answer_id):
    answer = Answer.query.get_or_404(answer_id)
    if answer.author != current_user:
        flash("You can't edit someone else's answer.", "danger")
        return redirect(url_for('main.view_question', question_id=answer.question.id))

    form = AnswerForm()
    if form.validate_on_submit():
        answer.body = form.body.data
        db.session.commit()
        flash("Answer updated!", "success")
        return redirect(url_for('main.view_question', question_id=answer.question.id))
    
    form.body.data = answer.body  # prefill form with current content
    return render_template('edit_answer.html', form=form, answer=answer)

# ====================== Delete Answer ======================
@main.route('/answer/<int:answer_id>/delete', methods=['POST'])
@login_required
def delete_answer(answer_id):
    answer = Answer.query.get_or_404(answer_id)

    if answer.author != current_user:
        abort(403)


    question_id = answer.question.id

    db.session.delete(answer)
    db.session.commit()

    return redirect(url_for('main.view_question', question_id=question_id))
