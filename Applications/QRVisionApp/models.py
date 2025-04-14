from django.db import models


# Create your models here.
class PrivateKey(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True )
    private_key = models.CharField(max_length=100, unique=True)

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

    '''def save(self, *args, **kwargs):
        # Gabungkan nilai amount_before_tax, total_invoice_amount, dan tax_amount ke dalam plain_text
        self.plain_text = f"{self.amount_before_tax or ''} {self.total_invoice_amount or ''} {self.tax_amount or ''}".strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Invoice {self.invoice_number}"'''
