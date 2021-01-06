import os
import re
from os.path import basename
from shutil import copy
from zipfile import ZipFile

import mysql.connector
import vlc
from varname import nameof


def select():
    """Return criteria given by user and the column in the database it refers to."""
    file_title, song_title = [None, None], [None, None]
    artist, data, tag, form = [None, None], [None, None], [None, None], [None, None]
    while True:
        file_title[0] = input("Would you like to select by file name?[Y/N]\t")
        if file_title[0] == 'Y':
            file_title[1] = input("Give file name:\t")
            break
        elif file_title[0] == 'N':
            break
        else:
            print("Unknown answer. Please respond with Y or N...")
    while True:
        song_title[0] = input("Would you like to select by song title?[Y/N]\t")
        if song_title[0] == 'Y':
            song_title[1] = input("Give song title:\t")
            break
        elif song_title[0] == 'N':
            break
        else:
            print("Unknown answer. Please respond with Y or N...")
    while True:
        artist[0] = input("Would you like to select by artist?[Y/N]\t")
        if artist[0] == 'Y':
            artist[1] = input("Give artist name:\t")
            break
        elif artist[0] == 'N':
            break
        else:
            print("Unknown answer. Please respond with Y or N...")
    while True:
        data[0] = input("Would you like to select by release date?[Y/N]\t")
        if data[0] == 'Y':
            data[1] = input("Give release date:\t")
            break
        elif data[0] == 'N':
            data[1] = None
            break
        else:
            print("Unknown answer. Please respond with Y or N...")
    while True:
        tag[0] = input("Would you like to select by tags?[Y/N]\t")
        if tag[0] == 'Y':
            tag[1] = input("Give a tag:\t")
            break
        elif tag[0] == 'N':
            tag[1] = None
            break
        else:
            print("Unknown answer. Please respond with Y or N...")
    while True:
        form[0] = input("Would you like to select by format?[Y/N]\t")
        if form[0] == 'Y':
            form[1] = input("Give format:\t")
            break
        elif form[0] == 'N':
            form[1] = None
            break
        else:
            print("Unknown answer. Please respond with Y or N...")
    where = ""  # Saves the where-clause for the database interrogation
    criteria = tuple()  # Saves the criteria given by the user
    if file_title[0] == 'Y':
        where += nameof(file_title) + " = %s AND "
        criteria += (file_title[1],)
    if song_title[0] == 'Y':
        where += nameof(song_title) + " = %s AND "
        criteria += (song_title[1],)
    if artist[0] == 'Y':
        where += nameof(artist) + " = %s AND "
        criteria += (artist[1],)
    if data[0] == 'Y':
        where += nameof(data) + " = %s AND "
        criteria += (data[1],)
    if tag[0] == 'Y':
        where += nameof(tag) + " LIKE %s AND "
        criteria += ("%" + tag[1] + "%",)
    if form[0] == 'Y':
        where += nameof(artist) + " = %s AND "
        criteria += (form[1],)
    return criteria, where


