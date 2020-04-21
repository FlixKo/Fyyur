#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)

migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String)
    shows = db.relationship('Show',backref='venue_shows', lazy=True,cascade="all, delete-orphan", passive_deletes=True)

class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String)
    shows = db.relationship('Show',backref='artist_shows', passive_deletes=True, lazy=True)

class Show(db.Model):
    __tablename__ = 'show'

    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer,db.ForeignKey('venue.id',ondelete='CASCADE'),nullable=False)
    artist_id = db.Column(db.Integer,db.ForeignKey('artist.id',ondelete='CASCADE'),nullable=False)
    start_time = db.Column(db.DateTime)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():

  venues = Venue.query.order_by(Venue.state, Venue.city).all()
  data = []
  areas = db.session.query(Venue.city, Venue.state).distinct()
  
  for venue in areas:
    venue = dict(zip(('city', 'state'), venue))
    venue['venues'] = []
    for venue_data in Venue.query.filter_by(city=venue['city'], state=venue['state']).all():
      shows = Show.query.filter_by(venue_id=venue_data.id).all()
      upcoming_shows = []
      for show in shows:
        if show.start_time > datetime.now():
          upcoming_shows.append({
            "artist_id": show.artist_id,
            "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
            "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
            "start_time": format_datetime(str(show.start_time))
          })
          venues_data = {
            'id': venue_data.id,
            'name': venue_data.name,
            'num_upcoming_shows': len(upcoming_shows)
          }
          venue['venues'].append(venues_data)
      data.append(venue)
  return render_template('pages/venues.html', areas=data)

  # replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  # data=[{
  #   "city": "San Francisco",
  #   "state": "CA",
  #   "venues": [{
  #     "id": 1,
  #     "name": "The Musical Hop",
  #     "num_upcoming_shows": 0,
  #   }, {
  #     "id": 3,
  #     "name": "Park Square Live Music & Coffee",
  #     "num_upcoming_shows": 1,
  #   }]
  # }, {
  #   "city": "New York",
  #   "state": "NY",
  #   "venues": [{
  #     "id": 2,
  #     "name": "The Dueling Pianos Bar",
  #     "num_upcoming_shows": 0,
  #   }]
  # }]
  # return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_str = request.form.get('search_term')
  flash(search_str)
  venue_search = Venue.query.filter(Venue.name.ilike('%{}%'.format(search_str)))
  venue_list = list(venue_search)
  # implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  response = {
    "count":len(venue_list),
    "data": venue_list
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = Venue.query.get(venue_id)
  shows = Show.query.filter_by(venue_id=venue_id).all()
  upcoming_shows = []
  past_shows = []
  for show in shows:
    if show.start_time > datetime.now():
      upcoming_shows.append({
        "artist_id": show.artist_id,
        "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
        "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
        "start_time": format_datetime(str(show.start_time))
      })
    else:
      past_shows.append({
        "artist_id": show.artist_id,
        "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
        "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
        "start_time": format_datetime(str(show.start_time))
      })

  data={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  error = False
  try:
      new_venue = Venue(
        name=request.form.get('name'),
        city=request.form.get('city'),
        state=request.form.get('state'),
        address=request.form.get('address'),
        phone=request.form.get('phone'),
        image_link=request.form.get('image_link'),
        genres=request.form.getlist('genres'),
        facebook_link=request.form.get('facebook_link'),
        website=request.form.get('website'),
        seeking_talent=request.form.get('seeking_talent'),
        seeking_description=request.form.get('seeking_description')
      )
      db.session.add(new_venue)
      db.session.commit()

  except Exception as e:
    flash('An error occurred. Venue could not be listed.')
    flash(f'Error: {e}')
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    # do not show success page.
    return render_template('pages/home.html')
  else:
    flash('Venue ' + request.form.get('name') + ' was successfully listed!')
    return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return None
  
  # Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artists = Artist.query.order_by(Artist.name).all()
  data = []
  for artist in artists:
    artist_data = {
      "id": artist.id,
      "name": artist.name,
    }
    data.append(artist_data)
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_str = request.form.get('search_term')
  artist_search = Artist.query.filter(Artist.name.ilike('%{}%'.format(search_str)))
  artist_list = list(artist_search)

  response = {
    "count":len(artist_list),
    "data": artist_list
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = Artist.query.get(artist_id)
  shows = Show.query.filter_by(artist_id=artist_id).all()
  upcoming_shows = []
  past_shows = []
  for show in shows:
    if show.start_time > datetime.now():
      upcoming_shows.append({
        "artist_id": show.artist_id,
        "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
        "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
        "start_time": format_datetime(str(show.start_time))
      })
    else:
      past_shows.append({
        "artist_id": show.artist_id,
        "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
        "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
        "start_time": format_datetime(str(show.start_time))
      })

  data={
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website": artist.website,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get(artist_id)
  form = ArtistForm(obj=artist)
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  error = False
  try:
    artist = Artist.query.get(artist_id)
    artist.name=request.form.get('name'),
    artist.city=request.form.get('city'),
    artist.state=request.form.get('state'),
    artist.phone=request.form.get('phone'),
    artist.genres=request.form.getlist('genres'),
    artist.facebook_link=request.form.get('facebook_link'),
    db.session.commit()

  except Exception as e:
    flash('An error occurred. Artist could not be updated.')
    flash(f'Error: {e}')
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    # do not show success page.
    return redirect(url_for('show_artist', artist_id=artist_id))
  else:
    flash('Artist ' + request.form.get('name') + ' was successfully updated!')
    return redirect(url_for('show_artist', artist_id=artist_id))
        
  

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)
  form = VenueForm(obj=venue)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id): 
  error = False
  try:
    venue = Venue.query.get(venue_id)
    venue.name=request.form.get('name'),
    venue.city=request.form.get('city'),
    venue.state=request.form.get('state'),
    venue.address=request.form.get('address'),
    venue.phone=request.form.get('phone'),
    venue.genres=request.form.getlist('genres'),
    venue.facebook_link=request.form.get('facebook_link'),
    db.session.commit()

  except Exception as e:
    flash('An error occurred. Venue could not be updated.')
    flash(f'Error: {e}')
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    # do not show success page.
    return redirect(url_for('show_venue', venue_id=venue_id))
  else:
    flash('Venue ' + request.form.get('name') + ' was successfully updated!')
    return redirect(url_for('show_venue', venue_id=venue_id))
        
#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error = False
  try:
    
      new_artist = Artist(
        name=request.form.get('name'),
        city=request.form.get('city'),
        state=request.form.get('state'),
        phone=request.form.get('phone'),
        image_link=request.form.get('image_link'),
        genres=request.form.getlist('genres'),
        facebook_link=request.form.get('facebook_link'),
        website=request.form.get('website'),
      )
      db.session.add(new_artist)
      db.session.commit()

      #genres = SelectMultipleField( 'genres', validators=[DataRequired(), AnyOf(values=genres)], choices=genres )

  except Exception as e:
    flash('An error occurred. Artist ' + request.form.get('name') + 'could not be listed.')
    flash(f'Error: {e}')
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    # do not show success page.
    return render_template('pages/home.html')
  else:
    flash('Artist ' + request.form.get('name') + ' was successfully listed!')
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  shows = Show.query.order_by(Show.start_time).all()
  data = []
  for show in shows:
    show_data = {
      "venue_id": show.venue_id,
      "venue_name": Venue.query.filter_by(id=show.venue_id).first().name,
      "artist_id": show.artist_id,
      "artist_name": Artist.query.filter_by(id=show.artist_id).first().name,
      "artist_image_link": Artist.query.filter_by(id=show.artist_id).first().image_link,
      "start_time": format_datetime(str(show.start_time))
    }
    data.append(show_data)
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  error = False
  try:
      new_show = Show(
        artist_id=request.form.get('artist_id'),
        venue_id=request.form.get('venue_id'),
        start_time=request.form.get('start_time'),
      )
      db.session.add(new_show)
      db.session.commit()

  except Exception as e:
    flash(f'An error occurred. Show could not be listed. Error: {e}')
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    # do not show success page.
    return render_template('pages/home.html')
  else:
    flash('Show was successfully listed!')
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
