import cv2
import numpy as np
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
import socket
import os
import time
import matplotlib.pyplot as plt

SERVER_IP = "127.0.0.1"
SERVER_PORT = 5001
BUFFER_SIZE = 4096

class StegoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("DCT Steganography Client")
        self.root.geometry("600x500+900+200")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Frame for Image Preview
        self.image_frame = ctk.CTkFrame(root, height=350)
        self.image_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Label for Image or Placeholder Text
        self.image_label = ctk.CTkLabel(self.image_frame, text="Select an image to preview", font=("Arial", 16))
        self.image_label.pack(expand=True)

        # Text Entry Field for Message
        self.text_entry = ctk.CTkEntry(root, width=400, placeholder_text="Enter text to embed")
        self.text_entry.pack(pady=10)

        # Buttons at the Bottom
        self.button_frame = ctk.CTkFrame(root)
        self.button_frame.pack(pady=10, fill="x")

        self.select_button = ctk.CTkButton(self.button_frame, text="Select Image", command=self.load_image)
        self.select_button.pack(side="left", padx=20, pady=10)

        self.process_button = ctk.CTkButton(self.button_frame, text="Process & Send", command=self.process_and_send, state="disabled")
        self.process_button.pack(side="right", padx=20, pady=10)

        # Store Image Path and CV2 Image
        self.image_path = None
        self.cv2_image = None

    def load_image(self):
        """Opens file dialog to select an image and updates the preview."""
        file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.png *.bmp")])
        if not file_path:
            return

        self.image_path = file_path
        self.cv2_image = cv2.imread(file_path)

        # Load and display the image with CTkImage
        pil_image = Image.open(file_path)
        pil_image.thumbnail((500, 350))
        self.ctk_image = ctk.CTkImage(light_image=pil_image, size=(500, 350))

        self.image_label.configure(image=self.ctk_image, text="")  # Remove text, show image
        self.process_button.configure(state="normal")  # Enable processing button

    def process_and_send(self):
        """Processes the image, visualizes DCT embedding, and sends the stego image."""
        if self.cv2_image is None:
            messagebox.showerror("Error", "No image selected!")
            return

        hidden_text = self.text_entry.get()
        if not hidden_text:
            messagebox.showerror("Error", "Enter a message to embed!")
            return

        img = self.cv2_image.copy()
        plt.figure(figsize=(10, 5), facecolor='#2b2b2b')

        # Step 1: Show Original Image
        plt.subplot(2, 3, 1)
        plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        plt.title("Original RGB Image", color='white')
        plt.axis("off")
        plt.pause(1)

        # Step 2: Convert to YCrCb
        img_ycrcb = cv2.cvtColor(img, cv2.COLOR_BGR2YCrCb)
        y, cr, cb = cv2.split(img_ycrcb)

        plt.subplot(2, 3, 2)
        plt.imshow(y, cmap='gray')
        plt.title("Luminance (Y) Channel", color='white')
        plt.axis("off")
        plt.pause(1)

        # Step 3: Apply DCT
        dct_y = cv2.dct(np.float32(y))
        plt.subplot(2, 3, 3)
        plt.imshow(np.log(abs(dct_y) + 1), cmap='gray')
        plt.title("DCT Transform", color='white')
        plt.axis("off")
        plt.pause(1)

        # Step 4: Subtle Message Embedding
        hash_val = sum(ord(c) for c in hidden_text) % 255  # Simple hash
        dct_y[20:40, 20:40] += hash_val * 0.01  # Embed message in a subtle way
        plt.subplot(2, 3, 4)
        plt.imshow(np.log(abs(dct_y) + 1), cmap='gray')
        plt.title("DCT with Embedded Message", color='white')
        plt.axis("off")
        plt.pause(1)

        # Step 5: Apply Inverse DCT
        idct_y = cv2.idct(dct_y)
        plt.subplot(2, 3, 5)
        plt.imshow(idct_y, cmap='gray')
        plt.title("Reconstructed Y Channel", color='white')
        plt.axis("off")
        plt.pause(1)

        # Step 6: Convert Back to RGB
        img_ycrcb[:, :, 0] = idct_y  # Replace modified Y channel
        final_img = cv2.cvtColor(img_ycrcb, cv2.COLOR_YCrCb2BGR)
        plt.subplot(2, 3, 6)
        plt.imshow(cv2.cvtColor(final_img, cv2.COLOR_BGR2RGB))
        plt.title("Final Reconstructed Image", color='white')
        plt.axis("off")
        plt.pause(1)

        plt.show()

        # Save the processed image
        temp_path = os.path.join(os.getcwd(), "stego_image.png")
        cv2.imwrite(temp_path, final_img)
        print(f"Stego image saved at {temp_path}")

        # Send Image to Server
        self.send_image(temp_path)

    def send_image(self, file_path):
        """Sends the stego image to the server."""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((SERVER_IP, SERVER_PORT))

            # Send file name first
            filename = os.path.basename(file_path)
            client_socket.sendall(filename.encode())

            # Send image data
            time.sleep(1)  # Ensure the server gets the filename first
            with open(file_path, "rb") as file:
                while (chunk := file.read(BUFFER_SIZE)):
                    client_socket.sendall(chunk)

            print(f"Image {filename} sent successfully to server.")
            client_socket.close()
            messagebox.showinfo("Success", f"Image sent to {SERVER_IP}:{SERVER_PORT}")

        except ConnectionRefusedError:
            messagebox.showerror("Error", "Server is not running! Start the server first.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send image: {e}")

# Run the Application
if __name__ == "__main__":
    root = ctk.CTk()
    app = StegoApp(root)
    root.mainloop()
