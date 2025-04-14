from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView, CreateView, View

from django.conf import settings

import os
import fitz  # pip install pymupdf
from Crypto.Cipher import AES  # pip install pycryptodome
# from Crypto.Util.Padding import pad
import base64
import qrcode  # pip install qrcode
from PIL import Image  # resize image # pip install pillow
from .forms import InvoiceForm, PrivateKeyForm
from .models import PrivateKey, Invoice
from django.contrib import messages

class CreatePrivateKeyView(CreateView):
    template_name = 'pages/create_regular.html'
    model = PrivateKey
    form_class = PrivateKeyForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['card_title'] = 'Create Private Key'
        items =  PrivateKey.objects.all()
        
        # Tambah tombol ke tiap baris data
        for item in items:
            item.buttons_action = [
                f"<button type='button' data-bs-toggle='modal' data-bs-target='#modal-first-{item.id}' class='btn btn-sm btn-danger'>Delete</button>"
            ]

            # Content modal
            item.modals_form = {
                'Delete Item': {
                    'modal_id': f'modal-first-{item.id}',
                    'action_url': reverse('key_delete', kwargs={'pk': item.id}),
                    'action_name': f'<button type="submit" class="btn btn-secondary">Delete</button>',
                    # 'info': f'<p class="fw-bolder">{item.get('nama_produk')}</p>'
                }
            }

        context['items'] = items
        context['fields'] = {
            'name': 'Name',
            'private_key': 'Private Key'
        }
        return context
    
    def form_valid(self, form):
        # Form is valid, save the object and display a success message
        response = super().form_valid(form)
        messages.success(self.request, 'Private key added successfully!')
        return response

    def form_invalid(self, form):
        # Form is invalid, display an error message
        response = super().form_invalid(form)
        messages.error(self.request, 'There was an error creating the Private Key. Please check the form and try again.')
        return response

    # Optional: You can define success_url to redirect after form submission
    def get_success_url(self):
        # Redirect to a specific page after a successful form submission
        return reverse_lazy('key_create')  # Replace with the name of the URL for your list page or another page.

class DeletePrivateKeyView(View):
    def post(self, request, pk):
        item = get_object_or_404(PrivateKey, pk=pk)
        item.delete()
        messages.success(request, "The item has been successfully deleted.")
        return redirect(reverse_lazy('key_create'))

'''class CreateManualGeneratePageView(TemplateView):
    template_name = 'pages/create.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = InvoiceForm
        context['card_title'] = 'Manual Input Invoice'
        context['additionals_button'] = f"<button type='button' class='btn btn-sm ms-2 btn-secondary' onclick='window.location.href=\"{reverse('key_create')}\"'><i class='fa fa-plus me-2'></i>Private Key</button>"
        return context'''

"""class CreateManualGeneratePageView(TemplateView):
    template_name = 'pages/create.html'
    model = PrivateKey
    form_class = PrivateKeyForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = InvoiceForm
        context['card_title'] = 'Manual Input Invoice'
        context['additionals_button'] = f"<button type='button' class='btn btn-sm ms-2 btn-secondary' onclick='window.location.href=\"{reverse('key_create')}\"'><i class='fa fa-plus me-2'></i>Private Key</button>"
        return context"""

class CreateManualGeneratePageView(CreateView):
    template_name = 'pages/create.html'
    model = Invoice
    form_class = InvoiceForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['card_title'] = 'Manual Input Invoice'
        context['items'] = Invoice.objects.all()
        context['additionals_button'] = f"<button type='button' class='btn btn-sm ms-2 btn-secondary' onclick='window.location.href=\"{reverse('key_create')}\"'><i class='fa fa-plus me-2'></i>Private Key</button>"
        return context

"""# Create your views here.
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


class GeneratePage2(TemplateView):
    template_name = 'generate_manual.html'

    def post(self, request, *args, **kwargs):
        files = request.POST.getlist('plainText')

        # Process files if there are any
        if files:
            private_key = self.request.POST.get('key')

            # Clear existing files in the media directory
            self.clear_media_directory()

            # Save private key
            with open(os.path.join(settings.MEDIA_ROOT, 'key', 'private_key.txt'), 'w') as key_file:
                key_file.write(private_key)

            # Define the file path within the temporary folder
            temp_folder_path = os.path.join(settings.MEDIA_ROOT, 'temp_2')

            # Define file paths for plaintext files
            plaintext_file_path = os.path.join(temp_folder_path, 'output_plaintext.txt')

            # Save plaintext content to a file
            with open(plaintext_file_path, 'w') as f:
                f.write('\n'.join(files))

        # Redirect back to the previous page
        return redirect(request.META.get('HTTP_REFERER'))


    # remove all files in the media path when the form is submitted
    def clear_media_directory(self):
        temp_folder_path = os.path.join(settings.MEDIA_ROOT, 'temp_2')
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

        # Read the private key from private_key.txt file
        private_key_file_path = os.path.join(settings.MEDIA_ROOT, 'key', 'private_key.txt')
        private_key = None  # Initializing private_key
        try:
            with open(private_key_file_path, 'r') as key_file:
                private_key = key_file.read().strip()

            # Add private key to the context
            context['private_key'] = private_key
        except FileNotFoundError:
            pass


        if private_key:
            # Define the temporary folder path
            temp_folder_path = os.path.join(settings.MEDIA_ROOT, 'temp_2')

            # Define file paths for plaintext and base64 encoded files
            plaintext_file_path = os.path.join(temp_folder_path, 'output_plaintext.txt')
            base64_file_path = os.path.join(temp_folder_path, 'output_base64.txt')

            key = private_key  # secret key
            iv = b'\0' * 16  # Default zero based bytes[16]
            base64_encoded_lines = []
                
            try:
                # Read plaintext content from file and encrypt each line
                with open(plaintext_file_path, 'r') as f:
                    for line in f:
                        # Encrypt plaintext content
                        cipher = AES.new(key.encode(), AES.MODE_CBC, iv)
                        cipher_text = cipher.encrypt(pad(line.encode(), AES.block_size))

                        # Encode encrypted content in base64 and append to the list
                        base64_encoded_lines.append(base64.b64encode(cipher_text).decode('utf-8'))

                # Concatenate encrypted lines with newline characters
                base64_encoded = '\n'.join(base64_encoded_lines)

                # Save base64 encoded content to a file
                with open(base64_file_path, 'w') as f:
                    f.write(base64_encoded)

            
                # Read plaintext content from file
                with open(plaintext_file_path, 'r') as f:
                    plaintext_data = [line.strip().split('|') for line in f.readlines()]
                    f.seek(0)  # Reset file pointer to beginning
                    plaintext_data_all = f.read().splitlines()

                # Read plaintext content from file
                with open(base64_file_path, 'r') as f:
                    cipher_text_data = f.read().splitlines()

                context['combined_data'] = zip(plaintext_data, plaintext_data_all, cipher_text_data)
                context['qr_generate'] = zip(plaintext_data, cipher_text_data)
            except OSError as e:
                print(e.errno)
        return context"""
        
