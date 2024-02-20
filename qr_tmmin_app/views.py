from django.shortcuts import render, redirect
from django.views.generic import TemplateView, View
# from django.conf import settings
from django.template.loader import render_to_string

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse

import os
import fitz  # pipenv install pymupdf
import re
from Crypto.Cipher import AES  # pipenv install pycryptodome
from Crypto.Util.Padding import pad, unpad
import base64
import qrcode  # pipenv install qrcode
from PIL import Image  # resize image # pipenv install pillow
import shutil


# Create your views here.
class GeneratePage(TemplateView):
    template_name = 'generate.html'

    def post(self, request, *args, **kwargs):
        files = request.FILES.getlist('pdf_file')

        if files:
            private_key = self.request.POST.get('key')
            # Clear existing files in the media directory
            self.clear_media_directory()
            converted_text_files = []

            # Save private key
            with open(os.path.join(settings.MEDIA_ROOT, 'key', 'private_key.txt'), 'w') as key_file:
                key_file.write(private_key)

            for file in files:
                with open(os.path.join(settings.MEDIA_ROOT, 'temp', file.name), 'wb+') as destination:
                    for chunk in file.chunks():
                        destination.write(chunk)


                text_file_path = self.convert_pdf_to_text(file)
                text_file_path_cleaned = self.remove_blank_newlines(text_file_path)
                converted_text_files.append(text_file_path_cleaned)

        return redirect(request.META.get('HTTP_REFERER'))

    #   convert multiple PDF files to text files using the PyMuPDF (fitz)
    def convert_pdf_to_text(self, pdf_file):
        pdf_path = os.path.join(settings.MEDIA_ROOT, 'temp', pdf_file.name)
        doc = fitz.open(pdf_path)
        text = ""

        for page in doc:
            text += page.get_text()

        text_file_path = pdf_path.replace('.pdf', '.txt')
        with open(text_file_path, 'w') as txt_file:
            txt_file.write(text)

        return text_file_path

    #   removing the blank lines
    def remove_blank_newlines(self, file_path):
        with open(file_path, 'r') as f:
            lines = f.readlines()

        # Remove blank lines
        lines = [line.strip() for line in lines if line.strip()]

        # Rewrite the file
        with open(file_path, 'w') as f:
            f.write('\n'.join(lines))

        return file_path

    #   remove all files in the media path when the form is submitted
    def clear_media_directory(self):
        temp_folder_path = os.path.join(settings.MEDIA_ROOT, 'temp')
        if os.path.exists(temp_folder_path) and os.path.isdir(temp_folder_path):
            for filename in os.listdir(temp_folder_path):
                file_path = os.path.join(temp_folder_path, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")
        else:
            print("Temp folder does not exist or is not a directory")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # text files in a directory media
        text_files_dir = os.path.join(settings.MEDIA_ROOT, 'temp')

        # Initialize an empty list to store filenames and corresponding plain_text
        files_data = []

        # Read the private key from private_key.txt file
        private_key_file_path = os.path.join(settings.MEDIA_ROOT, 'key', 'private_key.txt')
        try:
            with open(private_key_file_path, 'r') as key_file:
                private_key = key_file.read().strip()

            # Add private key to the context
            context['private_key'] = private_key
        except FileNotFoundError:
            pass

        # Read lines from each text file and store them in a dictionary with file names as keys
        for filename in os.listdir(text_files_dir):
            if filename.endswith('.txt'):
                file_path = os.path.join(text_files_dir, filename)
                with open(file_path, 'r') as file:
                    lines = file.readlines()
                    invoice_number = lines[12].replace('\n', '').replace(':', '').replace(' ', '')
                    amount_bef_tax = lines[18].replace('\n', '').replace(':', '').replace('IDR', '').replace(' ',
                                                                                                             '').replace(
                        ',', '')
                    tot_invoice_amount = lines[14].replace('\n', '').replace(':', '').replace('IDR', '').replace(' ',
                                                                                                                 '').replace(
                        ',', '')
                    invoice_tax_amount = lines[17].replace('\n', '').replace(':', '').replace('IDR', '').replace(' ',
                                                                                                                 '').replace(
                        ',', '')
                    invoice_tax_no = lines[15].replace('\n', '').replace(':', '').replace(' ', '')

                    plain_text = 'VISION' + '|' + invoice_number + '|' + amount_bef_tax + '.00|' + tot_invoice_amount + '.00|' + invoice_tax_amount + '.00|' + invoice_tax_no
                    key = private_key  # secret key
                    iv = b'\0' * 16  # Default zero based bytes[16]

                    # Pad the content
                    msg = pad(plain_text.encode(), AES.block_size)

                    # Create AES cipher object
                    cipher = AES.new(key.encode(), AES.MODE_CBC, iv)

                    # Encrypt the content
                    cipher_text = cipher.encrypt(msg)

                    # Encode the encrypted content in base64
                    base64_encoded = base64.b64encode(cipher_text).decode('utf-8')

                    # Generate QR code
                    im = qrcode.make(base64_encoded)
                    qr_image = im.resize((250, 250), Image.Resampling.LANCZOS)

                    # Save QR code to media folder
                    img_name = invoice_number + '.png'
                    img_path = os.path.join(settings.MEDIA_ROOT, 'temp', img_name)
                    qr_image.save(img_path)

                    # Store the filename and corresponding plain_text in the list
                    files_data.append(
                        {'filename': filename, 'invoice': invoice_number, 'plain_text': plain_text,
                         'encrypted_content': base64_encoded})

        context['files_data'] = files_data
        return context