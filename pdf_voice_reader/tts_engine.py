import threading
import queue
import time

class TTSEngine:
    def __init__(self):
        self.is_playing = False
        self.is_paused = False

        self.on_word_callback = None
        self.on_finish_callback = None

        self._command_queue = queue.Queue()
        self._speech_thread = threading.Thread(target=self._tts_worker, daemon=True)
        self._speech_thread.start()

        # We need a synchronous way to get available voices initially,
        # but pyttsx3 should ideally be initialized in the worker thread.
        # To avoid COM errors on Windows, we do everything pyttsx3-related in the worker.
        self._available_voices = []
        self._default_voice_id = None

        # Request initial setup
        self._command_queue.put(('setup', None))

        # We'll need to wait briefly for setup to finish so voices are populated
        time.sleep(0.5)

    def _tts_worker(self):
        """Dedicated thread for all pyttsx3 operations to avoid COM errors on Windows."""
        import pyttsx3
        try:
            self.engine = pyttsx3.init()
        except Exception:
            # Fallback if init fails (e.g., in CI environments)
            self.engine = None

        if self.engine:
            self.engine.connect('started-word', self._on_word)
            self.engine.connect('finished-utterance', self._on_finish)

        current_rate = 150

        while True:
            try:
                # Check for commands non-blocking while playing, blocking when idle
                cmd, args = self._command_queue.get(block=True, timeout=0.1)

                if not self.engine:
                    self._command_queue.task_done()
                    continue

                if cmd == 'setup':
                    self.engine.setProperty('rate', current_rate)
                    self._setup_spanish_voice()

                    voices = self.engine.getProperty('voices')
                    self._available_voices = [(v.id, v.name) for v in voices]
                    self._default_voice_id = self.engine.getProperty('voice')

                elif cmd == 'speak':
                    text = args
                    chunks = self._chunk_text(text)
                    self.is_playing = True
                    self.is_paused = False

                    for chunk in chunks:
                        if not self.is_playing:
                            break

                        # Handle pausing
                        while self.is_paused and self.is_playing:
                            # Process any incoming commands while paused (like 'stop' or 'resume')
                            try:
                                sub_cmd, sub_args = self._command_queue.get_nowait()
                                if sub_cmd == 'stop':
                                    self.is_playing = False
                                    self.is_paused = False
                                elif sub_cmd == 'resume':
                                    self.is_paused = False
                                elif sub_cmd == 'set_rate':
                                    self.engine.setProperty('rate', sub_args)
                                    current_rate = sub_args
                                elif sub_cmd == 'set_voice':
                                    self.engine.setProperty('voice', sub_args)
                                self._command_queue.task_done()
                            except queue.Empty:
                                pass
                            time.sleep(0.1)

                        if not self.is_playing:
                            break

                        self.engine.say(chunk)
                        try:
                            self.engine.runAndWait()
                        except RuntimeError:
                            pass

                    self.is_playing = False
                    if self.on_finish_callback:
                        # True indicates finished all chunks naturally
                        # False indicates it was stopped
                        self.on_finish_callback(True)

                elif cmd == 'stop':
                    self.is_playing = False
                    self.is_paused = False
                    self.engine.stop()

                elif cmd == 'pause':
                    self.is_paused = True

                elif cmd == 'resume':
                    self.is_paused = False

                elif cmd == 'set_voice':
                    self.engine.setProperty('voice', args)

                elif cmd == 'set_rate':
                    self.engine.setProperty('rate', args)
                    current_rate = args

                elif cmd == 'quit':
                    break

                self._command_queue.task_done()

            except queue.Empty:
                pass
            except Exception as e:
                print(f"TTS Worker Error: {e}")

    def _setup_spanish_voice(self):
        voices = self.engine.getProperty('voices')
        spanish_voices = []
        for voice in voices:
            if any('es' in str(lang).lower() for lang in voice.languages) or \
               'spanish' in voice.name.lower() or 'español' in voice.name.lower() or \
               'es-es' in voice.id.lower() or 'es-mx' in voice.id.lower():
                spanish_voices.append(voice)

        if spanish_voices:
            helena = next((v for v in spanish_voices if 'helena' in v.name.lower()), None)
            if helena:
                self.engine.setProperty('voice', helena.id)
            else:
                self.engine.setProperty('voice', spanish_voices[0].id)

    def get_available_voices(self):
        """Returns a list of available voices (id, name)."""
        # Return the cached voices populated during setup
        return self._available_voices

    def get_default_voice(self):
        return self._default_voice_id

    def set_voice(self, voice_id):
        self._command_queue.put(('set_voice', voice_id))

    def set_rate(self, rate):
        self._command_queue.put(('set_rate', rate))

    def set_callbacks(self, on_word=None, on_finish=None):
        self.on_word_callback = on_word
        self.on_finish_callback = on_finish

    def _on_word(self, name, location, length):
        if self.on_word_callback:
            self.on_word_callback(location, length)

    def _on_finish(self, name, completed):
        pass

    def _chunk_text(self, text):
        import re
        parts = re.split(r'([.!?;\n]+)', text)
        chunks = []
        current_chunk = ""
        for part in parts:
            current_chunk += part
            if re.search(r'[.!?;\n]', part):
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = ""

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        final_chunks = []
        max_len = 200
        for chunk in chunks:
            if len(chunk) > max_len:
                words = chunk.split()
                temp = ""
                for word in words:
                    if len(temp) + len(word) > max_len:
                        final_chunks.append(temp.strip())
                        temp = word + " "
                    else:
                        temp += word + " "
                if temp.strip():
                    final_chunks.append(temp.strip())
            else:
                final_chunks.append(chunk)

        return final_chunks

    def speak(self, text):
        # Stop any current speech
        self.stop()
        self._command_queue.put(('speak', text))

    def pause(self):
        self._command_queue.put(('pause', None))

    def resume(self):
        self._command_queue.put(('resume', None))

    def stop(self):
        # We need to clear the queue of pending speak commands
        # A simpler way is just to send a stop command which the worker will process.
        self._command_queue.put(('stop', None))

    def quit(self):
        self._command_queue.put(('quit', None))
        if self._speech_thread and self._speech_thread.is_alive():
            self._speech_thread.join(timeout=2.0)
