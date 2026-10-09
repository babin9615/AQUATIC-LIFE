from django import forms
from django.utils.text import slugify

from Aquraimuser.forms import BootstrapFormMixin
from Aquraimuser.models import BlogPost, Category, Product


def unique_slug(model, text, instance=None):
    base = slugify(text)[:45] or 'item'
    slug, n = base, 2
    qs = model.objects.all()
    if instance is not None and instance.pk:
        qs = qs.exclude(pk=instance.pk)
    while qs.filter(slug=slug).exists():
        slug = f'{base}-{n}'
        n += 1
    return slug


class ProductForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Product
        fields = ['category', 'name', 'price', 'old_price', 'stock', 'description', 'image', 'featured']
        widgets = {'description': forms.Textarea(attrs={'rows': 4}),
                   'price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
                   'old_price': forms.NumberInput(attrs={'step': '0.01', 'min': '0'})}
        labels = {'featured': 'Show as popular / featured'}

    def __init__(self, *args, kind=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].empty_label = '— choose a category —'
        if kind in ('fish', 'plant'):
            self.fields['category'].queryset = Category.objects.filter(kind=kind)
        if not self.instance.pk:
            self.fields['image'].required = True      # a new product must have a picture

    def clean(self):
        data = super().clean()
        p, old = data.get('price'), data.get('old_price')
        if p is not None and old is not None and old < p:
            self.add_error('old_price', 'MRP should be higher than the selling price (or leave it empty).')
        return data


class CategoryForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'kind', 'image']
        labels = {'kind': 'Type (fish or plant)'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['image'].required = True

    def save(self, commit=True):
        obj = super().save(commit=False)
        if not obj.slug:
            obj.slug = unique_slug(Category, obj.name, obj)
        if commit:
            obj.save()
        return obj


class BlogForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ['title', 'image', 'excerpt', 'content', 'published']
        widgets = {'content': forms.Textarea(attrs={'rows': 10}),
                   'excerpt': forms.TextInput(attrs={'placeholder': 'One-line summary shown on the blog list'})}
        labels = {'published': 'Published (visible on the website)'}

    def save(self, commit=True):
        obj = super().save(commit=False)
        if not obj.slug:
            obj.slug = unique_slug(BlogPost, obj.title, obj)
        if commit:
            obj.save()
        return obj
