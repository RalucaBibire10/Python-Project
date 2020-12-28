import mysql.connector
import os
import sys
from os.path import basename
from varname import nameof
from zipfile import ZipFile
from shutil import copy

os.add_dll_directory(r'C:\Program Files\VideoLAN\VLC')
import vlc
import re


# conectarea la baza de date


class SongStorage:
    path_re = re.compile("[C-F]{1}(:/){1}([a-z|A-Z|0-9]|/| |-|!|\(|\))+(.mp3|.wav)")
    path_zip = re.compile("[C-F]{1}(:/){1}([a-z|A-Z|0-9]|/| |-|!|\(|\))+(.zip)")
    path_storage_re = re.compile(
        "[C-F]{1}(:/){1}([a-z|A-Z|0-9]|/| |-|!|\(|\))+(Storage)([a-z|A-Z|0-9]|/| |-|!|\(|\))+(.mp3|.wav)")
    cnx = None
    isPlaying = False
    playSong = []
    p = str(os.path.dirname(os.path.realpath(__file__))).replace('\\', '/') + '/Storage'
    mycursor = None

    def __init__(self):
        self.cnx = mysql.connector.connect(user='root', password='',
                                           host='127.0.0.1',
                                           database='songstorage')
        os.add_dll_directory(r'C:\Program Files\VideoLAN\VLC')
        # crearea tabelei songs
        self.mycursor = self.cnx.cursor()
        # verificarea existentei tabelei
        self.mycursor.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'songstorage' AND table_name = 'songs'")
        myresult = self.mycursor.fetchall()
        # crearea prorpiu-zisa
        if myresult[0][0] == 0:
            self.mycursor.execute(
                "CREATE TABLE songs (ID INT NOT NULL AUTO_INCREMENT, file_title VARCHAR(255), song_title VARCHAR("
                "255), artist VARCHAR(255), format VARCHAR(255), data VARCHAR(255), tag VARCHAR(255), PRIMARY KEY ("
                "ID))")

    # asteptarea unei comenzi
    def startTool(self):
        while True:
            com = input("Give a command. Type H for help...:\t ")
            if com == 'H' or com == 'h':
                print('Available commands: H, Exit, Play, Stop, Pause, Add_song, Delete_song, Modify_data, '
                      'Create_save_list, Search')
            elif com == 'Exit':
                if self.isPlaying:
                    self.isPlaying = False
                    self.playSong[0].stop()
                    self.playSong.clear()
                print("Exiting...")
                break
            elif com == 'Play':
                if not self.isPlaying:
                    self.play_song()
                else:
                    stop = input("There is a song paused. Do you want to stop it and play another song? [Y/N]")
                    while True:
                        if stop == 'N':
                            print("The song current song will be resumed...")
                            self.playSong[0].play()
                            break
                        elif stop == 'Y':
                            self.stop_song()
                            break
                        else:
                            print("Unknown command. Please answer with Y or N...")
            elif com == 'Stop':
                self.stop_song()
            elif com == 'Pause':
                self.pause_song()
            elif com == 'Add_song':
                print(self.add_song())
            elif com == 'Delete_song':
                self.delete_song()
            elif com == 'Modify_data':
                self.modify_data()
            elif com == "Create_save_list":
                self.create_save_list()
            elif com == "Search":
                self.search()
            else:
                print("Unknown command. Try again...")

    def play_song(self):
        path = input('Give path to wanted song: ')
        path = path.replace('\\', '/')
        if not self.path_storage_re.match(path):
            print("Give a valid path")
        else:
            p = vlc.MediaPlayer(path)
            p.play()
            self.playSong.append(p)
            self.isPlaying = True

    def stop_song(self):
        if self.isPlaying:
            self.playSong[0].stop()
            self.playSong.clear()
            self.isPlaying = False
            print("Music stopped")
        else:
            print("Play a song first...")

    def pause_song(self):
        if self.isPlaying:
            self.playSong[0].pause()
            print("Song paused. To continue type Play.")
        else:
            print("Play a song first...")

    def add_song(self):
        path = input("Give file path:\t")
        path = path.replace('\\', '/')
        if self.path_re.match(path):
            copy(path, self.p)
            file_title, form = path.split("/")[-1].split(".")
            sql = "SELECT COUNT(*) FROM songs WHERE file_title = %s AND format = %s"
            self.mycursor.execute(sql, (file_title, form))
            r = self.mycursor.fetchall()
            if len(r):
                return "Song with this file name and format already exists!"
            song_title = input("Song title:\t")
            artist = input("Artist:\t")
            data = input("Release date:\t")
            tags = input("Associated tags:\t")
            sql = "INSERT INTO songs (file_title, song_title, artist, format, data, tag) VALUES (%s, %s, %s, %s, %s, " \
                  "%s) "
            val = (file_title, song_title, artist, form, data, tags)
            self.mycursor.execute(sql, val)
            self.cnx.commit()
            self.mycursor.execute(
                "SELECT MAX(ID) FROM songs")
            myresult = self.mycursor.fetchall()
            return "New song ID: " + str(myresult[0][0])
        else:
            return "Give valid path"

    def delete_song(self):
        id = tuple(input("Give the melody id to be deleted:\t"))
        sql = "SELECT file_title, format FROM songs WHERE id = %s"
        self.mycursor.execute(sql, id)
        myresult = self.mycursor.fetchall()
        if len(myresult) > 0:
            path = self.p + "/" + myresult[0][0] + "." + myresult[0][1]
            os.remove(path)
            sql = "DELETE FROM songs WHERE id = %s"
            self.mycursor.execute(sql, id)
            self.cnx.commit()
            print(self.mycursor.rowcount, "record(s) deleted")
        else:
            print("Give a valid id...")

    def modify_data(self):
        id = tuple(input("Give the melody id to be modified:\t"))
        sql = "SELECT song_title, artist, data, tag FROM songs WHERE id = %s"
        self.mycursor.execute(sql, id)
        res = self.mycursor.fetchall()
        if len(res) > 0:
            while True:
                sql = "SELECT song_title, artist, data, tag FROM songs WHERE id = %s"
                self.mycursor.execute(sql, id)
                myresult = self.mycursor.fetchall()
                modify = input("What do you want to modify? [title/artist/(release )date/tags/none]\t")
                if modify == 'title':
                    print('Current title is ' + myresult[0][0])
                    new = (input('Give new title:\t'), id[0])
                    sql = "UPDATE songs SET song_title = %s WHERE id = %s"
                    print(new)
                    self.mycursor.execute(sql, new)
                    self.cnx.commit()
                    print("New title assigned")
                if modify == 'artist':
                    print('Current artist is ' + myresult[0][1])
                    new = (input('Give new title:\t'), id[0])
                    sql = "UPDATE songs SET artist = %s WHERE id = %s"
                    self.mycursor.execute(sql, new)
                    self.cnx.commit()
                    print("New title assigned")
                if modify == 'date':
                    print('Current date is ' + myresult[0][2])
                    new = (input('Give new title:\t'), id[0])
                    sql = "UPDATE songs SET data = %s WHERE id = %s"
                    self.mycursor.execute(sql, new)
                    self.cnx.commit()
                    print("New date assigned")
                if modify == 'tags':
                    print('Current tags are ' + myresult[0][3])
                    new = (input('Give new title:\t'), id[0])
                    sql = "UPDATE songs SET tags = %s WHERE id = %s"
                    self.mycursor.execute(sql, new)
                    self.cnx.commit()
                    print("New tags assigned")
                if modify == 'none':
                    sql = "SELECT song_title, artist, data, tag FROM songs WHERE id = %s"
                    self.mycursor.execute(sql, id)
                    result = self.mycursor.fetchall()
                    print("Current data for the song with id" + id[0] + "are:\ntitle:" + result[0][0] + "\nartist:" +
                          result[0][1] + "\nrelease date:" + result[0][2] + "\ntags:" + result[0][3])
                    break
        else:
            print("Give a valid id...")

    def select(self):
        artist, data, tag, format = [None, None], [None, None], [None, None], [None, None]
        while True:
            artist[0] = input("Would you like to select by artist?[Y/N]\t")
            if artist[0] == 'Y':
                artist[1] = input("Give artist name:\t")
                break
            elif artist[0] == 'N':
                break
            else:
                print("Unknown answer. Please respond with Y or N")
        while True:
            data[0] = input("Would you like to select by release date?[Y/N]\t")
            if data[0] == 'Y':
                data[1] = input("Give release date:\t")
                break
            elif data[0] == 'N':
                data[1] = None
                break
            else:
                print("Unknown answer. Please respond with Y or N")
        while True:
            tag[0] = input("Would you like to select by tags?[Y/N]\t")
            if tag[0] == 'Y':
                tag[1] = input("Give a tag:\t")
                break
            elif tag[0] == 'N':
                tag[1] = None
                break
            else:
                print("Unknown answer. Please respond with Y or N")
        while True:
            format[0] = input("Would you like to select by format?[Y/N]\t")
            if format[0] == 'Y':
                format[1] = input("Give format:\t")
                break
            elif format[0] == 'N':
                format[1] = None
                break
            else:
                print("Unknown answer. Please respond with Y or N")
        where = ""
        criterias = tuple()
        if artist[0] == 'Y':
            where += nameof(artist) + " = %s AND "
            criterias += (artist[1],)
        if data[0] == 'Y':
            where += nameof(data) + " = %s AND "
            criterias += (data[1],)
        if tag[0] == 'Y':
            where += nameof(tag) + " LIKE %s AND "
            criterias += ("%" + tag[1] + "%",)
        if format[0] == 'Y':
            where += nameof(artist) + " = %s AND "
            criterias += (format[1],)
        return criterias, where

    def create_save_list(self):
        criterias, where = self.select()
        sql = "SELECT file_title, format FROM songs WHERE " + where[0:len(where) - 4]
        self.mycursor.execute(sql, criterias)
        result = self.mycursor.fetchall()
        if len(result) == 0:
            print("No songs match your criteria")
            return
        while True:
            path = input("Give the path to the zip:\t")
            path = path.replace('\\', '/')
            if self.path_zip.match(path):
                with ZipFile(path, 'w') as myzip:
                    for song in result:
                        song_path = self.p + "/" + song[0] + "." + song[1]
                        myzip.write(song_path, basename(song_path))
                    myzip.close()
                break
            else:
                print("Give valid path")

    def search(self):
        criterias, where = self.select()
        sql = "SELECT * FROM songs WHERE " + where[0:len(where) - 4]
        self.mycursor.execute(sql, criterias)
        result = self.mycursor.fetchall()
        if len(result) == 0:
            print("No songs match your criteria")
            return
        contor = 1
        for mel in result:
            print("------------",contor,"------------")
            for field, name in zip(mel, self.mycursor.column_names):
                print(name, ":", field)
            contor += 1


tool = SongStorage()
tool.startTool()

# TODO: configure the table, if there is an error, don't add the song, check if melody is already in playlist
