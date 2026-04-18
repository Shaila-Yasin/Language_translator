import tkinter as tk
from tkinter import ttk, messagebox
import speech_recognition as sr
from googletrans import Translator, LANGUAGES
from gtts import gTTS
from playsound import playsound
import tempfile
import threading
import os
import html
import time

#  Initialize translator
translator_client = Translator()

#  Supported languages (At least 15)
LANG_CODES = {
    "Auto Detect": "auto",
    "English": "en",
    "Urdu": "ur",
    "Hindi": "hi",
    "Arabic": "ar",
    "Chinese (Simplified)": "zh-cn",
    "Chinese (Traditional)": "zh-tw",
    "French": "fr",
    "German": "de",
    "Spanish": "es",
    "Italian": "it",
    "Russian": "ru",
    "Portuguese": "pt",
    "Japanese": "ja",
    "Korean": "ko",
    "Turkish": "tr",
    "Dutch": "nl",
    "Indonesian": "id",
    "Thai": "th",
    "Vietnamese": "vi"
}

# Invert dictionary for code lookup if needed, but we mostly use values
#  History storage
history_list = []

class TranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🌸 Voice Translator 🌸")
        self.root.geometry("600x750")
        self.root.config(bg="#ffe6f2")
        
        self.setup_styles()
        self.create_widgets()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Button Style
        self.style.configure("TButton",
                        font=("Comic Sans MS", 10, "bold"),
                        foreground="#fff",
                        background="#ff66b2",
                        padding=8)
        self.style.map("TButton",
                  background=[("active", "#ff80bf"), ("pressed", "#ff4da6")])

        # Combobox Style
        self.style.configure("CustomCombobox.TCombobox",
                        fieldbackground="white",
                        background="#ffe6f2",
                        foreground="#ff1493",
                        arrowcolor="#ff66b2",
                        font=("Comic Sans MS", 10))
        self.style.map("CustomCombobox.TCombobox",
                  fieldbackground=[('readonly', 'white')],
                  background=[('readonly', '#ffe6f2')],
                  foreground=[('readonly', '#ff1493')],
                  selectbackground=[('readonly', 'white')],
                  selectforeground=[('readonly', '#ff1493')])

    def create_widgets(self):
        #  Main Frame
        frame = tk.Frame(self.root, bg="#ffe6f2")
        frame.pack(padx=20, pady=10, fill="both", expand=True)

        #  Heading
        tk.Label(frame, text="✨ Language Translator ✨",
                 font=("Comic Sans MS", 16, "bold"),
                 bg="#ffe6f2", fg="#ff1493").pack(pady=5)

        #  Input Language Selection
        tk.Label(frame, text="Select Input Language:",
                 font=("Comic Sans MS", 11, "bold"),
                 bg="#ffe6f2", fg="#ff3385").pack(anchor="w", padx=10)
        
        self.input_lang_var = tk.StringVar(value="Auto Detect")
        self.input_lang_combo = ttk.Combobox(frame, textvariable=self.input_lang_var,
                                        values=list(LANG_CODES.keys()),
                                        font=("Comic Sans MS", 10),
                                        state="readonly",
                                        style="CustomCombobox.TCombobox")
        self.input_lang_combo.pack(pady=5, fill="x", padx=10)

        #  Input Text Area
        tk.Label(frame, text="Enter text or speak:",
                 font=("Comic Sans MS", 11, "bold"),
                 bg="#ffe6f2", fg="#ff3385").pack(anchor="w", padx=10)

        self.input_text = tk.Text(frame, height=5, width=50,
                             font=("Comic Sans MS", 10),
                             bd=3, relief="groove")
        self.input_text.pack(pady=5, padx=10)

        #  Controls (Record / Translate)
        btn_frame = tk.Frame(frame, bg="#ffe6f2")
        btn_frame.pack(pady=10)

        self.make_button(btn_frame, "🎤 Record Voice", lambda: threading.Thread(target=self.record_speech).start())
        self.make_button(btn_frame, "💬 Translate Text", self.translate_text)

        #  Target Language Selection
        tk.Label(frame, text="Select Target Language:",
                 font=("Comic Sans MS", 11, "bold"),
                 bg="#ffe6f2", fg="#ff3385").pack(anchor="w", padx=10)

        self.target_lang_var = tk.StringVar(value="English")
        self.target_lang_combo = ttk.Combobox(frame, textvariable=self.target_lang_var,
                                         values=[k for k in LANG_CODES.keys() if k != "Auto Detect"],
                                         font=("Comic Sans MS", 10),
                                         state="readonly",
                                         style="CustomCombobox.TCombobox")
        self.target_lang_combo.pack(pady=5, fill="x", padx=10)

        #  Translation Output
        tk.Label(frame, text="Translation:",
                 font=("Comic Sans MS", 11, "bold"),
                 bg="#ffe6f2", fg="#ff3385").pack(anchor="w", padx=10)

        self.bubble_frame = tk.Frame(frame, bg="#ff66b2", bd=4, relief="ridge")
        self.bubble_frame.pack(pady=5, padx=10, fill="both", expand=True)

        self.translated_text_var = tk.StringVar()
        self.output_label = tk.Label(self.bubble_frame, textvariable=self.translated_text_var,
                                wraplength=480, bg="white", fg="#ff1493",
                                font=("Comic Sans MS", 11, "italic"),
                                justify="center", width=40, height=8)
        self.output_label.pack(fill="both", expand=True, padx=2, pady=2)

        #  Output Controls (Speak / History)
        out_btn_frame = tk.Frame(frame, bg="#ffe6f2")
        out_btn_frame.pack(pady=10)

        self.make_button(out_btn_frame, "🔊 Speak Translation", lambda: threading.Thread(target=self.speak_translation).start())
        self.make_button(out_btn_frame, "📜 View History", self.show_history)

    def make_button(self, parent, text, command):
        btn = tk.Button(parent, text=text, command=command,
                        font=("Comic Sans MS", 10, "bold"),
                        fg="white", bg="#ff66b2",
                        activebackground="#ff80bf",
                        relief="flat", bd=0,
                        padx=15, pady=5, cursor="hand2")
        btn.pack(side="left", padx=5)
        btn.bind("<Enter>", lambda e: btn.config(bg="#ff4da6"))
        btn.bind("<Leave>", lambda e: btn.config(bg="#ff66b2"))
        return btn

    def record_speech(self):
        recognizer = sr.Recognizer()
        # Auto-detect logic for STT is hard with SR library as it defaults to English or main system lang usually
        # But we can try to pass the selected input language if it's not Auto
        input_lang_name = self.input_lang_var.get()
        lang_code = LANG_CODES.get(input_lang_name)
        
        # Mapping simple codes to BCP-47 for SpeechRecognition if possible, 
        # but Google recognizer handles mainly standard codes.
        # "auto" is not valid for SR, so default to None (en-US) or user choice
        sr_lang = None
        if lang_code and lang_code != "auto":
            sr_lang = lang_code 

        with sr.Microphone() as source:
            self.root.after(0, lambda: messagebox.showinfo("Recording", "🎙 Speak now..."))
            try:
                # recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.listen(source, timeout=8, phrase_time_limit=10)
                try:
                    text = recognizer.recognize_google(audio, language=sr_lang)
                    self.root.after(0, lambda: self.update_input_text(text))
                except sr.UnknownValueError:
                    self.root.after(0, lambda: messagebox.showerror("Error", "Could not understand audio"))
                except sr.RequestError as e:
                    self.root.after(0, lambda: messagebox.showerror("Error", f"Could not request results; {e}"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Recording error: {e}"))

    def update_input_text(self, text):
        self.input_text.delete("1.0", tk.END)
        self.input_text.insert(tk.END, text)

    def translate_text(self):
        text = self.input_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Warning", "Please enter text to translate!")
            return

        target_name = self.target_lang_var.get()
        target_code = LANG_CODES.get(target_name, "en")
        
        input_name = self.input_lang_var.get()
        input_code = LANG_CODES.get(input_name, "auto")

        try:
            # If input is auto, src='auto' (default)
            # If input is specified, src=input_code
            if input_code == "auto":
                translated = translator_client.translate(text, dest=target_code)
            else:
                translated = translator_client.translate(text, src=input_code, dest=target_code)
            
            result_text = translated.text
            self.translated_text_var.set(html.escape(result_text))
            
            # Add to history
            history_item = {
                "original": text,
                "translated": result_text,
                "src_lang": translated.src,
                "dest_lang": target_name,
                "timestamp": time.strftime("%H:%M:%S")
            }
            history_list.append(history_item)
            
        except Exception as e:
            messagebox.showerror("Error", f"Translation failed: {e}")

    def speak_translation(self):
        text = self.translated_text_var.get()
        if not text:
            messagebox.showwarning("Warning", "No translated text found!")
            return
        
        target_name = self.target_lang_var.get()
        lang_code = LANG_CODES.get(target_name, "en")
        
        try:
            tts = gTTS(text=text, lang=lang_code)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                temp_filename = fp.name
                tts.save(temp_filename)
            
            playsound(temp_filename)
            try:
                os.remove(temp_filename)
            except:
                pass 
        except Exception as e:
            messagebox.showerror("Error", f"TTS Error: {e}")

    def show_history(self):
        if not history_list:
            messagebox.showinfo("History", "No translations yet!")
            return
            
        history_window = tk.Toplevel(self.root)
        history_window.title("📜 Translation History")
        history_window.geometry("600x450")
        history_window.config(bg="#ffe6f2")
        
        tk.Label(history_window, text="Translation History",
                 font=("Comic Sans MS", 14, "bold"), bg="#ffe6f2",
                 fg="#ff1493").pack(pady=10)
        
        history_box = tk.Text(history_window, width=70, height=20,
                              font=("Comic Sans MS", 10), bg="white",
                              fg="#ff1493", bd=3, relief="groove")
        history_box.pack(padx=10, pady=10)
        
        for item in history_list:
            history_box.insert(tk.END, f"[{item['timestamp']}] {item['src_lang']} -> {item['dest_lang']}\n")
            history_box.insert(tk.END, f"In:  {item['original']}\n")
            history_box.insert(tk.END, f"Out: {item['translated']}\n")
            history_box.insert(tk.END, "-"*50 + "\n")
            
        history_box.config(state="disabled")

def main():
    root = tk.Tk()
    app = TranslatorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()