class SongStorage:
    path_song_re = re.compile("[C-F](:/)([a-z|A-Z|0-9]|/| |-|!|\(|\))+(.mp3|.wav)")  # Regex for the path to a song
    path_zip = re.compile("[C-F](:/)([a-z|A-Z|0-9]|/| |-|!|\(|\))+(.zip)")  # Regex for a path to a zip
    path_storage_re = re.compile(
        "[C-F](:/)([a-z|A-Z0-9]|/| |-|!|\(|\))+(Storage)([a-z|A-Z0-9]|/| |-|!|\(|\))+(.mp3|.wav)")  # Regex for a
    # song found in Storage directory

    cnx = None  # Connection to the database
    isPlaying = False  # Boolean variable for knowing if a song is currently playing or paused
    playSong = []  # VLC instance of the song that is currently playing
    p_storage = str(os.path.dirname(os.path.realpath(__file__))).replace('\\', '/') + '/Storage'  # Path to
    # the Storage directory
    cursor = None  # mySQL cursor

    def __init__(self):
        """
        Initialization of the tool
        Make database and table and connect to the database
        """

        self.cnx = mysql.connector.connect(user='root', password='',
                                           host='127.0.0.1',
                                           database='songstorage')  # Connect to mySQL, username root, password none
        self.cursor = self.cnx.cursor()  # Initialize the mySQL cursor
        self.cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'songstorage'"
                            " AND table_name = 'songs'")  # Check the existence of the table
        result = self.cursor.fetchall()
        if result[0][0] == 0:
            self.cursor.execute(
                "CREATE TABLE songs (ID INT NOT NULL AUTO_INCREMENT, file_title VARCHAR(255), song_title VARCHAR("
                "255), artist VARCHAR(255), form VARCHAR(255), data VARCHAR(255), tag VARCHAR(255), PRIMARY KEY ("
                "ID))")  # Create the table if it doesn't already exist

    def start_tool(self):
        """Waits for a command and calls the right function."""
        while True:
            com = input("Give a command. Type H for help...:\t ").lower()  # Receive a command from the user
            if com == 'h':
                print('Available commands: H, Exit, Play, Stop, Pause, Add_song, Delete_song, Modify_data, '
                      'Create_save_list, Search')
            elif com == 'exit':
                if self.isPlaying:  # Check if there's any song playing or paused and stop it before exiting
                    self.isPlaying = False
                    self.playSong[0].stop()
                    self.playSong.clear()
                print("Exiting...")
                break
            elif com == 'play':
                if not self.isPlaying:  # Play the song if none is currently paused
                    self.play_song()
                else:
                    stop = input(
                        "There is a song paused or currently playing. Do you want to stop it and play another song? ["
                        "Y/N]\t").lower()
                    while True:
                        if stop == 'n':
                            print("The song current song will be resumed...")
                            self.playSong[0].play()  # Resume the paused song
                            break
                        elif stop == 'y':
                            self.stop_song()  # Stop the paused song
                            self.play_song()  # Play another song
                            break
                        else:
                            print("Unknown command. Please answer with Y or N...")
            elif com == 'stop':
                self.stop_song()
            elif com == 'pause':
                self.pause_song()
            elif com == 'add_song':
                print(self.add_song())
            elif com == 'delete_song':
                self.delete_song()
            elif com == 'modify_data':
                self.modify_data()
            elif com == "create_save_list":
                self.create_save_list()
            elif com == "search":
                self.search()
            else:
                print("Unknown command. Try again...")

    def play_song(self):
        """Play a song based on its path."""
        path = input('Give path to wanted song: ')  # Request path to song
        path = path.replace('\\', '/')
        if not self.path_storage_re.match(path):  # Check if the wanted song is from the storage directory
            print("Give a valid path")
        else:
            p = vlc.MediaPlayer(path)  # Create VLC instance and play the song
            p.play()
            self.playSong.append(p)
            self.isPlaying = True

    def stop_song(self):
        """Stop the current playing/paused song."""
        if self.isPlaying:
            self.playSong[0].stop()
            self.playSong.clear()
            self.isPlaying = False
            print("Music stopped")
        else:
            print("Play a song first...")

    def pause_song(self):
        """Pause the current playing song."""
        if self.isPlaying:
            self.playSong[0].pause()
            print("Song paused. To continue type Play.")
        else:
            print("Play a song first...")

    def add_song(self):
        """Add song to the storage directory and to the database.
        Return ID of the new song / error message.
        """
        path = input("Give file path:\t")  # Request file path
        path = path.replace('\\', '/')
        if self.path_song_re.match(path) and not self.path_storage_re.match(
                path):  # Check that the path leads to a song that is not already found in Storage
            copy(path, self.p_storage)  # Copy the song to the storage directory
            file_title, form = path.split("/")[-1].split(".")  # Save file title and format from the path
            sql = "SELECT COUNT(*) FROM songs WHERE file_title = %s AND form = %s"  # Check the existence of a song
            # with the same title and format in the database
            self.cursor.execute(sql, (file_title, form))
            r = self.cursor.fetchall()
            if r[0][0] != 0:
                return "A song with this file name and format already exists!"
            song_title = input("Song title:\t")
            artist = input("Artist:\t")
            data = input("Release date:\t")
            tags = input("Associated tags:\t")
            sql = "INSERT INTO songs (file_title, song_title, artist, form, data, tag) VALUES (%s, %s, %s, %s, %s, " \
                  "%s) "  # Insert song into database
            columns = (file_title, song_title, artist, form, data, tags)
            self.cursor.execute(sql, columns)
            self.cnx.commit()
            self.cursor.execute(
                "SELECT MAX(ID) FROM songs")
            result = self.cursor.fetchall()
            return "New song ID: " + str(result[0][0])
        else:
            return "Give valid path"

    def delete_song(self):
        """Remove song from database and from the storage directory based on ID"""
        song_id = tuple(input("Give the melody id to be deleted:\t"))
        sql = "SELECT file_title, form FROM songs WHERE id = %s"  # Check existence of song with given ID
        self.cursor.execute(sql, song_id)
        result = self.cursor.fetchall()
        if len(result) > 0:
            path = self.p_storage + "/" + result[0][0] + "." + result[0][
                1]  # Find path of song by appending the name and format to the storage directory path
            os.remove(path)  # Remove song from directory
            sql = "DELETE FROM songs WHERE id = %s"  # Delete song from database
            self.cursor.execute(sql, song_id)
            self.cnx.commit()
            print(self.cursor.rowcount, "record(s) deleted")
        else:
            print("Give a valid id...")

    def modify_data(self):
        """Modifies song info in the database"""
        song_id = tuple(input("Give the id of the song to be modified:\t"))  # Request song ID
        sql = "SELECT song_title, artist, data, tag FROM songs WHERE id = %s"  # Find song with given ID
        self.cursor.execute(sql, song_id)
        res = self.cursor.fetchall()
        if len(res) > 0:
            while True:
                sql = "SELECT song_title, artist, data, tag FROM songs WHERE id = %s"  # Save current info
                self.cursor.execute(sql, song_id)
                result = self.cursor.fetchall()
                modify = input(
                    "What do you want to modify? [title/artist/(release )date/tags/none]\t")  # Request data to be
                # modified
                if modify == 'title':  # Modify title
                    print('Current title is ' + result[0][0])
                    new = (input('Give new title:\t'), song_id[0])
                    sql = "UPDATE songs SET song_title = %s WHERE id = %s"
                    self.cursor.execute(sql, new)
                    self.cnx.commit()
                    print("New title assigned")
                if modify == 'artist':  # Modify artist
                    print('Current artist is ' + result[0][1])
                    new = (input('Give new artist:\t'), song_id[0])
                    sql = "UPDATE songs SET artist = %s WHERE id = %s"
                    self.cursor.execute(sql, new)
                    self.cnx.commit()
                    print("New artist assigned")
                if modify == 'date':  # Modify release date
                    print('Current date is ' + result[0][2])
                    new = (input('Give new date:\t'), song_id[0])
                    sql = "UPDATE songs SET data = %s WHERE id = %s"
                    self.cursor.execute(sql, new)
                    self.cnx.commit()
                    print("New date assigned")
                if modify == 'tags':  # Modify tags
                    print('Current tags are ' + result[0][3])
                    new = (input('Give new tags:\t'), song_id[0])
                    sql = "UPDATE songs SET tag = %s WHERE id = %s"
                    self.cursor.execute(sql, new)
                    self.cnx.commit()
                    print("New tags assigned")
                if modify == 'none':  # Do not modify anything, print the current song info
                    sql = "SELECT song_title, artist, data, tag FROM songs WHERE id = %s"
                    self.cursor.execute(sql, song_id)
                    result = self.cursor.fetchall()
                    print(
                        "Current data for the song with id" + song_id[0] + "are:\ntitle:" + result[0][0] + "\nartist:" +
                        result[0][1] + "\nrelease date:" + result[0][2] + "\ntags:" + result[0][3])
                    break
        else:
            print("Give a valid id...")

    def create_save_list(self):
        criteria, where = select()  # Get criteria wanted by the user and the mySQL where clause
        if len(criteria) == 0:  # Check if user has selected any criteria
            print("You haven't selected any criteria!")
            return
        sql = "SELECT file_title, form FROM songs WHERE " + where[0:len(
            where) - 4]  # Interrogate the database, remove the last ' and' at the end of the where clause
        self.cursor.execute(sql, criteria)
        result = self.cursor.fetchall()
        if len(result) == 0:  # Check if any song matches the wanted criteria
            print("No songs match your criteria")
            return
        while True:
            path = input("Give the path to the zip:\t")  # Request the path to the zip
            path = path.replace('\\', '/')
            if self.path_zip.match(path):  # Check if path leads to zip
                with ZipFile(path, 'w') as my_zip:
                    for song in result:
                        song_path = self.p_storage + "/" + song[0] + "." + song[1]
                        my_zip.write(song_path, basename(song_path))  # Copy melody to zip
                    my_zip.close()
                print("Songs added to specified zip file")
                break
            else:
                print("Give valid path")

    def search(self):
        criteria, where = select()  # Get criteria wanted by the user and the mySQL where clause
        if len(criteria) == 0:  # Check if user has selected any criteria
            print("You haven't selected any criteria!")
            return
        sql = "SELECT * FROM songs WHERE " + where[0:len(
            where) - 4]  # Interrogate the database, remove the last ' and' at the end of the where clause
        self.cursor.execute(sql, criteria)
        result = self.cursor.fetchall()
        if len(result) == 0:  # Check if any song matches the wanted criteria
            print("No songs match your criteria")
            return
        contor = 1
        for song in result:  # add the songs to the zip
            print("------------", contor, "------------")
            for field, name in zip(song, self.cursor.column_names):
                print(name, ":", field)
            contor += 1


tool = SongStorage()
tool.start_tool()
