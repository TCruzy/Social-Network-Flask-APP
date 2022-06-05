from turtle import pos
from flask import Flask, render_template, request, redirect, url_for, session
from flask_cors import CORS
import sqlite3


conn = sqlite3.connect('soc-network.db',check_same_thread=False)
c = conn.cursor()

c.execute("""CREATE TABLE IF NOT EXISTS user (Username TEXT, Userid INTEGER PRIMARY KEY, password TEXT)""")
conn.commit()

c.execute("""CREATE TABLE IF NOT EXISTS posts 
            (postid INTEGER PRIMARY KEY, 
            post TEXT,
            userid INTEGER,
            post_date default current_timestamp,
            FOREIGN KEY(userid) REFERENCES user(Userid))
            """)
conn.commit()
c.execute("""CREATE TABLE IF NOT EXISTS comments 
            (commentid INTEGER PRIMARY KEY, 
            comment TEXT, postid INTEGER, 
            userid INTEGER, 
            FOREIGN KEY(postid) REFERENCES posts(postid), 
            FOREIGN KEY(userid) REFERENCES user(Userid))""")
conn.commit()
c.execute("""CREATE TABLE IF NOT EXISTS likes(postid INTEGER,
            userid INTEGER,
            FOREIGN KEY(postid) REFERENCES posts(postid), 
            FOREIGN KEY(userid) REFERENCES user(Userid))""")
conn.commit()
c.execute("""CREATE TABLE IF NOT EXISTS followers(userid INTEGER,following_id INTEGER)""")
conn.commit()



app = Flask(__name__)
CORS(app)

app.secret_key = 'santossantos123'

@app.route('/create-post')
def create_post():
    if "username" not in session.keys():
        return redirect(url_for('login'))
    if session["username"] == "admin":
        return render_template('cpost.htm')
    else:
        return render_template('cuserpost.htm')

@app.route('/admin_posts', methods=['GET', 'POST'])
def admin_posts():
    if request.method == 'POST':
        post_content = request.form['post_content']
        userid = request.form['userid']
        c.execute("select * from user where Userid = ?", (userid,))
        if userid.isdigit() and c.fetchone() is not None:
            c.execute("INSERT INTO posts (post, userid) VALUES (?, ?)", (post_content, userid))
            conn.commit()
            return redirect(url_for('posts'))
        else:
            return redirect(url_for('create_post'))
    else:
        if "username" not in session.keys():
            return redirect(url_for('login'))
        posts = []
        c.execute("SELECT * FROM posts")
        for row in c.fetchall():
            liked_by = []
            c.execute("SELECT userid FROM likes WHERE postid = ?", (row[0],))
            for user in c.fetchall():
                try:
                    c.execute("SELECT Username FROM user WHERE Userid = ?", (user[0],))
                    liked_by.append(c.fetchone()[0])
                except:
                    pass
            c.execute("SELECT username FROM user WHERE Userid = ?", (row[2],))
            posts.append({'postid': row[0], 'liked_by': liked_by, 'post': row[1], 'userid': row[2], 'post_date': row[3], 'username': c.fetchone()[0]})
        user = session['username']
        return render_template('posts.htm', posts=posts, user=user)
        # posts = []
        # c.execute("SELECT * FROM posts order by post_date desc")
        # for row in c:
        #     posts.append({'postid': row[0], 'post': row[1], 'userid': row[2], 'post_date': row[3]})
        # return {"all-post": posts}

@app.route('/')
def home():
    if "username" not in session.keys():
        return redirect(url_for('login'))
    elif session["username"] == "admin":
        return redirect(url_for('admin_posts'))
    else:
        return redirect(url_for('posts'))


