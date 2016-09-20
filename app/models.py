from app import db
from hashlib import md5

# This is a direct translation of the association table.
# use the lower level APIs in flask-sqlalchemy to create the table without an associated model.
followers = db.Table('followers',
	db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
	db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

class User(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	nickname = db.Column(db.String(64), index=True, unique=True)
	email = db.Column(db.String(120), index=True, unique=True)
	posts = db.relationship('Post', backref='author', lazy='dynamic')
	about_me = db.Column(db.String(140))
	last_seen = db.Column(db.DateTime)
	followed = db.relationship('User',
							   secondary=followers,
							   primaryjoin=(followers.c.follower_id == id),
							   secondaryjoin=(followers.c.followed_id == id),
							   backref=db.backref('followers', lazy='dynamic'),
							   lazy='dynamic')

	@property
	def is_authenticated(self):
		return True

	@property
	def is_active(self):
		return True
	
	@property
	def is_anonymous(self):
		return False
	
	def get_id(self):
		try:
			return unicode(self.id) # python 2
		except NameError:
			return str(self.id) # python 3
	
	def avatar(self, size):
		return 'http://www.gravatar.com/avatar/%s?d=mm&s=%d' % \
				 (md5(self.email.encode('utf-8')).hexdigest(), size)

	def follow(self, user):
		# When an object is returned, this object has to be added to 
		# the database session and committed.
		if not self.is_following(user):
			self.followed.append(user)
			# return an object when they succeed or None when they fail.
			return self
	
	def unfollow(self, user):
		if self.is_following(user):
			self.followed.remove(user)
			return self
	
	'''
	There are several methods in the query object that trigger the query execution. 
	We've seen that count() runs the query and returns the number of results 
	(throwing the actual results away). 
	We have also used first() to return the first result and throw away the rest, if any. 
	In this test we are using the all() method to get an array with all the results.
	'''
	def is_following(self, user):
		return self.followed.filter(followers.c.followed_id == user.id).count() > 0

	# This method returns a query object, not the results. 
	# This is similar to how relationships with lazy = 'dynamic' work.
	def followed_post(self):
		return Post.query.join(followers, (followers.c.followed_id == Post.user_id))\
						 .filter(followers.c.follower_id == self.id)\
						 .order_by(Post.timestamp.desc())

	# We can use without an instance of the Class.
	@staticmethod
	def make_unique_nickname(nickname):
		if User.query.filter_by(nickname=nickname).first() is None:
			return nickname
		version = 2
		while True:
			new_nickname = nickname + str(version)
			if User.query.filter_by(nickname=new_nickname).first() is None:
				break
			version += 1
		return new_nickname
	
	def __repr__(self):
		return '<User %r>' % (self.nickname)

class Post(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	body = db.Column(db.String(140))
	timestamp = db.Column(db.DateTime)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

	def __repr__(self):
		return '<Post %r>' % (self.body)

