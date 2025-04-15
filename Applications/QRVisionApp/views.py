from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, TemplateView, View

import base64
import io
import qrcode  # pip install qrcode

from .forms import InvoiceForm, PrivateKeyForm
from .models import Invoice, PrivateKey

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
                f"<button type='button' data-bs-toggle='modal' data-bs-target='#modal-first-{item.id}' class='btn btn-danger w-100'><i class='fas fa-trash me-2'></i>Delete</button>"
            ]

            # Content modal
            item.modals_form = {
                'Delete Item': {
                    'modal_id': f'modal-first-{item.id}',
                    'action_url': reverse('key_delete', kwargs={'pk': item.id}),
                    'action_button': f'<button type="submit" class="btn btn-danger">Delete</button>',
                    'info': f'<p class="fw-bolder text-secondary">{item.private_key}</p>'
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

class CreateManualInvoiceView(TemplateView):
    template_name = 'pages/create.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['card_title'] = 'Manual Input Invoice'

        context['buttons_action'] = f"""
            <button type="submit" name="action" value="print" class="btn btn-secondary" id="print-button"><i class="fas fa-print me-2 "></i>Print</button>
            <button type="button" data-bs-toggle="modal" data-bs-target="#modal-first" class="btn btn-danger" id="delete-button" ><i class="fas fa-trash me-2 "></i>Delete</button>
            """
        
        context['act_modal'] = {
            'Delete Item': {
                'modal_id': f'modal-first',
                'action_button': f'<button type="submit" name="action" value="delete" class="btn btn-danger" id="delete-modal-button">Delete</button>',
            }
        }
        context['form'] = InvoiceForm
        items = Invoice.objects.all()
        context['additionals_button'] = f"<button type='button' class='btn ms-2 btn-secondary' onclick='window.location.href=\"{reverse('key_create')}\"'><i class='fa fa-plus me-2'></i>Private Key</button>"
        
        # Tambah tombol ke tiap baris data
        for item in items:
            item.buttons_action = [
                f"<button type='button' data-bs-toggle='modal' data-bs-target='#modal-first-{item.id}' class='btn btn-danger w-100'><i class='fas fa-trash me-2'></i>Delete</button>"
            ]

            # Content modal
            item.modals_form = {
                'Delete Item': {
                    'modal_id': f'modal-first-{item.id}',
                    'action_url': reverse('invoice_delete_manual', kwargs={'pk': item.id}),
                    'action_button': f'<button type="submit" class="btn btn-danger">Delete</button>',
                    'info': f'<p class="fw-bolder text-secondary">Invoice {item.invoice_number}</p>'
                }
            }

        context['items'] = items
        return context
    
    def post(self, request, *args, **kwargs):
        if self.request.POST.get('action') == 'save':
            private_keys = self.request.POST.getlist('private_key')
            invoice_numbers = self.request.POST.getlist('invoice_number')
            amount_before_taxs = self.request.POST.getlist('amount_before_tax')
            total_invoice_amounts = self.request.POST.getlist('total_invoice_amount')
            tax_amounts = self.request.POST.getlist('tax_amount')
            tax_numbers = self.request.POST.getlist('tax_number')
            plain_texts = self.request.POST.getlist('plain_text')

            for private_key, invoice_number, amount_before_tax, total_invoice_amount, tax_amount, tax_number, plain_text  in zip(private_keys, invoice_numbers, amount_before_taxs, total_invoice_amounts, tax_amounts, tax_numbers, plain_texts):
                Invoice.objects.create(
                    private_key=get_object_or_404(PrivateKey, pk=private_key),
                    invoice_number=invoice_number,
                    amount_before_tax=amount_before_tax,
                    total_invoice_amount=total_invoice_amount,
                    tax_amount=tax_amount,
                    tax_number=tax_number,
                    plain_text=plain_text
                )

            messages.success(self.request, 'Invoice added successfully!')
            return redirect(self.request.META.get('HTTP_REFERER'))
            
        elif self.request.POST.get('action') == 'print':
            # Mendapatkan ID yang dipilih dari checkbox
            selected_ids = self.request.POST.getlist('select')
            invoices = Invoice.objects.filter(id__in=selected_ids)
            qr_data = []
            for invoice in invoices:
                qr = qrcode.make(invoice.cipher_text)  # Contoh: data QR dari private_key
                buffer = io.BytesIO()
                qr.save(buffer, format="PNG")
                img_str = base64.b64encode(buffer.getvalue()).decode()
                qr_data.append({
                    'invoice': f'INVOICE_{invoice.invoice_number}',
                    'qr_base64': img_str
                })

            return render(request, 'pages/qr_print.html', {'qr_data': qr_data})
        
        elif self.request.POST.get('action') == 'delete':
            # Mendapatkan ID yang dipilih dari checkbox
            selected_ids = self.request.POST.getlist('select')
            Invoice.objects.filter(id__in=selected_ids).delete()
            messages.success(request, "The item has been successfully deleted.")
            return redirect(self.request.META.get('HTTP_REFERER'))

    def form_invalid(self, form):
        # Form is invalid, display an error message
        response = super().form_invalid(form)
        messages.error(self.request, 'There was an error creating the Invoice. Please check the form and try again.')
        return response

    # Optional: You can define success_url to redirect after form submission
    def get_success_url(self):
        # Redirect to a specific page after a successful form submission
        return reverse_lazy('invoice_create_manual')  # Replace with the name of the URL for your list page or another page.

class DeleteInvoiceView(View):
    def post(self, request, pk):
        item = get_object_or_404(Invoice, pk=pk)
        item.delete()
        messages.success(request, "The item has been successfully deleted.")
        return redirect(reverse_lazy('invoice_create_manual'))