@app.route('/posts', methods=['GET', 'POST'])
def posts():
    if request.method == 'POST':
        post_content = request.form['post_content']
        c.execute("select userid from user where username = ?", (session['username'],))
        userid = c.fetchone()[0]
        c.execute("INSERT INTO posts (post, userid) VALUES (?, ?)", (post_content, userid))
        conn.commit()
        return redirect(url_for('posts'))
    else:
        global for_friends
        if "username" not in session.keys():
            return redirect(url_for('login'))
        posts = []
        for_friends = {"posted_by": None, "logged_in_user": None}
        if "admin" not in session.values():
            c.execute("SELECT * FROM posts")
            for row in c.fetchall():
                already_friend = 0  
                for_friends["posted_by"] = row[2]
                c.execute("select userid from user where username = ?", (session['username'],))
                for_friends["logged_in_user"] = c.fetchone()[0]
                try:
                    c.execute("select following_id from followers where userid = ?", (for_friends['logged_in_user'],))
                    friend = c.fetchall()
                    for friends in friend:
                        if friends[0] == for_friends["posted_by"]:
                            already_friend = 1
                except:
                    pass         
                c.execute("select userid from user where username = ?", (session['username'],))
                userid = c.fetchone()[0]
                liked_by = []
                c.execute("SELECT userid FROM likes WHERE postid = ?", (row[0],))
                for user in c.fetchall():
                    try:
                        c.execute("SELECT Username FROM user WHERE Userid = ?", (user[0],))
                        liked_by.append(c.fetchone()[0])
                    except:
                        pass
                liked_me = False
                # print(session['username'] in liked_by)
                if session["username"] in liked_by:
                    liked_me = True
                c.execute("SELECT username FROM user WHERE Userid = ?", (row[2],))
                posts.append({'postid': row[0],'liked_me': liked_me, 'liked_by': liked_by, 'post': row[1], 'userid': row[2], 'post_date': row[3], 'username': c.fetchone()[0],'already_friend': already_friend}) 
            if "admin" not in session.values():
                user = session['username']
                return render_template('posts.htm', posts=posts, user=user)
            
            return render_template('posts.htm', posts=posts, user=session['username'])
        else:
            return redirect(url_for('admin_posts'))



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if 'admin' in session.values():
            return redirect(url_for('admin_posts'))
        elif 'username' in session.keys():
            return redirect(url_for('posts'))
        return render_template('login.htm')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == "admin" and password == "admin":
            session['username'] = username
            return redirect(url_for('admin_posts'))
        try:
            c.execute("SELECT username FROM user WHERE Username = ? AND password = ?", (username, password))
            username = c.fetchone()[0]
            session['username'] = username
            # print(username,"/login post")
            return redirect(url_for('posts'))
        except:
            return render_template('login.htm')
        
        
     

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.htm')
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        c.execute("INSERT INTO user (Username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        return redirect(url_for('login')) 

@app.route('/like-post', methods=['POST'])
def like_post():
    if session['username'] == "admin":
        postid = request.form['postid']
        userid = request.form['userid']
        like_status = request.form['like_status']
        liked = 0
        c.execute("""select * from likes""")
        for like in c.fetchall():
            if int(postid) == like[0] and int(userid) == like[1]:
                liked = True
        if not liked:        
            c.execute("INSERT INTO likes (postid, userid) VALUES (?, ?)", (postid, userid))
            conn.commit()
            return redirect(url_for('posts'))
        else:
            c.execute("DELETE FROM likes WHERE postid = ? and userid = ?", (postid, userid))
            conn.commit()
            return redirect(url_for('posts'))
    else:
        c.execute("SELECT userid FROM user WHERE Username = ?", (session['username'],))
        like_status = request.form['like_status']
        userid = c.fetchone()[0]
        postid = request.form['postid']
        if like_status == "like":
            c.execute("INSERT INTO likes (postid, userid) VALUES (?, ?)", (postid, userid))
            conn.commit()
            return redirect(url_for('posts'))
        if like_status == "unlike":
            c.execute("DELETE FROM likes WHERE postid = ? and userid = ?", (postid, userid))
            conn.commit()
            return redirect(url_for('posts'))
    
@app.route('/posts/<name>', methods=['GET', 'POST'])
def posts_name(name):
    if request.method == 'POST':
        if session['username'] == "admin":
            postid = request.form['postid']
            userid = request.form['userid']
            like_status = request.form['like_status']
            liked = 0
            c.execute("""select * from likes""")
            for like in c.fetchall():
                if int(postid) == like[0] and int(userid) == like[1]:
                    liked = True
            if not liked:        
                c.execute("INSERT INTO likes (postid, userid) VALUES (?, ?)", (postid, userid))
                conn.commit()
                return redirect(url_for('posts_name', name=name))
            else:
                c.execute("DELETE FROM likes WHERE postid = ? and userid = ?", (postid, userid))
                conn.commit()
                return redirect(url_for('posts_name', name=name))
        else:
            like_status = request.form['like_status']
            c.execute("SELECT userid FROM user WHERE Username = ?", (session['username'],))
            userid = c.fetchone()[0]
            postid = request.form['postid']
            if like_status == "like":
                c.execute("INSERT INTO likes (postid, userid) VALUES (?, ?)", (postid, userid))
                conn.commit()
                return redirect(url_for('posts_name', name=name))
            if like_status == "unlike":
                c.execute("DELETE FROM likes WHERE postid = ? and userid = ?", (postid, userid))
                conn.commit()
                return redirect(url_for('posts_name', name=name))
    # print(name)
    if "username" not in session.keys():
        return redirect(url_for('login'))
    posts = []
    c.execute("SELECT userid FROM user WHERE username = ?", (name,))
    userid = c.fetchone()[0]
    c.execute("SELECT * FROM posts where userid = ?", (userid,))
    for row in c.fetchall():
        liked_by = []
        c.execute("SELECT userid FROM likes WHERE postid = ?", (row[0],))
        for user in c.fetchall():
            try:
                c.execute("SELECT Username FROM user WHERE Userid = ?", (user[0],))
                liked_by.append(c.fetchone()[0])
            except:
                pass
        liked_me = False
        # (session['username'] in liked_by)
        if session["username"] in liked_by:
            liked_me = True
        c.execute("SELECT username FROM user WHERE Userid = ?", (row[2],))
        posts.append({'postid': row[0],'liked_me': liked_me, 'liked_by': liked_by, 'post': row[1], 'userid': row[2], 'post_date': row[3], 'username': c.fetchone()[0]}) 
    if "admin" not in session.values():
        # print("shemovida")
        user = session['username']
        followers = 0
        c.execute("select following_id from followers where userid = ?", (userid,))
        for row in c.fetchall():
            followers += 1
        return render_template('userposts.htm', posts=posts, user=user, followers=followers)
    followers = 0
    c.execute("select following_id from followers where userid = ?", (userid,))
    for row in c.fetchall():
        followers += 1
    return render_template('userposts.htm', posts=posts, user=session['username'], followers=followers)


        
@app.route('/add-friend', methods=['POST'])
def add_friend():
    global puserid, luserid
    add = request.form['add']
    checkuserid = request.form['checkuserid']
    print(add, checkuserid)
    if add == "+":
        print("++")
        luserid = for_friends['logged_in_user']
        c.execute("insert into followers (userid, following_id) values (?, ?)", (luserid, checkuserid))
        conn.commit()
        for_friends['posted_by'] = None
        for_friends['logged_in_user'] = None
        return redirect(url_for('posts'))
    if add == "-":
        print("--")
 
        luserid = for_friends['logged_in_user'] 
        c.execute("DELETE from followers WHERE userid = ? AND following_id = ?", (luserid, checkuserid))
        conn.commit()
        for_friends['posted_by'] = None
        for_friends['logged_in_user'] = None
        return redirect(url_for('posts'))
        
    
    
@app.route('/my-posts')
def my_posts():
    if "username" not in session.keys():
        return redirect(url_for('login'))
    posts = []
    c.execute("SELECT userid FROM user WHERE username = ?", (session['username'],))
    userid = c.fetchone()[0]
    c.execute("SELECT * FROM posts where userid = ?", (userid,))
    for row in c.fetchall():
        liked_by = []
        c.execute("SELECT userid FROM likes WHERE postid = ?", (row[0],))
        for user in c.fetchall():
            try:
                c.execute("SELECT Username FROM user WHERE Userid = ?", (user[0],))
                liked_by.append(c.fetchone()[0])
            except:
                pass
        liked_me = False
        # (session['username'] in liked_by)
        if session["username"] in liked_by:
            liked_me = True
        c.execute("SELECT username FROM user WHERE Userid = ?", (row[2],))
        posts.append({'postid': row[0],'liked_me': liked_me, 'liked_by': liked_by, 'post': row[1], 'userid': row[2], 'post_date': row[3], 'username': c.fetchone()[0]}) 
    followers = 0
    c.execute("select following_id from followers where userid = ?", (userid,))
    for row in c.fetchall():
        followers += 1
    return render_template('userposts.htm', posts=posts, user=session['username'], followers=followers)
        

@app.route('/users')
def users():
    if "username" not in session.keys():
        return redirect(url_for('login'))
    elif "admin" not in session.values():
        return redirect(url_for('posts'))
    users = []
    for_name = -1
    c.execute("SELECT username, userid FROM user")
    users_ex = c.fetchall()
    for row in users_ex:
        for_name += 1
        c.execute("select postid from posts where userid = ?", (row[1],))
        posts_amount = len(c.fetchall())
        if posts_amount is None:
            posts_amount = 0
        c.execute("select following_id from followers where userid = ?", (row[1],))
        followers_amount = len(c.fetchall())
        if followers_amount is None:
            followers_amount = 0
        c.execute("select postid from likes where userid = ?", (row[1],))
        liked_amount = len(c.fetchall())
        if liked_amount is None:
            liked_amount = 0
        c.execute("select postid from posts where userid = ?", (row[1],))
        postidd = c.fetchall()
        likes_amount = 0
        if postidd is not None:
            for row in postidd:
                c.execute("select userid from likes where postid = ?" , (row[0],))
                likes_amount += len(c.fetchall())
        else:
            likes_amount = 0
        users.append({'name': users_ex[for_name][0], 'posts': posts_amount, 'followers': followers_amount, 'liked': liked_amount, 'likes': likes_amount})
        
        
    return render_template('users.htm', users=users)



# @app.route('/comment-post', methods=['POST'])
# def comment_post():
#     comment_content = request.args.get('comment_content')
#     postid = request.args.get('postid')
#     userid = request.args.get('userid')
#     c.execute("INSERT INTO comments (comment, postid, userid) VALUES (?, ?, ?)", (comment_content, postid, userid))
#     conn.commit()
#     comment = []
#     c.execute("SELECT * FROM comments WHERE postid = ?", (postid,))
#     for row in c:
#         comment.append({'commentid': row[0], 'comment': row[1], 'postid': row[2], 'userid': row[3]})
#     return {'comment': comment}



if __name__ == "__main__":
    app.run(debug=True)