import os
import shutil

from mutagen.easyid3 import EasyID3


# TODO this script is old, untested on latest Python/Mutagen
# TODO add tests and more comments
class MP3FileSorter:
    def __init__(self):
        self.DESTINATION = os.path.join(self.get_current_directory(), 'dest')
        self.SOURCE = os.path.join(self.get_current_directory(), 'source')
        
    def sort_from_source(self) -> None:
        self.sort_by_genre(self.SOURCE)
    
        for genre_name in os.listdir(self.DESTINATION):
            if genre_name not in ['None', 'Not MP3']:
                genre_path = os.path.join(self.DESTINATION, genre_name)
                self.sort_by_artist(genre_path)
    
                for artist_name in os.listdir(genre_path):
                    artist_path = os.path.join(genre_path, artist_name)
                    self.sort_by_album(artist_path)
    
    def sort_by_genre(self, directory: str):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            print('PROCESSING GENRE...', file_path)
    
            if file_path[-3:] != 'mp3':
                self.copy_to_folder('Not MP3', file_path)
    
            else:
                tags = EasyID3(file_path)
    
                if 'genre' in tags and tags['genre'] != '':
                    genre = tags['genre'][0].replace('/', ' ')
                    self.copy_to_folder(genre, file_path)
                else:
                    self.copy_to_folder('None', file_path)
    
    def sort_by_artist(self, directory: str):
        new_destination = os.path.join(self.DESTINATION, directory)
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            print('PROCESSING ARTIST...', file_path)
    
            try:
                tags = EasyID3(file_path)
            except Exception as error:
                print(error)
                continue
    
            if 'artist' in tags and tags['artist'] != '':
                artist = tags['artist'][0].replace('/', ' ')
                self.move_to_folder(new_destination, artist, file_path)
            elif 'albumartist' in tags and tags['albumartist'] != '':
                albumartist = tags['albumartist'][0].replace('/', ' ')
                self.move_to_folder(new_destination, albumartist, file_path)
            else:
                self.move_to_folder(new_destination, 'None', file_path)
    
    
    def sort_by_album(self, directory):
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            print('PROCESSING ALBUM...', file_path)
    
            try:
                tags = EasyID3(file_path)
            except Exception as error:
                print(error)
                continue
    
            if 'album' in tags and tags['album'] != '':
                album = tags['album'][0].replace('/', ' ')
                self.move_to_folder(directory, album, file_path)
            else:
                self.move_to_folder(directory, 'None', file_path)
    
    
    def get_current_directory(self) -> str:
        return os.path.dirname(os.path.realpath(__file__))
    
    
    def copy_to_folder(self, sub_folder: str, file_path: str) -> None:
        try:
            target = os.path.join(self.DESTINATION, sub_folder)
            if not os.path.exists(target):
                os.makedirs(target)
            shutil.copy2(file_path, target)
        except Exception:
            pass
    
    
    def move_to_folder(self, sub_folder: str, file_path: str):
        try:
            target = os.path.join(self.DESTINATION, sub_folder)
            if not os.path.exists(target):
                os.makedirs(target)
            shutil.move(file_path, target)
        except Exception:
            pass


if __name__ == "__main__":
    sorter = MP3FileSorter()
    sorter.sort_from_source()
