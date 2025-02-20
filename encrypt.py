import tkinter as tk
from tkinter import filedialog, messagebox, ttk, Entry, Label, Button
import cv2
import numpy as np
import os
from PIL import Image, ImageTk
import hashlib
import json
from datetime import datetime

class EnhancedEncryptApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Steganography - Encrypt")
        self.root.configure(bg='#f0f0f0')
        self.root.minsize(500, 600)
        self.selected_image_path = None
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the enhanced encryption interface."""
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
        
        # Message Entry with character counter
        Label(main_frame, text="Enter Secret Message:", bg='#f0f0f0').pack(pady=5)
        self.message_frame = tk.Frame(main_frame, bg='#f0f0f0')
        self.message_frame.pack(fill='x', pady=5)
        
        self.message_entry = tk.Text(self.message_frame, height=4, width=40)
        self.message_entry.pack(side='left', padx=(0, 5))
        self.message_entry.bind('<KeyRelease>', self.update_char_count)
        
        self.char_count_label = Label(self.message_frame, text="0/0", bg='#f0f0f0')
        self.char_count_label.pack(side='left', anchor='n')
        
        # Passcode Entry with strength meter
        Label(main_frame, text="Enter Passcode:", bg='#f0f0f0').pack(pady=5)
        self.passcode_entry = Entry(main_frame, width=40, show="*")
        self.passcode_entry.pack(pady=5)
        self.passcode_entry.bind('<KeyRelease>', self.update_password_strength)
        
        # Password strength meter
        self.strength_progress = ttk.Progressbar(main_frame, length=200, mode='determinate')
        self.strength_progress.pack(pady=5)
        self.strength_label = Label(main_frame, text="Password Strength: Weak", bg='#f0f0f0')
        self.strength_label.pack(pady=5)
        
        # Advanced options
        self.advanced_frame = tk.LabelFrame(main_frame, text="Advanced Options", bg='#f0f0f0')
        self.advanced_frame.pack(fill='x', pady=10)
        
        # Compression level
        self.compression_var = tk.IntVar(value=9)
        Label(self.advanced_frame, text="PNG Compression:", bg='#f0f0f0').pack(side='left', padx=5)
        compression_scale = ttk.Scale(self.advanced_frame, from_=0, to=9, 
                                    variable=self.compression_var, orient='horizontal')
        compression_scale.pack(side='left', padx=5, expand=True)
        
        # Encrypt Button
        self.encrypt_button = Button(main_frame, text="Encrypt", command=self.encrypt,
                                   bg='#007bff', fg='white', padx=20)
        self.encrypt_button.pack(pady=20)
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, length=300, mode='determinate')
        self.progress.pack(pady=5)
        
        # Status label
        self.status_label = Label(main_frame, text="", bg='#f0f0f0')
        self.status_label.pack(pady=5)
    
    def select_image(self):
        """Handle image selection with preview."""
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.gif"),
                ("All files", "*.*")
            ]
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
                original_size = os.path.getsize(file_path) / 1024  # KB
                max_chars = (os.path.getsize(file_path) * 8) // 64  # Approximate max characters
                self.info_label.config(
                    text=f"Size: {original_size:.1f}KB\nMax capacity: ~{max_chars} characters"
                )
                self.update_char_count(None)
            except Exception as e:
                messagebox.showerror("Error", f"Error loading image: {str(e)}")
    
    def update_char_count(self, event):
        """Update character counter and capacity warning."""
        if self.selected_image_path:
            current_chars = len(self.message_entry.get("1.0", "end-1c"))
            max_chars = (os.path.getsize(self.selected_image_path) * 8) // 64
            self.char_count_label.config(text=f"{current_chars}/{max_chars}")
            
            if current_chars > max_chars:
                self.char_count_label.config(fg='red')
                self.encrypt_button.config(state='disabled')
            else:
                self.char_count_label.config(fg='black')
                self.encrypt_button.config(state='normal')
    
    def update_password_strength(self, event):
        """Update password strength meter."""
        password = self.passcode_entry.get()
        strength = 0
        
        if len(password) >= 8:
            strength += 25
        if any(c.isupper() for c in password):
            strength += 25
        if any(c.islower() for c in password):
            strength += 25
        if any(c.isdigit() for c in password):
            strength += 25
            
        self.strength_progress['value'] = strength
        
        if strength < 50:
            self.strength_label.config(text="Password Strength: Weak", fg='red')
        elif strength < 75:
            self.strength_label.config(text="Password Strength: Medium", fg='orange')
        else:
            self.strength_label.config(text="Password Strength: Strong", fg='green')
    
    def str_to_bits(self, text):
        """Convert string to bits with proper uint8 handling."""
        bits = []
        for char in text:
            # Ensure the character value is within uint8 range
            char_value = ord(char) & 0xFF
            # Convert to 8-bit binary and ensure positive values
            bits.extend([int(b) & 1 for b in format(char_value, '08b')])
        return bits

    def embed_data(self, image_path, data_bits):
        """Embed data into image with proper uint8 handling."""
        # Read image and ensure uint8 type
        image = cv2.imread(image_path).astype(np.uint8)
        if len(data_bits) > image.size:
            raise ValueError("Message too large for image")
        
        # Flatten image and ensure uint8 type
        flat = image.flatten()
        
        # Track progress
        total_bits = len(data_bits)
        
        # Embed bits while maintaining uint8 range
        for i in range(total_bits):
            if i % 1000 == 0:  # Update progress
                self.progress['value'] = (i / total_bits) * 100
                self.root.update_idletasks()
            
            # Clear the least significant bit and set it to our data bit
            # Ensure we stay within uint8 range
            flat[i] = (flat[i] & 0xFE) | (data_bits[i] & 1)
        
        # Reshape back to original image dimensions
        return flat.reshape(image.shape)

    def encrypt(self):
        """Handle the encryption process with proper error handling."""
        try:
            if not self.selected_image_path:
                messagebox.showerror("Error", "Please select an image first")
                return
                
            message = self.message_entry.get("1.0", "end-1c")
            passcode = self.passcode_entry.get()
            
            if not message or not passcode:
                messagebox.showerror("Error", "Please enter both message and passcode")
                return
            
            # Create metadata
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "original_filename": os.path.basename(self.selected_image_path),
                "message_length": len(message),
                "passcode_hash": hashlib.sha256(passcode.encode()).hexdigest()
            }
            
            # Convert metadata to string and create header
            metadata_str = json.dumps(metadata)
            header = f"{len(metadata_str):08d}{len(passcode):08d}{len(message):08d}"
            
            # Combine all data
            full_message = header + metadata_str + passcode + message
            
            # Convert to bits with error checking
            try:
                data_bits = self.str_to_bits(full_message)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to convert message to bits: {str(e)}")
                return
            
            # Verify data size
            image = cv2.imread(self.selected_image_path)
            if len(data_bits) > image.size:
                messagebox.showerror("Error", "Message is too large for this image")
                return
            
            # Update status
            self.status_label.config(text="Encrypting...")
            self.root.update_idletasks()
            
            # Embed data with error handling
            try:
                modified_image = self.embed_data(self.selected_image_path, data_bits)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to embed data: {str(e)}")
                return
            
            # Get save location
            save_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png")],
                initialfile="encrypted.png"
            )
            
            if save_path:
                try:
                    # Save with selected compression
                    cv2.imwrite(save_path, modified_image, 
                              [cv2.IMWRITE_PNG_COMPRESSION, self.compression_var.get()])
                    
                    self.progress['value'] = 100
                    self.status_label.config(text="Encryption complete!")
                    
                    messagebox.showinfo("Success", 
                        f"Encryption complete!\nSaved as: {os.path.basename(save_path)}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save image: {str(e)}")
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.status_label.config(text="Encryption failed!")
        finally:
            self.progress['value'] = 0

    def run(self):
        """Start the encryption application."""
        self.root.mainloop()

if __name__ == "__main__":
    app = EnhancedEncryptApp()
    app.run()