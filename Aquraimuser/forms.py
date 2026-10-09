from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from .models import ContactMessage, tb_register


def validate_image_size(f):
    limit = getattr(settings, 'MAX_UPLOAD_MB', 5)
    if f and f.size > limit * 1024 * 1024:
        raise ValidationError(f'Image must be smaller than {limit} MB.')


class BootstrapFormMixin:
    """Gives every widget the right Bootstrap 5 class and marks invalid fields."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            w = field.widget
            if isinstance(w, forms.CheckboxInput):
                css = 'form-check-input'
            elif isinstance(w, (forms.Select, forms.SelectMultiple)):
                css = 'form-select'
            else:
                css = 'form-control'
            w.attrs['class'] = (w.attrs.get('class', '') + ' ' + css).strip()
            if isinstance(field, forms.ImageField):
                field.validators.append(validate_image_size)
                w.attrs.setdefault('accept', 'image/*')

    def full_clean(self):
        super().full_clean()
        for name in self.errors:
            w = self.fields[name].widget
            if 'is-invalid' not in w.attrs.get('class', ''):
                w.attrs['class'] = w.attrs.get('class', '') + ' is-invalid'


phone_validator = RegexValidator(r'^\+?[0-9 ]{10,15}$', 'Enter a valid phone number (10-15 digits).')
pin_validator = RegexValidator(r'^[0-9]{6}$', 'Enter a valid 6-digit pincode.')


class RegisterForm(BootstrapFormMixin, forms.Form):
    name = forms.CharField(max_length=60, min_length=2, label='Full name',
                           widget=forms.TextInput(attrs={'placeholder': 'Your name', 'autocomplete': 'name'}))
    age = forms.IntegerField(min_value=5, max_value=110,
                             widget=forms.NumberInput(attrs={'placeholder': 'Your age'}))
    email = forms.EmailField(max_length=100,
                             widget=forms.EmailInput(attrs={'placeholder': 'you@example.com', 'autocomplete': 'email'}))
    password = forms.CharField(min_length=6, widget=forms.PasswordInput(
        attrs={'placeholder': 'At least 6 characters', 'autocomplete': 'new-password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(
        attrs={'placeholder': 'Repeat password', 'autocomplete': 'new-password'}))
    image = forms.ImageField(required=False, label='Profile photo (optional)')

    def clean_email(self):
        email = self.cleaned_data['email'].strip()
        if tb_register.objects.filter(email__iexact=email).exists():
            raise ValidationError('That email is already registered. Try logging in.')
        return email

    def clean(self):
        data = super().clean()
        if data.get('password') and data.get('confirm_password') and data['password'] != data['confirm_password']:
            self.add_error('confirm_password', 'Passwords do not match.')
        return data


class ContactForm(BootstrapFormMixin, forms.ModelForm):
    phone = forms.CharField(required=False, max_length=15, validators=[phone_validator], label='Phone (optional)')

    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Your name'}),
            'email': forms.EmailInput(attrs={'placeholder': 'you@example.com'}),
            'subject': forms.TextInput(attrs={'placeholder': 'How can we help?'}),
            'message': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Write your message...'}),
        }


class CheckoutForm(BootstrapFormMixin, forms.Form):
    full_name = forms.CharField(max_length=80)
    phone = forms.CharField(max_length=15, validators=[phone_validator])
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}))
    city = forms.CharField(max_length=60)
    pincode = forms.CharField(max_length=6, validators=[pin_validator])


class ProfileForm(BootstrapFormMixin, forms.Form):
    name = forms.CharField(max_length=60, min_length=2)
    age = forms.IntegerField(min_value=5, max_value=110)
    image = forms.ImageField(required=False, label='Profile photo')
    current_password = forms.CharField(required=False, widget=forms.PasswordInput(attrs={'autocomplete': 'current-password'}))
    new_password = forms.CharField(required=False, min_length=6, widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}))

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean(self):
        from django.contrib.auth.hashers import check_password
        data = super().clean()
        if data.get('new_password') and not check_password(data.get('current_password') or '', self.user.password):
            self.add_error('current_password', 'Current password is incorrect.')
        return data
