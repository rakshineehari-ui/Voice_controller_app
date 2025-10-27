import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import pygame
import pyttsx3
import speech_recognition as sr
import threading
import webbrowser
import random
import time

# Initialize pygame mixer
pygame.mixer.init()

# Initialize text-to-speech engine
engine = pyttsx3.init()
engine.setProperty('rate', 150)

# Emergency contact (replace with actual emergency number)
EMERGENCY_CONTACT = "tel:+91 9629618017"

class VoiceControlledSmartHome:
    def __init__(self, root):
        self.root = root
        self.root.title("Voice Controlled Smart Home with Emotional Support")
        self.window_width = 1000
        self.window_height = 700
        self.root.geometry(f"{self.window_width}x{self.window_height}")
        self.root.configure(bg='#0a192f')

        self.assets_path = "assets"
        self.music_folder = os.path.join("music", "Aashiqui")

        # State variables
        self.light_on = False
        self.fan_on = False
        self.music_on = False
        self.emotion_state = "neutral"
        self.conversation_active = False
        self.emergency_triggered = False

        # Music playlist
        self.music_playlist = []
        self.current_track = 0

        # Emotional support messages
        self.supportive_messages = [
            "I'm here for you. Would you like to talk about what's bothering you?",
            "You're not alone. I'm always here to listen to you.",
            "It's okay to feel sad sometimes. Remember that this feeling will pass.",
            "Would you like me to play some calming music to help you feel better?",
            "I care about how you're feeling. Is there anything I can do to help?"
        ]

        # Load images
        self.images = {}
        self.load_assets()

        # Load music
        self.load_music_playlist()

        # Build UI
        self.create_ui()

        # Initialize voice recognition
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.is_listening = True

        # Start voice listener thread
        self.listening_thread = threading.Thread(target=self.listen_commands)
        self.listening_thread.daemon = True
        self.listening_thread.start()

        # Welcome message
        self.root.after(1000, lambda: self.speak("Welcome! Say 'light on', 'play music', or 'help' for commands."))

    def load_assets(self):
        """Load all assets with error handling"""
        try:
            size = 120
            device_icons = {
                'light_on': 'bulb_on.png',
                'light_off': 'bulb_off.png',
                'fan_on': 'fan_on.png',
                'fan_off': 'fan_off.png',
                'music_on': 'music_on.png',
                'music_off': 'music_off.png'
            }

            for key, filename in device_icons.items():
                path = os.path.join(self.assets_path, filename)
                if os.path.exists(path):
                    img = Image.open(path)
                    img = img.resize((size, size), Image.Resampling.LANCZOS)
                    self.images[key] = ImageTk.PhotoImage(img)
                else:
                    # Create placeholder
                    emoji = '💡' if 'light' in key else '🌀' if 'fan' in key else '🎵'
                    self.images[key] = self.create_emoji_image(emoji, size, 'on' if 'on' in key else 'off')

            # Emotion icons
            emotion_size = 60
            emotions = {'happy': '😊', 'sad': '😔', 'stressed': '😫', 'neutral': '😐'}
            for emotion, emoji in emotions.items():
                self.images[emotion] = self.create_emoji_image(emoji, emotion_size, emotion)

        except Exception as e:
            print(f"Error loading assets: {e}")

    def create_emoji_image(self, emoji, size, state):
        """Create an image with emoji"""
        img = Image.new('RGB', (size, size), color='#112240')
        from PIL import ImageDraw, ImageFont
        
        d = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", size-20)
        except:
            font = ImageFont.load_default()
        
        colors = {'on': '#64ffda', 'off': '#ff6b6b', 'happy': '#64ffda', 
                 'sad': '#4fc3f7', 'stressed': '#ff9800', 'neutral': '#8892b0'}
        
        d.text((size//2, size//2), emoji, font=font, 
               fill=colors.get(state, '#64ffda'), anchor="mm")
        return ImageTk.PhotoImage(img)

    def load_music_playlist(self):
        """Load music files from Aashiqui folder"""
        if os.path.exists(self.music_folder):
            for file in os.listdir(self.music_folder):
                if file.lower().endswith(('.mp3', '.wav', '.m4a')):
                    full_path = os.path.join(self.music_folder, file)
                    self.music_playlist.append({
                        'path': full_path,
                        'name': os.path.splitext(file)[0].replace('-', ' ').replace('_', ' ')
                    })
        
        if not self.music_playlist:
            self.music_playlist = [
                {'path': '', 'name': 'Tum Hi Ho - Aashiqui'},
                {'path': '', 'name': 'Sunn Raha Hai - Aashiqui'}
            ]

    def create_ui(self):
        """Create the user interface"""
        # Title
        title_label = tk.Label(self.root, text="Voice Controlled Smart Home", 
                              font=("Arial", 24, "bold"), fg="#64ffda", bg="#0a192f")
        title_label.pack(pady=10)

        # Status frame
        status_frame = tk.Frame(self.root, bg="#112240", relief="ridge", bd=2)
        status_frame.pack(pady=10, padx=20, fill="x")

        # Emotion status
        emotion_frame = tk.Frame(status_frame, bg="#112240")
        emotion_frame.pack(side="left", padx=20, pady=10)

        tk.Label(emotion_frame, text="Status:", font=("Arial", 12, "bold"), 
                fg="#64ffda", bg="#112240").pack()

        self.emotion_icon = tk.Label(emotion_frame, image=self.images['neutral'], bg="#112240")
        self.emotion_icon.pack()

        self.emotion_label = tk.Label(emotion_frame, text="Ready", font=("Arial", 12), 
                                     fg="#8892b0", bg="#112240")
        self.emotion_label.pack()

        # Device controls frame
        devices_frame = tk.Frame(self.root, bg="#0a192f")
        devices_frame.pack(pady=20)

        # Light control
        self.light_frame = tk.Frame(devices_frame, bg="#112240", relief="ridge", bd=2)
        self.light_frame.grid(row=0, column=0, padx=10, pady=10)

        tk.Label(self.light_frame, text="Light", font=("Arial", 16), 
                fg="#e6f1ff", bg="#112240").pack(pady=5)

        self.light_label = tk.Label(self.light_frame, image=self.images['light_off'], bg="#112240")
        self.light_label.pack(pady=5)

        self.light_status = tk.Label(self.light_frame, text="OFF", font=("Arial", 12), 
                                    fg="#ff6b6b", bg="#112240")
        self.light_status.pack(pady=5)

        # Fan control
        self.fan_frame = tk.Frame(devices_frame, bg="#112240", relief="ridge", bd=2)
        self.fan_frame.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(self.fan_frame, text="Fan", font=("Arial", 16), 
                fg="#e6f1ff", bg="#112240").pack(pady=5)

        self.fan_label = tk.Label(self.fan_frame, image=self.images['fan_off'], bg="#112240")
        self.fan_label.pack(pady=5)

        self.fan_status = tk.Label(self.fan_frame, text="OFF", font=("Arial", 12), 
                                  fg="#ff6b6b", bg="#112240")
        self.fan_status.pack(pady=5)

        # Music control
        self.music_frame = tk.Frame(devices_frame, bg="#112240", relief="ridge", bd=2)
        self.music_frame.grid(row=0, column=2, padx=10, pady=10)

        tk.Label(self.music_frame, text="Music", font=("Arial", 16), 
                fg="#e6f1ff", bg="#112240").pack(pady=5)

        self.music_label = tk.Label(self.music_frame, image=self.images['music_off'], bg="#112240")
        self.music_label.pack(pady=5)

        self.music_status = tk.Label(self.music_frame, text="OFF", font=("Arial", 12), 
                                    fg="#ff6b6b", bg="#112240")
        self.music_status.pack(pady=5)

        # Manual controls frame
        manual_frame = tk.Frame(self.root, bg="#0a192f")
        manual_frame.pack(pady=10)

        tk.Button(manual_frame, text="Light On", command=lambda: self.toggle_light(),
                 bg="#64ffda", fg="#0a192f", font=("Arial", 12)).grid(row=0, column=0, padx=5)

        tk.Button(manual_frame, text="Light Off", command=lambda: self.toggle_light(),
                 bg="#ff6b6b", fg="white", font=("Arial", 12)).grid(row=0, column=1, padx=5)

        tk.Button(manual_frame, text="Music On", command=lambda: self.toggle_music(),
                 bg="#64ffda", fg="#0a192f", font=("Arial", 12)).grid(row=0, column=2, padx=5)

        tk.Button(manual_frame, text="Music Off", command=lambda: self.toggle_music(),
                 bg="#ff6b6b", fg="white", font=("Arial", 12)).grid(row=0, column=3, padx=5)

        tk.Button(manual_frame, text="🚨 Emergency", command=self.trigger_emergency,
                 bg="#ff0000", fg="white", font=("Arial", 12, "bold")).grid(row=0, column=4, padx=5)

        # Music player
        player_frame = tk.Frame(self.root, bg="#112240", relief="ridge", bd=2)
        player_frame.pack(pady=10, padx=20, fill="x")

        self.now_playing = tk.Label(player_frame, text="Say 'play music' to start", 
                                   font=("Arial", 12), fg="#e6f1ff", bg="#112240")
        self.now_playing.pack(pady=10)

        # Voice command display
        self.voice_display = tk.Label(self.root, text="Listening for commands...", 
                                     font=("Arial", 14), fg="#e6f1ff", bg="#112240",
                                     width=60, height=2, relief="ridge", bd=2)
        self.voice_display.pack(pady=10)

        # Commands guide
        guide_frame = tk.Frame(self.root, bg="#112240", relief="ridge", bd=2)
        guide_frame.pack(pady=10, padx=20, fill="x")

        commands = [
            "🎯 Voice Commands:",
            "• 'Light on' / 'Light off' - Control lights",
            "• 'Fan on' / 'Fan off' - Control fan", 
            "• 'Play music' / 'Stop music' - Control music",
            "• 'Emergency' - Call for help",
            "• 'I am sad' - Emotional support",
            "• 'Help' - Show commands"
        ]
        
        for command in commands:
            tk.Label(guide_frame, text=command, font=("Arial", 11), 
                    fg="#e6f1ff", bg="#112240", justify="left").pack(anchor="w", padx=20, pady=2)

    def toggle_light(self):
        """Toggle light on/off"""
        self.light_on = not self.light_on
        image_to_use = self.images['light_on'] if self.light_on else self.images['light_off']
        self.light_label.config(image=image_to_use)
        self.light_status.config(text="ON" if self.light_on else "OFF", 
                                fg="#64ffda" if self.light_on else "#ff6b6b")
        self.speak("Light turned on" if self.light_on else "Light turned off")

    def toggle_fan(self):
        """Toggle fan on/off"""
        self.fan_on = not self.fan_on
        image_to_use = self.images['fan_on'] if self.fan_on else self.images['fan_off']
        self.fan_label.config(image=image_to_use)
        self.fan_status.config(text="ON" if self.fan_on else "OFF", 
                              fg="#64ffda" if self.fan_on else "#ff6b6b")
        self.speak("Fan turned on" if self.fan_on else "Fan turned off")

    def toggle_music(self):
        """Toggle music on/off - SIMPLIFIED"""
        if not self.music_on:
            # Turn music ON
            self.music_on = True
            if self.music_playlist:
                track = self.music_playlist[self.current_track]
                try:
                    if os.path.exists(track['path']):
                        pygame.mixer.music.load(track['path'])
                        pygame.mixer.music.play(-1)
                    self.now_playing.config(text=f"Playing: {track['name']}")
                except:
                    self.now_playing.config(text=f"Simulating: {track['name']}")
            
            self.music_label.config(image=self.images['music_on'])
            self.music_status.config(text="ON", fg="#64ffda")
            self.speak("Music started")
        else:
            # Turn music OFF
            self.music_on = False
            pygame.mixer.music.stop()
            self.music_label.config(image=self.images['music_off'])
            self.music_status.config(text="OFF", fg="#ff6b6b")
            self.now_playing.config(text="Music stopped")
            self.speak("Music stopped")

    def trigger_emergency(self):
        """Trigger emergency protocol"""
        if not self.emergency_triggered:
            self.emergency_triggered = True
            self.speak("Emergency! Calling for help in 5 seconds.")
            
            # Countdown
            for i in range(5, 0, -1):
                self.voice_display.config(text=f"EMERGENCY: Calling in {i} seconds...")
                time.sleep(1)
            
            try:
                webbrowser.open(EMERGENCY_CONTACT)
                messagebox.showwarning("EMERGENCY", "Help is on the way!")
            except:
                self.speak("Please call emergency services manually!")
            
            self.emergency_triggered = False
            self.voice_display.config(text="Emergency call completed")

    def speak(self, text):
        """Speak text using text-to-speech"""
        self.voice_display.config(text=text)
        try:
            engine.say(text)
            engine.runAndWait()
        except:
            print(f"Speech: {text}")

    def listen_commands(self):
        """Improved voice command listener"""
        time.sleep(2)  # Wait for initialization
        
        try:
            self.microphone = sr.Microphone()
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("🎤 Microphone ready")
        except Exception as e:
            print(f"❌ Microphone error: {e}")
            self.voice_display.config(text="Microphone not available - Use manual buttons")
            return

        while self.is_listening:
            try:
                with self.microphone as source:
                    self.voice_display.config(text="🎤 Listening... Speak now")
                    audio = self.recognizer.listen(source, timeout=8, phrase_time_limit=5)
                
                command = self.recognizer.recognize_google(audio).lower()
                print(f"🎯 You said: {command}")
                self.process_voice_command(command)
                
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                self.voice_display.config(text="❓ Could not understand audio")
            except sr.RequestError as e:
                self.voice_display.config(text="🌐 Internet required for voice commands")
            except Exception as e:
                print(f"Voice error: {e}")
            
            time.sleep(1)

    def process_voice_command(self, command):
        """Process voice commands - SIMPLIFIED AND IMPROVED"""
        self.voice_display.config(text=f"🎯 Command: {command}")
        
        # Simple command matching - much more reliable
        command_lower = command.lower()
        
        # Light commands
        if any(word in command_lower for word in ["light on", "turn on light", "switch on light"]):
            if not self.light_on:
                self.toggle_light()
                
        elif any(word in command_lower for word in ["light off", "turn off light", "switch off light"]):
            if self.light_on:
                self.toggle_light()
                
        elif "light" in command_lower:
            self.toggle_light()  # Toggle if just "light"
        
        # Fan commands
        elif any(word in command_lower for word in ["fan on", "turn on fan"]):
            if not self.fan_on:
                self.toggle_fan()
                
        elif any(word in command_lower for word in ["fan off", "turn off fan"]):
            if self.fan_on:
                self.toggle_fan()
                
        elif "fan" in command_lower:
            self.toggle_fan()
        
        # Music commands
        elif any(word in command_lower for word in ["play music", "music on", "start music"]):
            if not self.music_on:
                self.toggle_music()
                
        elif any(word in command_lower for word in ["stop music", "music off", "end music"]):
            if self.music_on:
                self.toggle_music()
                
        elif "music" in command_lower:
            self.toggle_music()
        
        # Emergency commands
        elif any(word in command_lower for word in ["emergency", "help", "save me", "accident"]):
            self.trigger_emergency()
        
        # Emotional support
        elif any(word in command_lower for word in ["sad", "unhappy", "depressed", "lonely"]):
            self.speak("I'm here for you. Would you like to talk about what's bothering you?")
        
        # Help command
        elif "help" in command_lower:
            help_text = "Say: Light on, Play music, Emergency, or I'm sad"
            self.speak(help_text)
        
        else:
            self.speak("Try: Light on, Play music, or Emergency")

    def __del__(self):
        """Cleanup"""
        self.is_listening = False
        if self.microphone:
            self.microphone = None


def main():
    root = tk.Tk()
    app = VoiceControlledSmartHome(root)
    
    def on_closing():
        app.is_listening = False
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()