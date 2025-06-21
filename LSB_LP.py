#steganography project using Least Significant Bit (LSB) image manipulation with XOR encryption
import cv2 as cv
import numpy as np
import os

# Load image
img = cv.imread("D:\Z Download\crypto-polyhedra.jpg")
if img is None:
    print("Failed to load image. Check the file path.")
    exit()

rows, cols, _ = img.shape
print("Width:", rows, " Height:", cols)

# Get key and message from user
key = input("Enter key to encrypt: ")
text = input("Enter text to hide: ")

# Add delimiter to mark end of message
delimiter = "#END#"
text_to_hide = text + delimiter

# Check if the message fits in the image
if len(text_to_hide) * 8 > rows * cols:
    print("Text is too long to hide in the image.")
    exit()

# Variables
n = 0  # row index
m = 0  # column index
z = 0  # channel index
kl = 0  # key index
l = len(text_to_hide)

# Embed the data
for i in range(l):
    # XOR encryption with key
    char = chr(ord(text_to_hide[i]) ^ ord(key[kl]))
    char_bin = ord(char)

    for k in range(8):
        pixel_value = int(img[n, m, z])
        bit = (char_bin >> (7 - k)) & 1
        new_pixel_value = (pixel_value & ~1) | bit
        img[n, m, z] = np.uint8(new_pixel_value)  # explicitly cast back to uint8

        m += 1
        if m >= cols:
            m = 0
            n += 1
        if n >= rows:
            print("Image capacity exceeded during embedding.")
            exit()

    kl = (kl + 1) % len(key)

# Save encrypted image
output_image_path = "encrypted_img.jpg"
cv.imwrite(output_image_path, img)
print("Data hiding completed successfully.")

# Try to open the image
try:
    os.startfile(output_image_path)
except AttributeError:
    print(f"Cannot open '{output_image_path}'. Please open it manually.")

# Decrypt process
ch = int(input("\nEnter 1 to extract data from image: "))
if ch == 1:
    key1 = input("\nRe-enter key to extract text: ")

    if key != key1:
        print("Key doesn't match.")
        exit()

    n = m = z = kl = 0
    decrypt = ""

    while True:
        char_bin = 0
        for k in range(8):
            if n >= rows or m >= cols:
                print("Reached end of image before finding delimiter.")
                break

            bit = img[n, m, z] & 1
            char_bin = (char_bin << 1) | bit

            m += 1
            if m >= cols:
                m = 0
                n += 1

        if n >= rows and char_bin == 0:
            break

        # XOR decryption using key
        decrypted_char = chr(char_bin ^ ord(key[kl]))
        decrypt += decrypted_char
        kl = (kl + 1) % len(key)

        if decrypt.endswith(delimiter):
            decrypt = decrypt[:-len(delimiter)]
            break

        if n >=rows:
            print("Reached end of image without finding delimiter.")
            break

    print("Decrypted text: ", decrypt)
else:
    print("Wrong Input, Try again...")
