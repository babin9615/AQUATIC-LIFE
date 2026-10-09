import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [('Aquraimuser', '0003_alter_category_image_alter_category_slug')]

    operations = [
        migrations.AlterModelOptions(name='category', options={'ordering': ['name'], 'verbose_name_plural': 'categories'}),
        migrations.AlterField(model_name='tb_register', name='password', field=models.CharField(max_length=128)),
        migrations.RemoveField(model_name='category', name='image'),
        migrations.AddField(model_name='category', name='image', field=models.ImageField(blank=True, upload_to='categories/')),
        migrations.AddField(model_name='category', name='kind', field=models.CharField(choices=[('fish', 'Aquatic Life'), ('plant', 'Plants')], default='fish', max_length=10)),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('price', models.DecimalField(decimal_places=2, max_digits=8)),
                ('description', models.TextField(blank=True)),
                ('image', models.ImageField(blank=True, upload_to='products/')),
                ('stock', models.PositiveIntegerField(default=10)),
                ('featured', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='Aquraimuser.category')),
            ],
            options={'ordering': ['-created']},
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('full_name', models.CharField(max_length=80)),
                ('phone', models.CharField(max_length=15)),
                ('address', models.TextField()),
                ('city', models.CharField(max_length=60)),
                ('pincode', models.CharField(max_length=10)),
                ('total', models.DecimalField(decimal_places=2, max_digits=10)),
                ('status', models.CharField(choices=[('placed', 'Placed'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled')], default='placed', max_length=12)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='Aquraimuser.tb_register')),
            ],
            options={'ordering': ['-created']},
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('price', models.DecimalField(decimal_places=2, max_digits=8)),
                ('quantity', models.PositiveIntegerField()),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='Aquraimuser.order')),
                ('product', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='Aquraimuser.product')),
            ],
        ),
    ]
