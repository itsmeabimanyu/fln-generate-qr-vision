from django import forms
from .models import PrivateKey, Invoice

class PrivateKeyForm(forms.ModelForm):
    class Meta:
        model = PrivateKey
        fields = ['name', 'private_key']

        labels = {
            'private_key': 'Private Key *'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control mt-2 mb-3'})
            field.widget.attrs.update({'autocomplete': 'off'})

            # Menambahkan placeholder berdasarkan nama field
            if field_name == 'name':
                field.widget.attrs.update({'placeholder': 'Enter the name of the key'})
            elif field_name == 'private_key':
                field.widget.attrs.update({'placeholder': 'Enter the private key'})

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = ['private_key', 'invoice_number', 'amount_before_tax', 'total_invoice_amount', 'tax_amount', 'tax_number', 'plain_text']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control mt-2 mb-2'})
            field.widget.attrs.update({'autocomplete': 'off'})

            if field_name in ['amount_before_tax', 'total_invoice_amount', 'tax_amount']:
                field.widget.attrs.update({'class': 'form-control number-with-commas mt-2 mb-2'})

            if field_name == 'private_key':
                field.widget.attrs.update({'class': 'form-control form-select mt-2 mb-2'})

            if field_name == 'plain_text':
                field.widget.attrs.update({'readonly': 'readonly', 'style' : 'background: transparent !important; border: transparent;'})

        # Mengambil data private_key dari model PrivateKey dan mengubahnya menjadi tuple (id, private_key)
        self.fields['private_key'].choices = [
            (key.id, f"{key.private_key}") for key in PrivateKey.objects.all()
        ]

"""class InvoiceForm(forms.Form):
    class Meta:
        model = Invoice
        fields = ['invoice_number', 'amount_before_tax', 'total_invoice_amount', 'tax_amount', 'tax_number']


        labels = {
            'private_key': 'Private Key *'
        }
    private_key = forms.ChoiceField(choices=[], label="Private Key", widget=forms.Select(attrs={
        'class': 'form-control form-select ',  # Menambahkan class CSS
        'id': 'privateKeyDropdown',  # Kamu bisa menambahkan id juga jika diperlukan
    }))

    invoice_number = forms.CharField(
        label='Invoice Number',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Invoice Number',
            'autocomplete': 'off',
            'required': 'required'
        })
    )
    
    amount_before_tax = forms.IntegerField(
        label='Amount Before Tax',
        required=False,
        widget=forms.TextInput(attrs={'class': 'number-with-commas', 'placeholder': 'Enter amount before tax'})
    )

    total_invoice_amount = forms.IntegerField(
        label='Total Invoice Amount',
        required=False,
        widget=forms.TextInput(attrs={'class': 'number-with-commas', 'placeholder': 'Enter total invoice amount'})
    )

    tax_amount = forms.IntegerField(
        label='Tax Amount',
        required=False,
        widget=forms.TextInput(attrs={'class': 'number-with-commas', 'placeholder': 'Enter tax amount'})
    )

    tax_number = forms.CharField(
        label='Tax Number',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Tax Number',
            'autocomplete': 'off',
            'required': 'required'
        })
    )

    plain_text = forms.CharField(
        label='Concatenated Values',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'id': 'concatenatedValues',
            'name': 'plainText',
            'readonly': 'readonly'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Mengambil data private_key dari model PrivateKey dan mengubahnya menjadi tuple (id, private_key)
        self.fields['private_key'].choices = [
            (key.id, f"{key.private_key}") for key in PrivateKey.objects.all()
        ]
"""