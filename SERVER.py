import socket
import cv2
import numpy as np
import os
import time
import customtkinter as ctk
from tkinter import messagebox, filedialog
from PIL import Image

# Server Configuration
SERVER_IP = "127.0.0.1"
SERVER_PORT = 5001
BUFFER_SIZE = 4096
SAVE_PATH = r"C:\Users\HP\Desktop\Image Received\Stego_image.png"  # Ensure folder exists

class StegoServer:
    def __init__(self, root):
        self.root = root
        self.root.title("DCT Steganography Server")
        self.root.geometry("600x500+100+200")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Frame for Image Preview
        self.image_frame = ctk.CTkFrame(root, height=350)
        self.image_frame.pack(pady=10, padx=10, fill="both", expand=True)

        self.image_label = ctk.CTkLabel(self.image_frame, text="Waiting for Image...", font=("Arial", 16))
        self.image_label.pack(expand=True)

        # Buttons
        self.button_frame = ctk.CTkFrame(root)
        self.button_frame.pack(pady=10, fill="x")

        self.start_server_button = ctk.CTkButton(self.button_frame, text="Start Server", command=self.start_server)
        self.start_server_button.pack(side="left", padx=20, pady=10)

        self.extract_button = ctk.CTkButton(self.button_frame, text="Extract Data", command=self.extract_message, state="disabled")
        self.extract_button.pack(side="right", padx=20, pady=10)

        self.received_image_path = None

    def start_server(self):
        """Starts the server to receive an image from the client."""
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.bind((SERVER_IP, SERVER_PORT))
            server_socket.listen(1)
            messagebox.showinfo("Server", f"Server started. Waiting for a connection on {SERVER_IP}:{SERVER_PORT}...")

            conn, addr = server_socket.accept()
            print(f"Connected by {addr}")

            # Receive filename
            filename = conn.recv(BUFFER_SIZE).decode()
            print(f"Receiving file: {filename}")

            # Receive image data
            os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
            with open(SAVE_PATH, "wb") as file:
                while True:
                    data = conn.recv(BUFFER_SIZE)
                    if not data:
                        break
                    file.write(data)

            print(f"Image saved at {SAVE_PATH}")
            conn.close()

            # Update GUI with received image
            self.received_image_path = SAVE_PATH
            self.display_received_image()
            self.extract_button.configure(state="normal")  # Enable extraction button

        except Exception as e:
            messagebox.showerror("Server Error", f"Failed to receive image: {e}")

    def display_received_image(self):
        """Displays the received image in the GUI."""
        pil_image = Image.open(self.received_image_path)
        pil_image.thumbnail((500, 350))
        ctk_image = ctk.CTkImage(light_image=pil_image, size=(500, 350))

        self.image_label.configure(image=ctk_image, text="")
        self.image_label.image = ctk_image

    def extract_message(self):
        """Extracts the hidden message using DCT steganography."""
        if not self.received_image_path or not os.path.exists(self.received_image_path):
            messagebox.showerror("Error", "No stego image found!")
            return

        try:
            # Load the stego image
            stego_image = cv2.imread(self.received_image_path)
            if stego_image is None:
                messagebox.showerror("Error", "Failed to load stego image!")
                return

            # Step 2: Convert to YCrCb and extract the luminance (Y) channel
            stego_ycrcb = cv2.cvtColor(stego_image, cv2.COLOR_BGR2YCrCb)
            y_channel, _, _ = cv2.split(stego_ycrcb)

            # Step 3: Apply DCT to the Y channel
            dct_y = cv2.dct(np.float32(y_channel))

            # Step 4: Extract the embedded message
            # Assuming the message is encoded within the [20:40, 20:40] block
            embedded_block = dct_y[20:40, 20:40]
            average_value = np.mean(embedded_block) / .58  # Reverse the embedding scaling
            extracted_hash = int(average_value) % 255  # Convert back to hash value

            # Step 5: Attempt to deduce the message
            retrieved_message = None
            possible_messages = ["hello", "secret", "message", "steganography"]  # Example messages

            for msg in possible_messages:
                computed_hash = sum(ord(c) for c in msg) % 255
                if computed_hash == extracted_hash:
                    retrieved_message = msg
                    break

            # Display the extraction result
            if retrieved_message:
                messagebox.showinfo("Extracted Message", f"Recovered Message: {retrieved_message}")
            else:
                messagebox.showwarning("Extraction Result", f"Hash extracted: {extracted_hash}, but no match found.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to extract message: {e}")

# Run the Server Application
if __name__ == "__main__":
    root = ctk.CTk()
    app = StegoServer(root)
    root.mainloop()
