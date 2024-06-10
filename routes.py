from flask import Flask, render_template, request, session, redirect, url_for, flash
from datetime import datetime
from app import app,db
from models import User, Playlist, Song, Album
from sqlalchemy import func



@app.route('/')
def welcome():
    if 'user_id' not in session:
        return render_template('welcome.html')
    
    user = User.query.get(session['user_id'])
    if user.is_admin:
        return render_template('admin_dashboard.html',user=user )
    
    return render_template('user_dashboard.html', user=user)

#__________________________________________________________________________________________________________________


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and user.password == password and user.is_admin:
            session['user_id'] = user.id

            flash('You have successfully logged in as admin.', 'success')
            return redirect(url_for('admin_dashboard')) 

        flash('Invalid admin credentials. Please try again.')

    return render_template('admin_login.html')


@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session :
        flash('Please Login first')
        return redirect(url_for('admin_login'))

    user=User.query.get(session['user_id'])
    if not user.is_admin:
        flash('Unauthorized access')
        return redirect(url_for('admin_login'))
    
    creators = User.query.filter_by(is_creator=True).all()

    total_songs = Song.query.count()
    total_albums = Album.query.count()
    total_users = User.query.filter_by(is_admin=False).count()
    total_creators = User.query.filter_by(is_creator=True).count()
    total_genres = Album.query.distinct(Album.genre).count()
    if total_songs > 0:
        avg_rating = round((db.session.query(func.avg(Song.rating)).scalar()),2)
    else:
        avg_rating = 0  


    return render_template('admin_dashboard.html',user=user, creators=creators,total_albums=total_albums,total_songs=total_songs,
                           total_users=total_users,total_creators=total_creators,total_genres=total_genres,avg_rating=avg_rating )

@app.route('/blacklist_creator/<int:user_id>')
def blacklist_creator(user_id):
    if 'user_id' not in session:
        flash('Please log in first.')
        return redirect(url_for('admin_login'))

    user = User.query.get(session['user_id'])
    if not user.is_admin:
        flash('Unauthorized access.')
        return redirect(url_for('admin_login'))

    creator = User.query.get(user_id)
    if not creator:
        flash('Creator not found.')
        return redirect(url_for('admin_dashboard'))

    # Toggle blacklist status
    creator.is_blacklisted = not creator.is_blacklisted
    db.session.commit()

    flash('User blacklist status has been updated.')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin_tracks')
def admin_tracks():
    if 'user_id' not in session:
        flash('Please log in first.')
        return redirect(url_for('admin_login'))

    user = User.query.get(session['user_id'])
    if not user.is_admin:
        flash('Unauthorized access.')
        return redirect(url_for('admin_login'))

    songs = Song.query.all()  
    query = request.args.get('query')
    category = request.args.get('category')

    if not query or not category: 
        return render_template('admin_tracks.html', songs=songs,user=user)
    
    if category == 'songs':
        songs = Song.query.filter(Song.title.ilike('%' + query + '%')).all()
        return render_template('admin_tracks.html', songs=songs,user=user)
    elif category == 'genre':
        return render_template('admin_tracks.html', songs=songs,user=user, genre=query)
    elif category == 'rating':
        try:
            rating = int(query)
            return render_template('admin_tracks.html', songs=songs,user=user, rating=rating)
        except ValueError:
            flash('Please enter a valid rating (1-10)')
            return redirect(url_for('admin_tracks'))
    

    return render_template('admin_tracks.html', songs=songs,user=user)



@app.route('/admin_albums')
def admin_albums():
    if 'user_id' not in session:
        flash('Please log in first.')
        return redirect(url_for('admin_login'))

    user = User.query.get(session['user_id'])
    if not user.is_admin:
        flash('Unauthorized access.')
        return redirect(url_for('admin_login'))

    albums = Album.query.all()  
    query = request.args.get('query')
    category = request.args.get('category')

    if not query or not category: 
        return render_template('admin_albums.html', albums=albums,user=user)
    
    if category == 'albums':
        albums = Album.query.filter(Album.name.ilike('%' + query + '%')).all()
        return render_template('admin_albums.html', albums=albums,user=user)
    elif category == 'genre':
        return render_template('admin_albums.html', albums=albums,user=user, genre=query)
    elif category == 'artist':
        return render_template('admin_albums.html', albums=albums,user=user, artist=query)
        

    return render_template('admin_albums.html', albums=albums,user=user)



