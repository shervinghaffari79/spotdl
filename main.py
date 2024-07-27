from telegram import *
from telegram.ext import *
# import spotipy
# from spotipy.oauth2 import SpotifyClientCredentials
# import spotdl
# import re
# import os
# import time
# import subprocess

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id='fa032c00d47049548b789d364180b116',
                                                           client_secret='b456da8e4acd4cf8aca1a61ef111643f'))

def start(update: Update, context: CallbackContext) -> None:

   keyboard = [
        [
            InlineKeyboardButton("Search Tracks",switch_inline_query_current_chat='tracks')
        ]
    ]

   reply_markup = InlineKeyboardMarkup(keyboard)

   f_name = update.message.from_user.first_name
   update.message.reply_text(f'Hi, {f_name}. Search By:',reply_markup=reply_markup)

def download_from_spotify(url, update: Update):
    """
    Download track from Spotify using spotdl, updating progress in Telegram.
    """
    command = f"spotdl {url}"

    # Start the subprocess
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # Send initial message to user
    message = update.message.reply_text('Starting download')


    dots = 0
    try:
        while True:
            if process.poll() is not None:
                break  # Exit loop if process is done
            dots+=1
            dots%=3+1
            update.message.bot.edit_message_text(chat_id=update.message.chat_id, message_id=message.message_id, text=f'Starting download{"." * dots}')
            time.sleep(1)

    except Exception as e:
        update.message.reply_text(f'Error during download: {str(e)}')

    # Final message after loop completion
    if process.returncode == 0:
        update.message.bot.edit_message_text(chat_id=update.message.chat_id, message_id=message.message_id, text="Download complete!")
    else:
        update.message.reply_text("Download failed. Please try again.")


def extract_track_id(url):
    """
    Extract the track ID from a Spotify track URL.
    """
    track_id_pattern = re.compile(r'spotify\.com/track/([^?&]+)')
    match = track_id_pattern.search(url)
    if match:
        return match.group(1)
    return None

def get_track_details(url):
    """
    Get track details from a Spotify URL.
    """
    track_id = extract_track_id(url)
    if track_id:
        track = sp.track(track_id)
        return {
            'name': track['name'],
            'artists': [artist['name'] for artist in track['artists']],
            'album': track['album']['name'],
            'release_date': track['album']['release_date'],
            'popularity': track['popularity'],
            'preview_url': track['preview_url'],
            'external_url': track['external_urls']['spotify'],
            'image_url': track['album']['images'][0]['url'] if track['album']['images'] else None
        }
    else:
        return None

def search_tracks(query):
    results = sp.search(q=query, limit=10, type='track')
    tracks = []
    seen = set()

    for track in results['tracks']['items']:

        main_artist = track['artists'][0]['name'] if track['artists'] else 'Unknown'
        track_key = (track['name'], main_artist)

        if track_key not in seen:
            seen.add(track_key)
            tracks.append({
                'id': len(tracks) + 1,
                'name': track['name'],
                'artists': [artist['name'] for artist in track['artists']],
                'url': track['external_urls']['spotify'],
                'image_url': track['album']['images'][-1]['url'] if track['album']['images'] else None,
                'release_date': track['album']['release_date'] if 'release_date' in track['album'] else 'Unknown'
            })

    return tracks

def inline_query(update: Update, context: CallbackContext):
    query = update.inline_query.query
    query = query.split()[1:]
    if not query:
        return
    try:
        track_results = search_tracks(query)
        results = [
            InlineQueryResultArticle(
                id=str(track['id']),
                title=f"Track: {track['name']}",
                input_message_content=InputTextMessageContent(
                    f"{track['url']}"
                ),
                description=f"Artists: {', '.join(artist for artist in track['artists'])}\nReleased: {track['release_date']}\n",
                thumb_url=track['image_url']
            ) for track in track_results
        ]

        update.inline_query.answer(results, cache_time=10)
    except Exception as e:
        print(f"Error processing the inline query: {e}")




def handle_message(update: Update, context: CallbackContext) -> None:
    url = update.message.text
    track_details = get_track_details(url)

    if track_details:
        # Send photo
        image_url = track_details['image_url']
        caption=f"""💽 Track: {track_details['name']}\n🎤 Artists: {', '.join(track_details['artists'])}\n📅 Released: {track_details['release_date']}\n🥂 Popularity: {track_details['popularity']}\n"""
        if image_url:
            try:
                update.message.reply_photo(photo=image_url,caption=caption)
            except Exception as e:
                update.message.reply_text(f'Failed to send photo: {e}')

        file_path = f"/content/{track_details['artists'][0]} - {track_details['name']}.mp3"  # Temporary file path
        try:
            download_from_spotify(url,update)
            with open(file_path, 'rb') as audio_file:
                update.message.reply_audio(audio_file)

        except Exception as e:
            update.message.reply_text(f'Failed to Download: {e}')
    else:
        update.message.reply_text('Failed to get track details or invalid URL.')

def main() -> None:

    updater = Updater('6182770161:AAHK7Wppu5TZv_CEHmANdPOGrWdbybQlQtM')

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    # dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    # dp.add_handler(InlineQueryHandler(inline_query))


    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
  main()
