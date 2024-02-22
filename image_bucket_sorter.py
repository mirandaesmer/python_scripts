import os

from PIL import Image, ImageTk, ImageFile
from shutil import copy2
from string import ascii_letters, digits
from tkinter import messagebox, StringVar, ttk, Tk
from typing import Dict, List

# Bucket defaults
DEFAULT_AMOUNT = 3
VALID_IMAGE_EXTENSIONS = [".png", ".jpg", ".jpeg"]
CONFIG_FILE_NAME = "image_bucket_sort_config.txt"  # For faster processing

# Label strings
TITLE_STR = "IMAGE BUCKET SORTER"
AMOUNT_INSTR_STR = "Amount of Buckets (2 to 9)"
NAMING_INSTR_STR = "Unique Names (only ascii, numbers and underscores)"

# Button strings
AMOUNT_BUTTON_STR = "Continue"
NAME_BUTTON_STR = "Bucket Sort"
EXIT_BUTTON_STR = "Exit"
CONFIRM_COPY_BUTTON_STR = "Confirm File Copy"

# Error Strings
HEADER_ERR = 'Error'
FILES_NOT_FOUND_ERR = 'No image files in target directory: '

# Results Strings
FILES_COPIED_STR = ' files copied!'
ERRS_CAPTURED_STR = ' errors captured!'

# Filters
VALID_NAME_CHARS = list(digits) + list(ascii_letters) + ['_']
IMG_MAX_HEIGHT = 900
IMG_MAX_WIDTH = 1850


