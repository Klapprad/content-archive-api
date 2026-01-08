#####HEADDER
#### Librarys laden
from flask import Flask, request, jsonify
import yt_dlp
import os
from datetime import datetime

######Flask <- empfängt request und gibt an die funktionen weiter, die dann dlp tool aufrufen
app = Flask(__name__)

# Pfad für die Downloads
# DOWNLOAD_DIR = "/media/usb/tiktok"            ###für usb
#DOWNLOAD_DIR = "./downloads"
#os.makedirs(DOWNLOAD_DIR, exist_ok=True)

DOWNLOAD_DIR = "/home/tom/Desktop/tiktok"
##########################FILTERFUNKTION #############################################################
# Args:
    #incomplete <- flag ob Download noch läuft
    #start_date
    #end_date

#Returns:
    #None <- Video behalten
    #String wenn Video übersprungen wird wegen Filter


def date_filter(info, *, incomplete, start_date=None, end_date=None):

    upload_date = info.get('upload_date')           # Datum aus Metadaten holen

    if not upload_date:                             # kein Datum = video skippen
        return None

    #daytime conversion
    video_date = datetime.strptime(upload_date, '%Y%m%d')

    # Filter für start
    if start_date:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        if video_date < start:
            return 'davor'      # wird übersprungen

    # Filter für ende
    if end_date:
        end = datetime.strptime(end_date, '%Y-%m-%d')
        if video_date > end:
            return 'danach'     # wird übersprungen

    ####None = Video fällt in den Zeitraum und wird runtergeladen
    return None

######################### USER CONTEND ##################################################
@app.route('/download/user', methods=['POST'])   # API-Endpunkt lädt Videos des users
def download_user_videos():
    data = request.get_json()

    ##### failsafe
    if not data or 'username' not in data:
        return jsonify({'error': 'Username fehlt'}), 400

    ###### Parameter für downlod aus request:
    username = data['username']             # muss
    start_date = data.get('start_date')     # optional mit None
    end_date = data.get('end_date')         # optional mit None

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

    # dlp konfig
    ydl_opts = {
        'format': 'best',
        'outtmpl': os.path.join(user_dir, '%(upload_date)s_%(title)s.%(ext)s'),
        'ignoreerrors': True,
        'writeinfojson': True,  # Jason abspeichern, False wenn nicht
    }

    #### Zeitfilter zum Request für jedes Video
    if start_date or end_date:
        # Lambda-Funktion die für jedes Video aufgerufen wird
        ydl_opts['match_filter'] = lambda info, incomplete: date_filter(
            info,
            incomplete=incomplete,
            start_date=start_date,
            end_date=end_date
        )

    # tiktok URL zusammenbauen
    url = f'https://www.tiktok.com/@{username}'

    try:
        ## Downloars Liste
        downloaded_videos = []

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)        # extract_info holt  infos und lädt runter

            if 'entries' in info:                           # entries = alle videos des Users
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

    except Exception as e:                      #Fehlermedlung
        return jsonify({
            'status': 'error',
            'username': username,
            'error': str(e)
        }), 500


##Failsafe API läuft
@app.route('/health', methods=['GET'])
def health():

    return jsonify({'status': 'up'}), 200

########################################################################
###############################  HAUPTPROGRAMM ###########################
    # Startet Flask
    # debug=True zeigt Fehlermeldungen
    # port=5001 <- server läuft auf Port 5001, kann bei Problemen angepasst werden

if __name__ == '__main__':
    print("Skript läuft")

    app.run(debug=True, host='0.0.0.0', port=5001)