#_________________________________________________________________________________________________________________


@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check if any field is empty
        if not username or not password :
            flash('Please fill all the fields.')
            return redirect(url_for('user_login'))

        user = User.query.filter_by(username=username, password=password).first()

        if user:
            if user.is_blacklisted:
                flash('Sorry, you are blacklisted and cannot login.')
                return redirect(url_for('user_login'))
            
            elif user.is_admin:
                flash('Invalid username or password.')
                return redirect(url_for('user_login'))

            
            session['user_id'] = user.id
            return redirect(url_for('user_dashboard')) 

            
        # If the user is not found or authentication fails, show an error message
        flash('Invalid username or password. Please try again.')
        return redirect(url_for('user_login'))  # Redirect back to login page with an error message

    return render_template('user_login.html')

@app.route('/user_register', methods=['GET', 'POST'])
def user_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        name = request.form['name']

        # Check if any field is empty
        if not username or not password or not name:
            flash('Please fill all the fields.')
            return redirect(url_for('user_register'))

        # Check if the username is already taken
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose another one.')
            return redirect(url_for('user_register'))

        # Create a new user and add it to the database
        user = User(username=username, password=password, name=name)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('user_login'))
    
    return render_template('user_register.html')



@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' not in session:
        flash('Please Login first')
        return redirect(url_for('user_login'))
    
    
    user=User.query.get(session['user_id'])
    all_playlists = user.playlists
    all_songs = Song.query.all()
    query = request.args.get('query')
    category = request.args.get('category')

    if not query or not category: 
        return render_template('user_dashboard.html', user=user, all_playlists= all_playlists, all_songs=all_songs)
    
    if category == 'songs':
        songs = Song.query.filter(Song.title.ilike('%' + query + '%')).all()
        return render_template('user_dashboard.html',user=user,all_playlists= all_playlists, all_songs=songs)
    elif category == 'albums':
        return render_template('user_dashboard.html', user=user, all_playlists= all_playlists, all_songs=all_songs, album=query)
    elif category == 'genre':
        return render_template('user_dashboard.html', user=user, all_playlists= all_playlists, all_songs=all_songs, genre=query)
    elif category == 'rating':
        try:
            rating = int(query)
            return render_template('user_dashboard.html', user=user, all_playlists=all_playlists, all_songs=all_songs, rating=rating)
        except ValueError:
            flash('Please enter a valid rating (1-10)')
            return redirect(url_for('user_dashboard'))
    elif category == 'artist':
        return render_template('user_dashboard.html', user=user, all_playlists= all_playlists, all_songs=all_songs, artist=query)

    return render_template('user_dashboard.html', user=user, all_songs=all_songs, all_playlists= all_playlists)



@app.route('/user_profile', methods=['GET', 'POST'])
def user_profile():
    if 'user_id' not in session:
        flash('Please Login first')
        return redirect(url_for('user_login'))
    
    if request.method == 'POST':
        user=User.query.get(session['user_id'])
        username = request.form.get('username')
        name = request.form.get('name')
        oldpassword =  request.form.get('oldpassword')
        newpassword = request.form.get('password')
        if username =='' or name== '' or oldpassword==''or newpassword=='':
            flash('No field can be empty')
            return redirect(url_for('user_profile'))
        if User.query.filter_by(username = username).first() and user.username != username:
            flash('username already exists, choose another')
            return redirect(url_for('user_profile'))
        if user.password != oldpassword:
            flash('Incorrect password')
            return redirect(url_for('user_profile'))
        user.name = name
        user.username = username
        user.password = newpassword
        db.session.commit()
        flash('Profile has been updated successfully')
        return redirect(url_for('user_profile'))
    
    return render_template('user_profile.html', user=User.query.get(session['user_id']))

#______________________________________________________________________________________________________________________

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('welcome'))

@app.route('/creator_dashboard')
def creator_dashboard():
    if 'user_id' not in session:
        flash('Please Login first')
        return redirect(url_for('user_login'))
    
    user=User.query.get(session['user_id'])
    
    if len(user.albums)>0 :        
        total_songs = sum(len(album.songs) for album in user.albums)
        if total_songs>0:
            total_rating=0
            for album in user.albums:
                for song in album.songs:
                    total_rating+= song.rating
            avg_rating= total_rating/total_songs

            total_albums = len(user.albums)
            return render_template('creator_dashboard.html', user=user, total_songs=total_songs, avg_rating=avg_rating, total_albums=total_albums)

    return render_template('creator_dashboard.html', user=user)



