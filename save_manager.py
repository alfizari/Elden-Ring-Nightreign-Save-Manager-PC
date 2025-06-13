import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog, Scrollbar
from functools import wraps
from time import time
import hashlib
import binascii
import shutil
import glob
from main_file import decrypt_ds2_sl2, encrypt_modified_files

window = tk.Tk()
window.title("ER Nightreign Save Transfer")
window.geometry("300x200")
window.resizable(True, True)

def ask_steam_id_window(callback):
    # Create a new window for entering the Steam ID
    steam_id_window = tk.Toplevel(window)  # Pass the parent window
    steam_id_window.title("Enter Your 17-Digit Steam ID")
    steam_id_window.geometry("400x150")
    
    # Make it modal and focused
    steam_id_window.transient(window)  # Set parent window
    steam_id_window.grab_set()  # Make it modal
    steam_id_window.focus_force()  # Force focus
    steam_id_window.lift()  # Bring to front
    
    # Center the window relative to parent
    steam_id_window.geometry("+%d+%d" % (window.winfo_rootx() + 50, window.winfo_rooty() + 50))

    # Label for the input field
    label = tk.Label(steam_id_window, text="Enter your 17-digit Steam ID:")
    label.pack(pady=10)

    # Entry widget for the Steam ID
    steam_id_entry = tk.Entry(steam_id_window, width=30)
    steam_id_entry.pack(pady=5)
    steam_id_entry.focus_set()  # Focus on the entry field

    # Function to handle the submission of the Steam ID
    def submit_steam_id():
        steam_id = steam_id_entry.get()
        
        if len(steam_id) != 17 or not steam_id.isdigit():
            messagebox.showerror("Invalid Steam ID", "Steam ID must be exactly 17 digits!")
            return

        # Convert Steam ID to hexadecimal and then to little-endian format
        steam_id_hex = format(int(steam_id), 'x').zfill(16)
        steam_id_bytes = bytes.fromhex(steam_id_hex)
        steam_id_bytes = steam_id_bytes[::-1]

        steam_id_window.destroy()
        callback(steam_id_bytes)

    # Submit button
    submit_button = tk.Button(steam_id_window, text="Submit", command=submit_steam_id)
    submit_button.pack(pady=10)
    
    # Allow Enter key to submit
    steam_id_window.bind('<Return>', lambda event: submit_steam_id())

def get_output():
    filename = filedialog.asksaveasfilename(
        title="Save New Encrypted SL2 File As",
        filetypes=[("SL2 Files", "*.sl2"), ("All Files", "*.*")],
        defaultextension=".sl2",
        initialfile="DS2SOFS0000.sl2"
    )
    if filename:
        print(f"Selected output SL2 file: {filename}") 
        return filename
    return None

def get_input():
    return filedialog.askopenfilename(
        title="Select Decrypted SL2 File",
        filetypes=[("SL2 Files", "*.sl2"), ("All Files", "*.*")]
    )

def open_folder_and_show_files():
    # Get all userdata files in the folder
    input_file = get_input()
    folder_path = decrypt_ds2_sl2(input_file)
    userdata_files = sorted(glob.glob(os.path.join(folder_path, "USERDATA*")))
    
    user_data_10_path = os.path.join(folder_path, 'USERDATA_10')
    if os.path.isfile(user_data_10_path):
        with open(user_data_10_path, 'rb') as f:
            steam_id_offset = 0x8
            f.seek(steam_id_offset)
            steam_id = f.read(8)
    else:
        messagebox.showerror("Error", f"USERDATA_10 not found in {folder_path}")
        return
    
    def handle_steam_id(steam_id_bytes):
        if not steam_id_bytes:
            return
        
        print(f"Old Steam ID (hex): {steam_id.hex()}")
        print(f"New Steam ID (hex): {steam_id_bytes.hex()}")
        
        files_modified = 0
        
        # Process the files with the new Steam ID
        for file_path in userdata_files:
            with open(file_path, 'rb') as f:
                data = f.read()
            
            # Check if the old steam_id exists in this file
            if steam_id in data:
                print(f"Found old Steam ID in {os.path.basename(file_path)}")
                new_data = data.replace(steam_id, steam_id_bytes)
                
                # Verify the replacement actually happened
                if new_data != data:
                    with open(file_path, 'wb') as f:
                        f.write(new_data)
                    print(f"Successfully replaced Steam ID in {os.path.basename(file_path)}")
                    files_modified += 1
                else:
                    print(f"Warning: No replacement occurred in {os.path.basename(file_path)}")
            else:
                print(f"Old Steam ID not found in {os.path.basename(file_path)}")
        
        if files_modified > 0:
            messagebox.showinfo("Success", f"Steam ID replaced in {files_modified} file(s)")
        else:
            messagebox.showwarning("Warning", "No files were modified. Old Steam ID may not have been found.")
        
        # NOW get the output file after Steam ID processing is complete
        output_sl2_file = get_output()
        if output_sl2_file:  # Only proceed if user didn't cancel
            encrypt_modified_files(output_sl2_file)

    # Only ask for Steam ID first
    ask_steam_id_window(handle_steam_id)





#UI
window.columnconfigure(0, weight=1)
window.rowconfigure(0, weight=1)

# Create main frame with padding
main_frame = ttk.Frame(window, padding=10)
main_frame.grid(row=0, column=0, sticky="nsew")

# Allow content in main_frame to expand
main_frame.columnconfigure(0, weight=1)
main_frame.rowconfigure(0, weight=1)

# Styling constants
button_width = 30
button_padding_y = 15
button_padding_x = 20

# Add buttons using grid
decrypt_button = ttk.Button(main_frame, text="Select Save file to resign", width=button_width, command=open_folder_and_show_files)
decrypt_button.grid(row=0, column=0, pady=button_padding_y, padx=button_padding_x)


# Run the application
window.mainloop()