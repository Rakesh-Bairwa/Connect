import os
import csv
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from project import app, db, bcrypt
from project.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm
from project.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required

scraped_data = []
file = 'linkedinScrapped.csv'
with open(file, 'r') as csvfile:
	csvreader = csv.reader(csvfile)
	fields = next(csvreader)
	for row in csvreader:
		scraped_data.append(row)

default_img = '/static/profile_pics/default_img.jpg'

title_provided = 'Home Page'
@app.route("/")
def home():
	if not current_user.is_authenticated:
		flash('Please Login to make a post :)', 'secondary')
	posts = Post.query.all()
	return render_template('home.html', posts = posts)

@app.route("/meet_us") # render about.html but route name is meet_us
def about():
	return render_template('about.html', title = about, data=scraped_data, len=len(scraped_data), default_img=default_img)

@app.route("/memories")
def memories():
	return render_template('memories.html', title = memories)

@app.route("/register", methods=['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = RegistrationForm()
	if form.validate_on_submit():
		hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
		user = User(username=form.username.data, email=form.email.data, password=hashed_password)
		db.session.add(user)
		db.session.commit()
		flash('Your account has been created! You are now able to log in', 'success')
		return redirect(url_for('login'))
	return render_template('register.html', title = 'Register', form = form)

@app.route("/login", methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('home'))
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user and bcrypt.check_password_hash(user.password, form.password.data):
			login_user(user, remember=form.remember.data)
			next_page = request.args.get('next')
			flash('You have been logged in!', 'success')
			if next_page:
				return redirect(next_page)
			else:
				return redirect(url_for('home'))
		else :
			flash('Login failed :(', 'danger')
	return render_template('login.html', title = 'Login', form = form)

@app.route("/logout")
def logout():
	logout_user()
	return redirect(url_for('home'))

@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
	form = UpdateAccountForm()
	if request.method == 'GET':
		form.username.data = current_user.username
		form.email.data = current_user.email
	if form.validate_on_submit():

		if form.picture.data:
			random_hex = secrets.token_hex(8)
			img, ext = os.path.splitext(form.picture.data.filename)
			file = random_hex + ext
			img_path = os.path.join(app.root_path,'static/profile_pics',file)
			
			output_size = (125, 125)
			i = Image.open(form.picture.data)
			i.thumbnail(output_size)
			i.save(img_path)

			current_user.image_file = file

		current_user.username = form.username.data
		current_user.email = form.email.data
		db.session.commit()
		flash('Your account is updated', 'success')
		return redirect(url_for('account'))
	image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
	return render_template('account.html', title = 'Account', image_file=image_file, form=form)

@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
	form = PostForm()
	photo_path = None # creata a copy of uploaded form image & store in static/profile_pics
	if form.validate_on_submit():
		if form.picture.data:
			random_hex = secrets.token_hex(8)
			img, ext = os.path.splitext(form.picture.data.filename)
			file = random_hex + ext
			photo_path = os.path.join(app.root_path,'static/profile_pics',file)
			
			image = Image.open(form.picture.data)
			image.save(photo_path)

		if photo_path:
			img_loc = url_for('static', filename='profile_pics/' + file)
		else:
			img_loc = None
		post = Post(title=form.title.data, content=form.content.data, author=current_user, img_path=img_loc)

		db.session.add(post)
		db.session.commit()
		flash('Your post has been created!', 'success')
		return redirect(url_for('home'))
	return render_template('create_post.html', title = 'New Post', form=form, legend ='New Post')

@app.route("/post/<int:post_id>")
def post(post_id):
	post = Post.query.get_or_404(post_id)
	return render_template('post.html', title=post.title, post=post)

@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
	post = Post.query.get_or_404(post_id)
	if post.author != current_user:
		abort(403) # forbidden if not author try to update the post
	form = PostForm()
	
	if form.validate_on_submit():
		post.title = form.title.data
		post.content = form.content.data

		photo_path = None

		if form.picture.data:
			random_hex = secrets.token_hex(8)
			img, ext = os.path.splitext(form.picture.data.filename)
			file = random_hex + ext
			photo_path = os.path.join(app.root_path,'static/profile_pics',file)
			
			image = Image.open(form.picture.data)
			image.save(photo_path)

		if photo_path:
			post.img_path = url_for('static', filename='profile_pics/' + file)
		else:
			post.img_path = None

		db.session.commit()
		flash('Your Post is updated!','success')
		return redirect(url_for('post',post_id=post.id))

	elif request.method == 'GET':
		form.title.data = post.title
		form.content.data = post.content

	return render_template('create_post.html', title = 'Update Post', form=form, legend ='Update Post')

@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
	post = Post.query.get_or_404(post_id)
	if post.author != current_user:
		abort(403) # forbidden if not author try to update the post
	
	db.session.delete(post)
	db.session.commit()
	flash('Your Post is deleted successfully!','success')
	return redirect(url_for('home'))
