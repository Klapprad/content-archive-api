#####HEADDER
#### Librarys laden
from flask import Flask, request, jsonify           # <- API Framework
import yt_dlp                                       # <- Git downloader für Videos
import os
from datetime import datetime                       # <- brauchen wir für den Datumsfilter

######Flask <- empfängt request und gibt an die funktionen weiter, die dann dlp tool aufrufen
app = Flask(__name__)

# Pfad für die Downloads
DOWNLOAD_DIR = "./downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

##########################FILTERFUNKTION #############################################################
def date_filter(info, *, incomplete, start_date=None, end_date=None):
    ####extrahiert Upload_date YYYYMMDD
    upload_date = info.get('upload_date')


    if not upload_date:             ###falls kein Datum vorhanden trotzdem runterladen
        return None

    #daytime conversion
    video_date = datetime.strptime(upload_date, '%Y%m%d')

    # Filter für start_date
    if start_date:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        if video_date < start:
            return 'Video ist zu alt'  # Video wird übersprungen

    # Filter nach end_date
    if end_date:
        end = datetime.strptime(end_date, '%Y-%m-%d')
        if video_date > end:
            return 'Video ist zu neu'  # Video wird übersprungen

    ####None = Video fällt in den Zeitraum und wird heruntergeladen
    return None

######################### USER CONTEND ##################################################
@app.route('/download/user', methods=['POST'])
def download_user_videos():
    data = request.get_json()

    ##### failsafe
    if not data or 'username' not in data:
        return jsonify({'error': 'Username eingeben'}), 400

    ###### request mit parametern:
    username = data['username']
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    # failsafe Format YYYY-MM-DD
    if start_date:
        try:
            datetime.strptime(start_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Format YYYY-MM-DD'}), 400

    if end_date:
        try:
            datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Format YYYY-MM-DD'}), 400

    # Erstellet eigenen Ordner für den Download/User
    user_dir = os.path.join(DOWNLOAD_DIR, username)
    os.makedirs(user_dir, exist_ok=True)

    # Konfiguration für yt-dlp
    ydl_opts = {
        'format': 'best',  # Beste verfügbare Qualität
        # Dateiname: 20241218_Videotitel.mp4
        'outtmpl': os.path.join(user_dir, '%(upload_date)s_%(title)s.%(ext)s'),
        'ignoreerrors': True,  # Bei Fehler weitermachen, nicht abbrechen
        'writeinfojson': True,  # Metadaten als .json Datei speichern
    }

    #### Zeitfilter zum Request für jedes Video
    if start_date or end_date:
        ydl_opts['match_filter'] = lambda info, incomplete: date_filter(
            info,
            incomplete=incomplete,
            start_date=start_date,
            end_date=end_date
        )

    #### URL mit Usernamen vervcollständingen
    url = f'https://www.tiktok.com/@{username}'

    try:
        downloaded_videos = []

        ###download mit dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)            # extract_info holt  infos und lädt runter


            if 'entries' in info:                               # entries = alle videos des Users
                for entry in info['entries']:
                    if entry:
                        downloaded_videos.append({
                            'title': entry.get('title'),
                            'upload_date': entry.get('upload_date'),
                            'id': entry.get('id')
                        })

            ##### download bestätigen
            return jsonify({
                'status': 'success',
                'username': username,
                'start_date': start_date,
                'end_date': end_date,
                'videos_downloaded': len(downloaded_videos),
                'output_dir': user_dir,
                'videos': downloaded_videos             # Liste der downloads
            }), 200

    except Exception as e:                      #Fehlermeldung
        return jsonify({
            'status': 'error',
            'username': username,
            'error': str(e)
        }), 500

##Failsafe
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200


##################################### Hauptprogramm ###########################
    # Startet Flask
    # debug=True zeigt Fehlermeldungen
    # port=5001 <- server läuft auf Port 5001, kann bei Problemen angepasst werden

if __name__ == '__main__':
    print(f"Downloads werden gespeichert in: {DOWNLOAD_DIR}")
    print("API läuft auf http://localhost:5001")
    print("\nBeispiel:")
    print('curl -X POST http://localhost:5001/download/user -H "Content-Type: application/json" -d \'{"username":"USERNAME","start_date":"2024-01-01","end_date":"2024-12-31"}\'')

    app.run(debug=True, host='0.0.0.0', port=5001)