class ImageBucketSorter:
    """
    Simple Tkinter keyboard-based image bucket sorting tool.
    
    NOTE: Only uses COPY operations in order to avoid file losses
    NOTE: Prioritizes safety (no file losses) over speed
    NOTE: Only tested thoroughly on Windows 10 OS
    NOTE: Only tested thoroughly on VALID_IMAGE_EXTENSIONS
    NOTE: Pillow ImageTk library docs: "Currently, the PhotoImage widget
          supports the GIF, PGM, PPM, and PNG file as of latest Tkinter version"
    """
    def __init__(self) -> None:
        self._log = []
        self._log_error_count = 0
        self._log_file_count = 0
        
        # Avoids "OSError: file is truncated" with large files (on img.resize())
        ImageFile.LOAD_TRUNCATED_IMAGES = True
        
        # Image traversal
        self._curr_image_count = 0
        self._total_image_count = 0
        
        # Class vars for callbacks and image viewer
        self.amount_entry = None  # Entry
        self.name_entry = None  # StringVar
        self.pil_image = None  # PIL.Image
        self.scaled_image = None  # PIL.Image
        self.tk_image = None  # ImageTk.PhotoImage
        self.lbl_image = None  # ttk.Label
        
        # Init full-screen Tkinter UI
        self.tk = Tk()
        self.tk.title(TITLE_STR)
        # self.tk.state("zoomed")  # Go full-screen
        self.tk.columnconfigure(0, weight=1)
        self.tk.rowconfigure(0, weight=1)
        
        # Create root frame to hold ALL widgets
        self.root = ttk.Frame(self.tk)
        self.root.grid(column=0, row=0)
        
        # Prep file names
        self.curr_dir = os.getcwd()
        all_file_names = [
            f for f in os.listdir(self.curr_dir)
            if os.path.isfile(os.path.join(self.curr_dir, f))
        ]
        self.image_file_names = [
            f for f in all_file_names
            if str(os.path.splitext(f)[1]).lower() in VALID_IMAGE_EXTENSIONS
        ]
        if not self.image_file_names:
            err_msg = FILES_NOT_FOUND_ERR + f'{self.curr_dir}'
            messagebox.showerror(HEADER_ERR, err_msg)
            self.tk.destroy()  # End app
            return
        
        self._total_image_count = len(self.image_file_names)
        
        # Use defaults from config file if possible
        if CONFIG_FILE_NAME in all_file_names:
            with open(CONFIG_FILE_NAME, 'r') as f:
                bucket_names = [
                    l.strip() for l in f.readlines() if len(l.strip()) > 0
                ]
            amount = len(bucket_names)
            incorrect_amount = amount < 2 or amount > 9
            contains_duplicates = amount != len(set(bucket_names))
            invalid_names = not self.bucket_names_are_valid(bucket_names)
            
            if incorrect_amount or contains_duplicates or invalid_names:
                err_str = f'{AMOUNT_INSTR_STR} {NAMING_INSTR_STR}'
                err_str += f' in "{CONFIG_FILE_NAME}"'
                messagebox.showerror(HEADER_ERR, err_str)
                self.tk.destroy()  # End app
                return
            
            self.amount = amount
            self.buckets = {b: set() for b in bucket_names}
            self.key_mapping = {
                str(i + 1): b for i, b in enumerate(bucket_names)
            }
            
            # Skip amount and naming screens
            self.create_image_screen()
        
        else:  # Use hardcoded defaults
            self.amount = DEFAULT_AMOUNT
            self.buckets = {
                f"bucket_{i + 1}": set() for i in range(self.amount)
            }
            self.key_mapping = {
                str(i + 1): f"bucket_{i + 1}" for i in range(self.amount)
            }
            
            # DEBUG: skip directly to screen
            self.create_amount_screen()
            # self.create_name_screen()
            # self.create_image_screen()
            # self.bucket_sort_images()  # DEBUG: requires additional input
            # self.create_results_screen()  # DEBUG: requires additional input
    
    ############################################################################
    # CREATE SCREEN FUNCTIONS
    ############################################################################
    def create_amount_screen(self) -> None:
        # Labels
        ttk.Label(self.root, text=TITLE_STR).grid(**self._gridv())
        ttk.Label(self.root, text=AMOUNT_INSTR_STR).grid(**self._gridv())
        
        # Text Entry
        amt_str = StringVar(),
        amount_entry = ttk.Entry(self.root, width=20, textvariable=amt_str)
        amount_entry.grid(**self._gridv())
        amount_entry.bind('<Return>', self.on_click_amount_continue)
        amount_entry.focus_set()
        self.amount_entry = amount_entry
        
        # Buttons
        amount_button = ttk.Button(
            self.root,
            text=AMOUNT_BUTTON_STR,
            command=self.on_click_amount_continue,
        )
        amount_button.grid(**self._gridv())
    
    def create_name_screen(self) -> None:
        # Labels
        ttk.Label(self.root, text=TITLE_STR).grid(**self._gridv())
        ttk.Label(self.root, text=NAMING_INSTR_STR).grid(**self._gridv())
        
        # Dynamic amount of entries
        name_entry_strs = []
        for i in range(self.amount):
            new_str = StringVar()
            new_entry = ttk.Entry(self.root, width=20, textvariable=new_str)
            new_entry.grid(**self._gridv())
            
            new_entry.bind('<Return>', self.on_click_name_continue)
            name_entry_strs.append(new_str)
            if i == 0:
                new_entry.focus_set()
        
        self.name_entry = name_entry_strs
        
        # Buttons
        name_button = ttk.Button(
            self.root,
            text=NAME_BUTTON_STR,
            command=self.on_click_name_continue,
        )
        name_button.grid(**self._gridv())
    
    def create_image_screen(self) -> None:
        if self._curr_image_count < self._total_image_count:
            image_name = self.image_file_names[self._curr_image_count]
            self._curr_image_count += 1
        else:
            self.clear_screen()
            self.bucket_sort_images()
            self.create_results_screen()
            return
        
        # Image
        self.pil_image = Image.open(image_name)
        width, height = self.pil_image.size
        
        # Labels
        progress_str = f"[{self._curr_image_count} / {self._total_image_count}]"
        image_info_str = f"Current Image: {image_name} ({width} x {height})"
        keymap_str = '        '.join([
            f"{key}: '{b}'" for key, b in self.key_mapping.items()
        ])
        ttk.Label(
            self.root,
            text=progress_str + image_info_str + keymap_str
        ).grid(**self._gridv())
        
        self.scaled_image = self.get_scaled_image(self.pil_image)
        self.tk_image = ImageTk.PhotoImage(self.scaled_image)
        self.lbl_image = ttk.Label(self.root, image=self.tk_image)
        
        # Dynamic binds
        for key, bucket_name in self.key_mapping.items():  # {'1': 'name_1'}
            data = {'bucket': bucket_name, 'image': image_name}
            self.lbl_image.bind(
                key,
                lambda e, d=data: self.on_keyclick_add_to_bucket(e, d)
            )
        
        self.lbl_image.grid(**self._gridv())
        self.lbl_image.focus_set()
    
    def create_results_screen(self) -> None:
        fc_str = f'{self._log_file_count}{FILES_COPIED_STR}'
        ec_str = f'{self._log_error_count}{ERRS_CAPTURED_STR}'
        ttk.Label(self.root, text=TITLE_STR).grid(**self._gridv())
        ttk.Label(self.root, text=fc_str).grid(**self._gridv())
        ttk.Label(self.root, text=ec_str).grid(**self._gridv())
        ttk.Label(self.root, text="\n".join(self._log[:30])).grid(
            **self._gridv()
        )
    
    ############################################################################
    # EVENT LISTENERS
    ############################################################################
    def on_click_amount_continue(self, _) -> None:
        amount_str = self.amount_entry.get()
        if len(amount_str) == 0:
            self.clear_screen()
            self.create_name_screen()
        
        elif str(amount_str).isnumeric():
            amount_int = int(amount_str)
            if 1 < amount_int < 10:
                self.amount = amount_int
                self.clear_screen()
                self.create_name_screen()
    
    def on_click_name_continue(self, _) -> None:
        bucket_names = [str(entry.get()) for entry in self.name_entry]
        if all([n == '' for n in bucket_names]):  # All empty, use defaults
            self.clear_screen()
            self.create_image_screen()
        
        elif self.bucket_names_are_valid(bucket_names):
            self.buckets = {b: set() for b in bucket_names}
            self.key_mapping = {
                str(i + 1): b for i, b in enumerate(bucket_names)
            }
            self.clear_screen()
            self.create_image_screen()
    
    def on_keyclick_add_to_bucket(self, _, data: Dict[str, str]) -> None:
        answer = messagebox.askokcancel(
            CONFIRM_COPY_BUTTON_STR,
            f"File '{data['image']}'' will be copied to '{data['bucket']}'",
        )
        if answer:
            self.buckets[data['bucket']].add(data['image'])
            self.clear_screen()
            self.create_image_screen()
    
    ############################################################################
    # OTHER FUNCS
    ############################################################################
    def bucket_names_are_valid(self, bucket_names: List[str]) -> bool:
        # Check for copies
        if len(bucket_names) != len(set(bucket_names)):
            return False
        
        # Check for mismatch
        for name in bucket_names:
            for ch in name:
                if ch not in self.VALID_NAME_CHARS:
                    return False
        return True
    
    def clear_screen(self) -> None:
        for w in self.root.winfo_children():
            w.destroy()
    
    def bucket_sort_images(self) -> None:
        # Creates subdirectories based on bucket names and sorts images by
        # COPYING images from curr_dir to each subdirectory
        all_subdir_names = [
            f for f in os.listdir(self.curr_dir)
            if os.path.isdir(os.path.join(self.curr_dir, f))
        ]
        
        # Create subdirectories only if they do not exist
        for bucket, image_set in self.buckets.items():
            if bucket not in all_subdir_names:
                try:
                    os.mkdir(os.path.join(self.curr_dir, bucket))
                    self.log(f"Successfully created {bucket}")
                except FileExistsError as e:
                    self.log(f"{bucket} already exists in {self.curr_dir}: {type(e)} {e}", True)
                except FileNotFoundError as e:
                    self.log(f"{self.curr_dir} not found: {type(e)} {e}", True)
                except OSError as e:
                    self.log(f"OS or I/O Exception when creating {bucket}: {type(e)} {e}", True)
                except Exception as e:
                    self.log(f"Unhandled Exception when creating dir {bucket}: {type(e)} {e}", True)
            
            # Subdir guaranteed to exist by now
            for image in image_set:
                try:
                    copy2(
                        os.path.join(self.curr_dir, image),
                        os.path.join(self.curr_dir, bucket),
                    )
                    self.log(f"Successfully copied {image} to {bucket}")
                    self._log_file_count += 1
                except Exception as e:
                    self.log(f"Unhandled Exception when copying {image} to {bucket}: {type(e)} {e}", True)
    
    def get_scaled_image(self, image: Image) -> Image:
        # Only need to use the largest scaling ratio to guarantee it is within bounds
        width, height = image.size
        scaling_ratio = max([width / self.IMG_MAX_WIDTH, height / self.IMG_MAX_HEIGHT])
        if scaling_ratio > 1:
            new_width = int(width * (1 / scaling_ratio))
            new_height = int(height * (1 / scaling_ratio))
            image = image.resize((new_width, new_height))
        return image
    
    def log(self, data: str, is_error: bool = False) -> None:
        if is_error:
            self._log_error_count += 1
            messagebox.showerror("Error", data)
        self._log.append(data)
    
    def _gridv(self) -> Dict[str, int]:
        # Appends widgets vertically
        r = len(self.root.winfo_children()) + 1
        return {'column': 1, 'row': r, 'padx': 50, 'pady': 10}


if __name__ == "__main__":
    sorter = ImageBucketSorter()
    sorter.tk.mainloop()