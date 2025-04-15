import base64
from django.db import models
from django.utils import timezone
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

# Create your models here.
class PrivateKey(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True )
    private_key = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.private_key}"

class Invoice(models.Model):
    private_key = models.ForeignKey(PrivateKey, on_delete=models.CASCADE)
    invoice_number = models.CharField(max_length=100)
    amount_before_tax = models.CharField(max_length=100)
    total_invoice_amount = models.CharField(max_length=100)
    tax_amount = models.CharField(max_length=100)
    tax_number = models.CharField(max_length=100)
    plain_text = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    cipher_text = models.CharField(max_length=255)

    def save(self, *args, **kwargs):
        key = self.private_key.private_key  # secret key
        iv = b'\0' * 16  # Default zero based bytes[16]
        # Pad the content
        msg = pad(self.plain_text.encode(), AES.block_size)
        # Create AES cipher object
        cipher = AES.new(key.encode(), AES.MODE_CBC, iv)
        # Encrypt the content
        cipher_text = cipher.encrypt(msg)
        # Encode the encrypted content in base64
        base64_encoded = base64.b64encode(cipher_text).decode('utf-8')
        self.cipher_text = base64_encoded
        super().save(*args, **kwargs)

    '''def save(self, *args, **kwargs):
        # Gabungkan nilai amount_before_tax, total_invoice_amount, dan tax_amount ke dalam plain_text
        self.plain_text = f"{self.amount_before_tax or ''} {self.total_invoice_amount or ''} {self.tax_amount or ''}".strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Invoice {self.invoice_number}"'''