@app.route('/creator/register', methods=['GET','POST'])
def creator_register():
    
    user = User.query.get(session['user_id'])

    # Update the 'is_creator' column to True
    if user:
        user.is_creator = True
        db.session.commit()
        flash('You have successfully registered as a creator!')
    else:
        flash('User not found.')

    return redirect(url_for('creator_dashboard'))

@app.route('/add_album', methods=['GET','POST'])
def add_album():
    if 'user_id' not in session:
        flash('Please Login first')
        return redirect(url_for('user_login'))
    
    user=User.query.get(session['user_id'])
    if not user.is_creator:
        flash('You are not a creator')
        return redirect(url_for('user_dashboard'))
    
    if request.method == 'POST':
        user=User.query.get(session['user_id'])
        album_name = request.form['name']
        album_genre = request.form['genre']
        album_artist = request.form['artist']

        # Create a new Album object with the received data and associate it with the user
        new_album = Album(name=album_name, genre=album_genre, artist=album_artist, creator=user)

        # Add the new album to the database session and commit changes
        db.session.add(new_album)
        db.session.commit()

        return redirect(url_for('creator_dashboard'))

    return render_template('add_album.html', user=User.query.get(session['user_id']))


@app.route('/add_song/<int:album_id>', methods=['GET','POST'])
def add_song(album_id):
    if 'user_id' not in session:
        flash('Please Login first')
        return redirect(url_for('user_login'))
    
    user=User.query.get(session['user_id'])
    if not user.is_creator:
        flash('You are not a creator')
        return redirect(url_for('user_dashboard'))
    
    if request.method == 'POST':
        title = request.form['title']
        lyrics = request.form['lyrics']
        duration = int(request.form['duration'])
        rating = int(request.form['rating'])

        if not (1 <= rating <= 10):
            flash('Rating should be between 1 and 10 !')
            return render_template('add_song.html')
        

        date_created = datetime.now()

        album = Album.query.get(album_id)

        if album:
            new_song = Song(
                title=title,
                lyrics=lyrics,
                duration=duration,
                date_created=date_created,
                rating=rating,
                album=album
            )

            db.session.add(new_song)
            db.session.commit()

            return redirect(url_for('creator_dashboard'))  

    return render_template('add_song.html')


@app.route('/edit_album/<int:album_id>', methods=['GET', 'POST'])
def edit_album(album_id):
    album = Album.query.get(album_id)
    if 'user_id' not in session:
        flash('Please Login first')
        return redirect(url_for('user_login'))
    
    user=User.query.get(session['user_id'])
    if (not user.is_creator) or (user != album.creator):
        flash('You are not creator')
        return redirect(url_for('user_dashboard'))
    
    if album:
        if request.method == 'POST':
            name = request.form['name']
            genre = request.form['genre']
            artist = request.form['artist']
            if name== '' or genre==''or artist=='':
                flash('No field can be empty')
                return render_template('edit_album.html', album=album, user=user)
            
            album.name=name
            album.genre=genre
            album.artist = artist

            db.session.commit()
            flash('Changes have been saved successfully!')
            return redirect(url_for('creator_dashboard'))

        return render_template('edit_album.html', album=album, user=user)
    else:         
        return redirect(url_for('creator_dashboard'))


@app.route('/delete_album/<int:album_id>')
def delete_album(album_id):
    
    if 'user_id' not in session:
        flash('Please Login first')
        return redirect(url_for('user_login'))
    
    album = Album.query.get(album_id)
    user=User.query.get(session['user_id'])

    if user.is_admin or (user.is_creator and user == album.creator):        
        if album:
            songs = Song.query.filter_by(album=album).all()
            for song in songs:
                db.session.delete(song)

            db.session.delete(album)
            db.session.commit()
            flash('Album deleted successfully')
            if user.is_admin:
                return redirect(url_for('admin_albums'))
        return redirect(url_for('creator_dashboard'))
    else:
        flash('Permission denied. You are not authorized to delete this album!')
        return redirect(url_for('user_dashboard'))



