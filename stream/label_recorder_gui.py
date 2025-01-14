import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import random
import time
import csv
import os
import sys
import argparse
from webcam_streamer import WebcamStreamer

class GestureApp:
    SAVE_PATH = r"C:\Users\lhauptmann\Code\WristPPG2\data\labels"
    GESTURE_TIME_MAX = 1.0
    GESTURE_TIME_MIN = 1.4

    LETTER_GESTURES = {
        "a": "Swipe Forward",
        "b": "Swipe Backward",
        "c": "Swipe Left",
        "d": "Swipe Right",
        "p": "Fast Pinch",
        "prr": "Rotate Right",
        "prl": "Rotate Left",
        "pbd": "Back to Default",
        "pc": "Pinch Hold",
        "po": "Pinch Open",
        "sp": "Side Tap",
        "o": "Nothing",
        "s": "Knock"
    }

    LETTER_ICONS = {
        "a": "image",
        "b": "image",
        "c": "image",
        "d": "image",
        "p": "image",
        "prr": "image",
        "prl": "image",
        "pbd": "image",
        "pc": "image",
        "po": "image",
        "sp": "image",
        "o": "❌",
        "s": "👊"
    }

    IMAGE_PATH = r"C:\Users\lhauptmann\Code\WristPPG2\scripts\images"

    def __init__(self, root, file_index, repetition_mode=False, random_seed=42):
        self.root = root
        self.fname = os.path.join(self.SAVE_PATH, f'label_{file_index:03d}.csv')
        self.data_log = []
        self.letters = []
        self.past_letters = []
        self.repetition_mode = repetition_mode
        self.gesture_count = 0
        self.gesture_group_count = 0
        self.r_key_pressed = False
        self.random_seed = random_seed
        self.continue_flag = False
        self.use_webcam = use_webcam

        self.init_gui()
        self.init_csv()
        self.bind_keys()
        if self.use_webcam:
            self.init_webcam()
        self.running = False
        if self.random_seed is not None:
            random.seed(self.random_seed)

    def init_gui(self):
        self.root.title("Countdown & Letter Display")
        self.root.state('zoomed')

        self.image_label = tk.Label(self.root)
        self.image_label.place(relx=0.5, rely=0.5, anchor='center')

        self.label = tk.Label(self.root, text="", font=("Helvetica", 48))
        self.label.place(relx=0.5, rely=0.2, anchor='center')

        self.progress_bar = ttk.Progressbar(self.root, orient="horizontal", length=300, mode="determinate")
        self.progress_bar.place(relx=0.5, rely=0.8, anchor='center')

        self.start_button = tk.Button(self.root, text="Start", command=self.start_sequence, font=("Helvetica", 24), padx=5, pady=5)
        self.start_button.place(relx=0.5, rely=0.9, anchor='center')

        self.finish_button = tk.Button(self.root, text="Finish", command=self.finish_recording, font=("Helvetica", 24), padx=5, pady=5)
        self.finish_button.place(relx=0.5, rely=0.9, anchor='center')
        self.finish_button.place_forget()  # Initially hide the finish button

        self.key_pressed = tk.StringVar()
        
    def init_webcam(self):
        webcam_file_name = os.path.join(self.SAVE_PATH, f'webcam_{file_index:03d}.avi')
        self.webcam = WebcamStreamer(webcam_file_name, codec='MJPG', fps=30, resolution=(1280, 720))


    def bind_keys(self):
        self.root.bind('<KeyPress>', self.on_key_press)
        self.root.bind('<KeyRelease-r>', self.on_key_release_r)
        self.root.bind('<Delete>', self.delete_last)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_gesture_sequence(self):
        train_input_set = [['a']]*15 + [['b']]*15 + [['c']]*15 + [['d']]*15 + [["p"]] * 15 + [["sp"]] * 15 + [["pc", "po"]] * 5 + [["o"]] * 15 + [["pc", "prr", "po", "pbd"]] * 5 + [["pc", "prl", "po", "pbd"]] * 5
        test_input_set = [['a', 'a']]*8 + [['b', 'b']]*8 + [['c', 'c']]*8 + [['d', 'd']]*8 + [["p", "p"]] * 8 + [["sp", "sp"]] * 8 + [["p", "pc", "po"]] * 5 + [["o"]] * 15 + [["p", "pc", "prr", "po", "pbd"]] * 5 + [["p", "pc", "prl", "po", "pbd"]] * 5 + [["p", "pc", "po"]] * 5
        if self.repetition_mode:
            input_set = test_input_set
        else:
            input_set = train_input_set
        random.shuffle(input_set)
        return input_set[::-1]

    def countdown(self, seconds):
        self.image_label.config(image='', text='')
        for i in range(int(seconds), 0, -1):
            self.label.config(text=i, font=("Helvetica", 96))
            self.root.update()
            time.sleep(1)
        self.label.config(text="", image='')
        self.root.update()
        time.sleep(seconds - int(seconds))

    def show_letter(self, letter, waiting_time=None):
        gesture = self.LETTER_GESTURES[letter]
        print(f"Displaying letter: {letter} (",gesture.replace('\n', ' '),")")
        self.label.config(text=gesture, font=("Helvetica", 96))

        icon = self.LETTER_ICONS[letter]
        if icon == "image":
            try:
                img_path = os.path.join(self.IMAGE_PATH, f"{letter}.png")
                img = Image.open(img_path).resize((200, 200))
                img_tk = ImageTk.PhotoImage(img)
                self.image_label.config(image=img_tk)
                self.image_label.image = img_tk
            except Exception:
                self.image_label.config(image='')
        else:
            self.image_label.config(text=icon, image='', font=("Helvetica", 96))

        self.root.update()
        if self.use_webcam:
            self.webcam.display_text(gesture)
        if waiting_time == -1:
            self.root.wait_variable(self.key_pressed)
        else:
            if not waiting_time:
                waiting_time = random.uniform(self.GESTURE_TIME_MIN, self.GESTURE_TIME_MAX)
        
            time.sleep(waiting_time)
        if self.use_webcam:
            self.webcam.display_text("")

    def init_csv(self):
        
        if os.path.exists(self.fname):
            # if file is not empty
            with open(self.fname, 'r') as file:
                reader = csv.reader(file)
                if len(list(reader)) > 1:
                    raise FileExistsError(f"File {self.fname} already exists.")
        with open(self.fname, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['start_time', 'end_time', 'label'])

    def write_csv(self, data):
        with open(self.fname, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(data)

    def start_end_sequence(self):
        if self.running:
            self.finish_recording()
        else:
            self.start_sequence()
            
    def start_sequence(self):
        # Remove the start button after recording starts
        if self.use_webcam:
            self.webcam.start_recording()
            self.webcam.display_text("Start")
        self.running = True
        self.start_button.place_forget()
        start_entry = (time.time(), time.time(), "s")
        self.data_log = [start_entry]
        self.write_csv(self.data_log)
        total_letters = len(self.create_gesture_sequence())
        self.letters = self.create_gesture_sequence()
        self.progress_bar['maximum'] = total_letters
        
        self.countdown(5)

        while self.letters:
            self.continue_flag = False
            letter = self.letters.pop()
            self.past_letters.append(letter)
            self.gesture_group_count += 1   
            if not isinstance(letter, list):
                letter = [letter]
            for subletter in letter:
                start_time = time.time()
                self.show_letter(subletter)
                self.countdown(0.1)
                #entries.append((start_time, time.time(), subletter))
                if self.continue_flag:
                    self.continue_flag = False
                    break
                self.gesture_count += 1
                entry = (start_time, time.time(), subletter)
                self.data_log.append(entry)
                self.write_csv([entry])
            else:       
                self.progress_bar['value'] += 1
                self.root.update()

            if self.gesture_count >= 12 or not self.letters: # break every 12 gestures or when there are no more gestures to be shown
                self.show_break_message()
                if self.use_webcam:
                    self.webcam.display_text("Break")
                self.root.wait_variable(self.key_pressed)
                #if self.key_pressed.get() == 'r':
                #    self.r_key_pressed = True
                #    self.repeat_last_n(n=self.gesture_group_count)
                if self.use_webcam:
                    self.webcam.display_text("")
                self.gesture_count = 0
                self.gesture_group_count = 0
                self.countdown(0.1)

        self.show_negative_letter()
            
        # Show finish button after all gestures are shown        
        self.finish_button.place(relx=0.5, rely=0.9, anchor='center')

    def show_negative_letter(self):
        start_time = time.time()
        negative_gesture = "o"
        self.show_letter(negative_gesture, -1)

        entry = (start_time, time.time(), negative_gesture)
        self.data_log.append(entry)
        self.write_csv([entry])

    def show_break_message(self):
        self.label.config(text="Break", font=("Helvetica", 96))
        self.image_label.config(image='')
        self.root.update()

    def on_key_press(self, event):
        if event.char in ['s', 'r', 'k']:
            self.key_pressed.set(event.char)
            if event.char == 's':
                self.start_end_sequence()
            if event.char == "r" and not self.r_key_pressed:
                # repeat last n gestures
                self.r_key_pressed = True
                self.repeat_last_n()
                self.gesture_count = 0
                self.gesture_group_count = 0
                self.continue_flag = True
                if self.use_webcam:
                    self.webcam.display_text("Repeat")
                self.countdown(0.1)
                
    def on_key_release_r(self, event):
        self.r_key_pressed = False

            

    def repeat_last_n(self):
        n = self.gesture_group_count
        print(f"Repeating last {n} gestures.")
        
        letters_to_repeat = self.past_letters[-n:][::-1]
        self.past_letters = self.past_letters[:-n]
        self.letters = self.letters + letters_to_repeat
        n_single_letters = self.gesture_count
        if n_single_letters > 0:
        #print(f"Deletting {self.data_log[-n_single_letters:]}")
            self.data_log = self.data_log[:-n_single_letters]
            with open(self.fname, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['start_time', 'end_time', 'label'])
                writer.writerows(self.data_log)
        self.progress_bar['value'] -= len(letters_to_repeat)

    def delete_last(self, event=None):
        if self.data_log:
            last_entry = self.data_log.pop()
            with open(self.fname, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['start_time', 'end_time', 'label'])
                writer.writerows(self.data_log)
            self.progress_bar['value'] -= 1
            self.letters.append(last_entry[2])
            self.root.update()
            print(f"Last entry '{last_entry[2]}' deleted.")
        else:
            print("No more entries to delete.")
            
    def finish_recording(self):
        # Hide the finish button
        self.running = False
        self.finish_button.place_forget()
        if self.use_webcam:
            self.webcam.display_text("Finish")
        self.write_csv([(time.time(), time.time(), "s")])
        time.sleep(1)
        if self.use_webcam:
            self.end_webcam()
        self.root.destroy()

    def on_closing(self):
        self.running = False  # Stop any ongoing operations
        time.sleep(1)
        if self.use_webcam:
            self.end_webcam()  # Ensure webcam resources are released
        try:
            if self.root.winfo_exists():  # Check if root window exists
                self.root.destroy()  # Destroy the root window
        except Exception as e:
            print(f"Error during closing: {e}")
        
    def end_webcam(self):
        self.webcam.stop_recording()
        self.webcam.save_timestamps()
        self.webcam.stop_streaming()
        self.webcam.release_camera()

use_webcam = True
def parse_args():
    parser = argparse.ArgumentParser(description="Gesture recording application.")
    parser.add_argument(
        "file_index",
        type=int,
        help="Index of the file to process"
    )
    parser.add_argument(
        "--rep",
        action="store_true",
        help="Enable repetition mode"
    )
    
    parser.add_argument(
        "--random_seed",
        type=int,
        default=None,
    )

    return parser.parse_args()

if __name__ == "__main__":
    try:
        args = parse_args()
        file_index = args.file_index
        repetition_mode = args.rep
        random_seed = args.random_seed
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    root = tk.Tk()
    app = GestureApp(root, file_index, repetition_mode=repetition_mode, random_seed=random_seed)
    root.mainloop()