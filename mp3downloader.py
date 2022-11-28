from flask import Flask, render_template, request, redirect
from werkzeug.exceptions import HTTPException
from flask_caching import Cache
import subprocess
import os
import secrets
from pytube import YouTube, exceptions
import socket
from waitress import serve
from flask_compress import Compress

VERSION = "v0.0.8"

os.system("title MP3 YT Downloader %s" % VERSION)

app = Flask(__name__)
app.secret_key = secrets.token_hex(64)

title = ["Homepage", "About"]
config = {
    "DEBUG": True,
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 300
}

app.config.from_mapping(config)
cache = Cache(app)
cache.init_app(app)
app.config["COMPRESS_REGISTER"] = False  # disable default compression of all eligible requests
compress = Compress()
compress.init_app(app)


@app.route("/", methods=(["GET", "POST"]))
@compress.compressed()
def main_page():
    if request.method == "POST":
        yt_link = request.form.get("yt-link").encode()

        try:
            

            yt = YouTube(yt_link.decode(), allow_oauth_cache=True)
            UNALLOWED_CHARS = ["\\", "/", ":", "*", "?", "\"", "<", ">", "|"]
            formatted_title = "".join(["-" if char in UNALLOWED_CHARS else char for char in yt.title.encode("ascii", "ignore").decode()])
            formatted_author = yt.author.replace("- Topic", " ")
            yt.streams.filter(abr="160kbps", progressive=False).first().download(
                filename="DOWNLOADS\%s.webm" % formatted_title)
            os.chdir(os.getcwd().replace("\\\src", " "))
            subprocess.run(
                f'ffmpeg -y -i "DOWNLOADS\%s.webm" -codec:a:1 eac3 -b:a 320k -metadata title="%s" -metadata '
                f'artist="%s" "DOWNLOADS\%s.mp3" -hide_banner -loglevel error' % (
                    formatted_title, formatted_title, formatted_author, formatted_title),
                shell=True)

            os.remove("DOWNLOADS\%s.webm" % formatted_title)

        except exceptions.RegexMatchError:
            return redirect('/404')

    return render_template("index.html", title=title[0], status_title="MP3 YT Downloader")


@app.route("/about", methods=(["GET"]))
@cache.cached(timeout=1)
def about():
    return render_template("about.html", title=title[1], VERSION=VERSION)


@app.errorhandler(HTTPException)
def error(error_):
    return render_template('error.html', title=str(error_.code), error_code=error_.code,
                           error_message=error_.description)


if __name__ == "__main__":
    subprocess.run(["cls"], shell=True)
    print("Host: \033[93m%s\033[0m\nRunning on: \033[94mhttp://%s:8080\033[0m" % (socket.gethostname(), socket.gethostbyname(socket.gethostname())))
    serve(app, host="0.0.0.0", port=8080, threads=6)
