from django import template
from urllib.parse import quote_plus
from django.db.models.fields.files import FieldFile
from django.utils.dateformat import format
import datetime, os
import base64

register = template.Library()

@register.filter
def get_field_value(obj, attr_name):
    # Mengambil nilai field dari objek model berdasarkan nama field (attr_name)
    value = getattr(obj, attr_name, None)
    #  Menangani FieldFile (misalnya ImageField atau FileField pada model)
    if isinstance(value, FieldFile):
        return os.path.basename(value.name)
    # Menangani datetime (mengonversi menjadi format yang lebih mudah dibaca)
    if isinstance(value, datetime.datetime):
        return format(value, 'd/m/Y H:i')
    # Menangani date (mengonversi menjadi format yang lebih mudah dibaca)
    if isinstance(value, datetime.date):
        # return value.strftime('%d-%b-%Y').upper()
        return format(value, 'd/m/Y')
    # Menangani boolean (mengonversi menjadi 'Yes'/'No')
    if isinstance(value, bool):
        return "YES" if value else "NO"
    # Menangani None (mengonversi menjadi '--')
    if value is None:
        return "--"
    return value

@register.filter
def startswith(value, arg):
    """Mengembalikan True jika 'value' dimulai dengan 'arg'."""
    if value:
        return value.startswith(arg)
    return False