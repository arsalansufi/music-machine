from music_machine import audio_info_extractor

extractor = audio_info_extractor.AudioInfoExtractor('config.yml')
yellow = extractor.get_audio_file('Yellow.mp3')
