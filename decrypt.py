import tkinter as tk
from tkinter import filedialog, messagebox, ttk, Entry, Label, Button
import cv2
import numpy as np
import hashlib
import json
from datetime import datetime
from PIL import Image, ImageTk
import os  # Added the missing import

class EnhancedDecryptApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Steganography - Decrypt")
        self.root.configure(bg='#f0f0f0')
        self.root.minsize(500, 600)
        self.selected_image_path = None
        self.setup_ui()
    
    def setup_ui(self):
        """Initialize the decryption interface."""
        # Main frame
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)
        
        # Image preview frame
        self.image_frame = tk.LabelFrame(main_frame, text="Image Preview", bg='#f0f0f0')
        self.image_frame.pack(fill='both', expand=True, pady=(0, 20))
        
        self.image_label = Label(self.image_frame, text="No image selected", bg='#f0f0f0')
        self.image_label.pack(pady=10)
        
        # Select image button
        Button(main_frame, text="Select Image", command=self.select_image,
               bg='#28a745', fg='white', padx=20).pack(pady=5)
        
        # Image info label
        self.info_label = Label(main_frame, text="", bg='#f0f0f0')
        self.info_label.pack(pady=5)
        
        # Passcode Entry
        Label(main_frame, text="Enter Passcode:", bg='#f0f0f0').pack(pady=5)
        self.passcode_entry = Entry(main_frame, width=40, show="*")
        self.passcode_entry.pack(pady=5)
        
        # Decrypt Button
        self.decrypt_button = Button(main_frame, text="Decrypt", command=self.decrypt,
                                   bg='#007bff', fg='white', padx=20)
        self.decrypt_button.pack(pady=20)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, length=300, mode='determinate')
        self.progress.pack(pady=5)
        
        # Status label
        self.status_label = Label(main_frame, text="", bg='#f0f0f0')
        self.status_label.pack(pady=5)
        
        # Decrypted message display
        Label(main_frame, text="Decrypted Message:", bg='#f0f0f0').pack(pady=5)
        self.message_text = tk.Text(main_frame, height=8, width=40)
        self.message_text.pack(pady=5)
        
        # Metadata display
        self.metadata_frame = tk.LabelFrame(main_frame, text="Metadata", bg='#f0f0f0')
        self.metadata_frame.pack(fill='x', pady=10)
        self.metadata_label = Label(self.metadata_frame, text="", bg='#f0f0f0', justify=tk.LEFT)
        self.metadata_label.pack(pady=5, padx=5)
    
    def select_image(self):
        """Handle encrypted image selection with preview."""
        file_path = filedialog.askopenfilename(
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if file_path:
            try:
                self.selected_image_path = file_path
                # Create image preview
                image = Image.open(file_path)
                # Calculate size to fit in preview
                preview_size = (300, 300)
                image.thumbnail(preview_size, Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                
                self.image_label.configure(image=photo)
                self.image_label.image = photo  # Keep reference
                
                # Update info label
                size = os.path.getsize(file_path) / 1024  # KB
                self.info_label.config(text=f"Size: {size:.1f}KB")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error loading image: {str(e)}")
    
    def bits_to_str(self, bits):
        """Convert bits back to string."""
        chars = []
        for i in range(0, len(bits), 8):
            byte = bits[i:i+8]
            chars.append(chr(int(''.join(map(str, byte)), 2)))
        return ''.join(chars)
    
    def extract_bits(self, image_path, num_bits):
        """Extract hidden bits from image."""
        # Read image
        image = cv2.imread(image_path).astype(np.uint8)
        flat = image.flatten()
        
        # Extract bits
        bits = []
        for i in range(num_bits):
            if i % 1000 == 0:  # Update progress
                self.progress['value'] = (i / num_bits) * 100
                self.root.update_idletasks()
            bits.append(flat[i] & 1)
        
        return bits
    
    def decrypt(self):
        """Handle the decryption process."""
        try:
            if not self.selected_image_path:
                messagebox.showerror("Error", "Please select an image first")
                return
            
            passcode = self.passcode_entry.get()
            if not passcode:
                messagebox.showerror("Error", "Please enter the passcode")
                return
            
            self.status_label.config(text="Decrypting...")
            self.root.update_idletasks()
            
            # First extract header (24 digits for metadata_length, passcode_length, and message_length)
            header_bits = self.extract_bits(self.selected_image_path, 24 * 8)
            header_str = self.bits_to_str(header_bits)
            
            try:
                metadata_length = int(header_str[:8])
                passcode_length = int(header_str[8:16])
                message_length = int(header_str[16:24])
            except ValueError:
                messagebox.showerror("Error", "Invalid or corrupted header")
                return
            
            # Extract metadata, passcode, and message
            total_bits = (24 + metadata_length + passcode_length + message_length) * 8
            all_bits = self.extract_bits(self.selected_image_path, total_bits)
            
            # Convert bits to string
            full_text = self.bits_to_str(all_bits)
            
            # Parse the components
            header = full_text[:24]
            metadata_str = full_text[24:24+metadata_length]
            stored_passcode = full_text[24+metadata_length:24+metadata_length+passcode_length]
            message = full_text[24+metadata_length+passcode_length:]
            
            # Verify passcode
            if passcode != stored_passcode:
                messagebox.showerror("Error", "Incorrect passcode")
                return
            
            # Display message
            self.message_text.delete('1.0', tk.END)
            self.message_text.insert('1.0', message)
            
            # Display metadata
            try:
                metadata = json.loads(metadata_str)
                metadata_text = f"Original filename: {metadata['original_filename']}\n"
                metadata_text += f"Timestamp: {metadata['timestamp']}\n"
                metadata_text += f"Message length: {metadata['message_length']} characters"
                self.metadata_label.config(text=metadata_text)
            except json.JSONDecodeError:
                self.metadata_label.config(text="Metadata unavailable or corrupted")
            
            self.progress['value'] = 100
            self.status_label.config(text="Decryption complete!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Decryption failed: {str(e)}")
            self.status_label.config(text="Decryption failed!")
        finally:
            self.progress['value'] = 0
    
    def run(self):
        """Start the decryption application."""
        self.root.mainloop()

if __name__ == "__main__":
    app = EnhancedDecryptApp()
    app.run()