@app.route('/delete_song/<int:song_id>')
def delete_song(song_id):
    if 'user_id' not in session:
        flash('Please Login first')
        return redirect(url_for('user_login'))
    
    user = User.query.get(session['user_id'])
    song = Song.query.get(song_id)

    if not song:
        flash('Song not found')
        return redirect(url_for('creator_dashboard'))

    # Check if the user is an admin or the creator of the song's album
    if user.is_admin or (user.is_creator and user == song.album.creator):
        db.session.delete(song)
        db.session.commit()
        flash('Song deleted successfully')
        if user.is_admin:
            return redirect(url_for('admin_tracks'))
        return redirect(url_for('creator_dashboard'))        
    else:
        flash('Permission denied. You are not authorized to delete this song.')
        return redirect(url_for('user_dashboard'))




@app.route('/read_lyrics/<int:song_id>', methods=['GET', 'POST'])
def read_lyrics(song_id):
    if 'user_id' not in session:
        flash('Please Login first')
        return redirect(url_for('user_login'))
    
    user=User.query.get(session['user_id'])
    song = Song.query.get(song_id)

    if song:
        if request.method == 'POST':
            new_rating = request.form['rating']
            if new_rating and new_rating.isdigit():
                new_rating = int(new_rating)
                if 1 <= new_rating <= 10:
                    if song.rating:
                        current_rating = song.rating
                        updated_rating = (current_rating + new_rating) / 2
                        song.rating = int(updated_rating)
                    else:
                        song.rating = new_rating

                    db.session.commit()
                    flash('Thanks for rating this song')

        return render_template('read_lyrics.html', song=song,user=user)
    else:
        return redirect(url_for('creator_dashboard'))
    

@app.route('/edit_song/<int:song_id>', methods=['GET', 'POST'])
def edit_song(song_id):
    song = Song.query.get(song_id)
    if 'user_id' not in session:
        flash('Please Login first')
        return redirect(url_for('user_login'))
    
    user=User.query.get(session['user_id'])
    if (not user.is_creator) or (user != song.album.creator):
        flash('You are not creator')
        return redirect(url_for('user_dashboard'))
    
    if song:
        if request.method == 'POST':
            title = request.form['title']
            lyrics = request.form['lyrics']
            duration = int(request.form['duration'])
            rating = int(request.form['rating'])

            if title== '' or lyrics==''or duration=='' or rating=='':                    
                flash('No field can be empty')
                return render_template('edit_song.html', song=song, user=user)

            if not (1 <= rating <= 10):
                flash('Rating should be between 1 and 10 !')
                return render_template('edit_song.html', song=song, user=user)
            
            
            
            song.title=title
            song.lyrics=lyrics
            song.duration=duration
            song.rating=rating

            db.session.commit()
            flash('Changes have been saved successfully!')
            return redirect(url_for('creator_dashboard'))

        return render_template('edit_song.html', song=song, user=user)
    else:         
        return redirect(url_for('creator_dashboard'))

#_____________________________________________________________________________________________________

@app.route('/create_playlist', methods=['GET', 'POST'])
def create_playlist():
    if 'user_id' not in session:
        flash('Please Login first')
        return redirect(url_for('user_login'))
    
    user = user=User.query.get(session['user_id'])

    if request.method == 'POST':
        playlist_name = request.form.get('name')
        selected_songs = request.form.getlist('selected_songs')

        
        user = User.query.get(session['user_id'])
        if user:
            playlist = Playlist(name=playlist_name, playlist_creator=user)
            db.session.add(playlist)
            db.session.commit()

            # Add selected songs to the playlist
            for song_id in selected_songs:
                song = Song.query.get(song_id)
                if song:
                    playlist.songs.append(song)

            db.session.commit()

            flash('Playlist created successfully!')
            return redirect(url_for('view_playlist', playlist_id= playlist.id))  

        flash('Failed to create playlist. Please try again.')
        return redirect(url_for('create_playlist'))  # Redirect to the create playlist page if user is not found

    songs = Song.query.all()
    return render_template('create_playlist.html', songs=songs,user=user)


@app.route('/view_playlist/<int:playlist_id>')
def view_playlist(playlist_id):
    if 'user_id' not in session:
        flash('Please Login first')
        return redirect(url_for('user_login'))
    
    user = user=User.query.get(session['user_id'])
    playlist = Playlist.query.get(playlist_id)

    if not playlist:
        flash('Playlist not found!')
        return redirect(url_for('user_dashboard'))  # Redirect to the user dashboard or any appropriate page

    return render_template('view_playlist.html', playlist=playlist, user=user)
