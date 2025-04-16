from django.conf import settings
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, TemplateView, View, ListView
from django.contrib.auth.views import LoginView
from django_auth_ldap.backend import LDAPBackend
from django.contrib.auth import login, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin

import base64
import io, ldap
import qrcode  # pip install qrcode

from .forms import InvoiceForm, PrivateKeyForm, CustomLoginForm, RegisterAccountForm
from .models import Invoice, PrivateKey, CustomUserLogin

class Template404View(TemplateView):
    template_name = "404.html"

# forbiden
class Template403View(TemplateView):
    template_name = "403.html"

# Chapter: Login
class LoginView(LoginView):
    template_name = 'layouts/base_login.html'
    success_url = reverse_lazy('/')
    form_class = CustomLoginForm 

    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated and self.request.user.is_active:
            return redirect(self.success_url)  # Redirect to the home page if already authenticated
        return super().get(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["text_submit"] = "Login"
        return context

    def form_valid(self, form):
        # Pertama coba autentikasi LDAP
        ldap_backend = LDAPBackend()
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')

        user = None
        try:
            user = ldap_backend.authenticate(self.request, username=username, password=password)
        except ldap.LDAPError as e:
            # Set pesan kesalahan untuk debugging
            print(f"LDAP authentication error: {e}")

        # Jika autentikasi LDAP gagal, coba autentikasi lokal
        if user is None:
            user = authenticate(self.request, username=username, password=password)

        if user is not None:
            login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect(self.get_success_url())
        else:
            # Tambahkan pesan kesalahan dan kembalikan form yang tidak valid
            return self.form_invalid(form)

    def form_invalid(self, form):
        # Set pesan kesalahan untuk pengguna    
        messages.error(self.request, 'Login failed. Please check your username and password!')
        return super().form_invalid(form)

    """
    def form_valid(self, form):
        # Cek login biasa (menggunakan database lokal)
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        
        user = authenticate(self.request, username=username, password=password)
        if user is not None:
            login(self.request, user)
            return super().form_valid(form)
        else:
            # Jika login biasa gagal, coba autentikasi menggunakan LDAP
            ldap_user = self.authenticate_ldap(username, password)
            if ldap_user:
                # Jika login LDAP sukses, buat/mendapatkan user dari LDAP
                user = self.create_or_get_user_from_ldap(username)
                login(self.request, user)
                return super().form_valid(form)
            else:
                form.add_error(None, 'Invalid credentials.')
                return self.form_invalid(form)

    def authenticate_ldap(self, username, password):
        try:
            ldap_connection = ldap.initialize(settings.LDAP_SERVER)
            ldap_connection.simple_bind_s(f"uid={username},ou=users,dc=example,dc=com", password)
            return True  # Jika bind berhasil, dianggap login sukses
        except ldap.LDAPError:
            return False  # Jika gagal, return False
    """
    
class LogoutView(View):
    def get(self, request, *args, **kwargs):
        # logout(request)
        request.session.flush()
        return redirect(settings.LOGOUT_REDIRECT_URL)

# *Untuk testing non ldap (disable saat produksi)
class RegisterAccount(CreateView):
    template_name = 'pages/create_regular.html'
    model = CustomUserLogin
    form_class = RegisterAccountForm
    success_url = reverse_lazy('account_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['card_title'] = 'Register Account'
        return context
    
    def form_valid(self, form):
        form.instance.is_superuser = True
        form.instance.registered = True
        # Menambahkan pesan success
        messages.success(self.request, 'Form submitted successfully!')
        # Anda bisa melanjutkan ke URL sukses
        return super().form_valid(form)
    
    def form_invalid(self, form):
        # Pesan untuk form yang invalid
        messages.error(self.request, 'Form submission failed. Please check the fields.')
        return super().form_invalid(form)
    
# Chapter Register for development
"""class RegisterView(CreateView):
    form_class = RegisterForm  # Form yang digunakan
    template_name = 'layouts/base_login.html'  # Template untuk form registrasi
    success_url = reverse_lazy('event_dashboard')  # URL tujuan setelah registrasi berhasil

    def form_valid(self, form):
        # Simpan user
        user = form.save()

        # Tentukan backend autentikasi secara manual
        user.backend = 'django.contrib.auth.backends.ModelBackend'

        # Login pengguna
        login(self.request, user)

        # Redirect ke halaman sukses
        return redirect(self.success_url)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["text_submit"] = "Register"
        return context"""

# Chapter Authorization
class BaseRequiredMixin(LoginRequiredMixin):
    """Mixin dasar untuk mengecek apakah user aktif dan sudah terdaftar"""
    def dispatch(self, request, *args, **kwargs):
        # First, check if the user is authenticated
        if request.user.is_authenticated:
            if not (request.user.is_active and request.user.registered):
                return redirect('403_view')
        return super().dispatch(request, *args, **kwargs)
    
class SuperuserRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Check if the user registered and superuser
        if not request.user.registered or not request.user.is_superuser:
            return redirect('403_view')
        
        return super().dispatch(request, *args, **kwargs)
 
class AccountListView(SuperuserRequiredMixin, ListView):
    template_name = 'pages/create_regular.html'
    model = CustomUserLogin
    context_object_name ='items'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['fields'] = {
            'username': 'Username',
            'email': 'Email',
            'registered': 'Registered',
            'is_superuser': 'Superuser Status',
        }

        # Tambah tombol ke tiap baris data
        for item in context['items']:
            item.buttons_action = [
                f"""
                <button type="button" data-bs-toggle="modal" data-bs-target="#modal-first-{item.id}"
                {'class="btn btn-danger mb-1 w-100"><i class="icon-logout me-2"></i>Unregister' if item.registered 
                 else 'class="btn btn-primary mb-1 w-100"><i class="icon-login me-2"></i>Register'}</button>
                """, 
                f"""
                <button type="button" data-bs-toggle="modal" data-bs-target="#modal-second-{item.id}" {'' if item.registered else 'disabled'}
                {'class="btn btn-danger w-100"><i class="fa fa-user-alt-slash mb-1 me-2"></i>Revoke Superuser' if item.is_superuser 
                 else 'class="btn btn-primary w-100"><i class="fas fa-user-cog mb-1 me-2"></i>Make Superuser'}</button>
                """
            ]

            # Content modal
            item.modals_form = {
                'Unregister Account' if item.registered else 'Register Account': {
                    'modal_id': f'modal-first-{item.id}',
                    'action_url': reverse('account_mark_register', kwargs={'pk': item.id}),
                    'action_button': f'<button type="submit" class="btn btn-danger">Unregister</button>' if item.registered else '<button type="submit" class="btn btn-primary">Register</button>',
                    'info': f'<p class="fw-bolder text-secondary">{item}</p>'
                },
                'Unset as Superuser' if item.is_superuser else 'Set as Superuser': {
                    'modal_id': f'modal-second-{item.id}',
                    'action_url': reverse('account_mark_superuser', kwargs={'pk': item.id}),
                    'action_button': f'<button type="submit" class="btn btn-danger">Unset as Superuser</button>' if item.is_superuser else '<button type="submit" class="btn btn-primary">Set as Superuser</button>',
                    'info': f'<p class="fw-bolder text-secondary">{item}</p>'
                }
            }
        return context

class RegisterMarkStatusView(View):
    def post(self, request, pk):
        item = get_object_or_404(CustomUserLogin, pk=pk)
        if item.registered:
            item.registered = False
        else:
            item.registered = True
        item.save()
        messages.success(request, "The account has been successfully changed.")
        return redirect(reverse_lazy('account_list'))
    
class SuperuserMarkStatusView(View):
    def post(self, request, pk):
        item = get_object_or_404(CustomUserLogin, pk=pk)
        if item.registered:
            if item.is_superuser:
                item.is_superuser = False
            else:
                item.is_superuser = True
            item.save()
            messages.success(request, "The account has been successfully changed.")
        else:
            messages.error(request, "To modify an account, you must be registered first.")

        return redirect(reverse_lazy('account_list'))

class CreatePrivateKeyView(BaseRequiredMixin, CreateView):
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
        form.instance.created_by = self.request.user
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

class CreateManualInvoiceView(BaseRequiredMixin, TemplateView):
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
                    plain_text=plain_text,
                    created_by = self.request.user
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

