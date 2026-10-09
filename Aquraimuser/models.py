from django.db import models


class tb_register(models.Model):
    name = models.CharField(max_length=60)
    age = models.IntegerField()
    email = models.EmailField(max_length=100)
    password = models.CharField(max_length=128)  # stored hashed
    image = models.ImageField(upload_to='profile/', blank=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    KINDS = [('fish', 'Aquatic Life'), ('plant', 'Plants')]
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    kind = models.CharField(max_length=10, choices=KINDS, default='fish')
    image = models.ImageField(upload_to='categories/', blank=True)

    class Meta:
        verbose_name_plural = 'categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    old_price = models.DecimalField('MRP (optional)', max_digits=8, decimal_places=2, null=True, blank=True,
                                    help_text='Original price. Shows a discount badge when higher than the price.')
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='products/', blank=True)
    stock = models.PositiveIntegerField(default=10)
    featured = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.name

    @property
    def discount(self):
        if self.old_price and self.old_price > self.price:
            return int(round((self.old_price - self.price) / self.old_price * 100))
        return 0


class Order(models.Model):
    STATUS = [('placed', 'Placed'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled')]
    user = models.ForeignKey(tb_register, on_delete=models.CASCADE, related_name='orders')
    full_name = models.CharField(max_length=80)
    phone = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=60)
    pincode = models.CharField(max_length=10)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=12, choices=STATUS, default='placed')
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=120)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    quantity = models.PositiveIntegerField()

    @property
    def subtotal(self):
        return self.price * self.quantity



class BlogPost(models.Model):
    title = models.CharField(max_length=160)
    slug = models.SlugField(unique=True, blank=True)
    image = models.ImageField(upload_to='blogs/', blank=True)
    excerpt = models.CharField(max_length=240, blank=True)
    content = models.TextField()
    published = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.title


class ContactMessage(models.Model):
    name = models.CharField(max_length=80)
    email = models.EmailField()
    phone = models.CharField(max_length=15, blank=True)
    subject = models.CharField(max_length=120)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return f'{self.subject} - {self.name}'
