from decimal import Decimal
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from Aquraimuser.models import BlogPost, Category, Product

IMG = Path(__file__).resolve().parents[2] / 'static' / 'images'
# (category, kind, image file, [(product, price, mrp or None)])
DATA = [
    ('Angelfish', 'fish', 'angel fish.jpg', [('Silver Angelfish', 150, 200), ('Koi Angelfish', 350, None)]),
    ('Apistogramma', 'fish', 'Apistogramma.jpg', [('Apistogramma Cacatuoides', 450, 550)]),
    ('Badis Fish', 'fish', 'Badis Fish.jpg', [('Blue Badis', 280, None)]),
    ('Barbs', 'fish', 'barb.jpg', [('Tiger Barb', 60, 80), ('Cherry Barb', 70, None)]),
    ('Betta Fish', 'fish', 'Betta fish.jpg', [('Halfmoon Betta', 250, 300), ('Plakat Betta', 180, None)]),
    ('Crayfish', 'fish', 'Cray fish.jpg', [('Blue Crayfish', 600, None)]),
    ('Discus Fish', 'fish', 'Discuss fish.jpg', [('Red Melon Discus', 1800, 2200)]),
    ('Dwarf Cichlids', 'fish', 'Dwarf Cichlid fish.jpg', [('German Blue Ram', 320, None)]),
    ('Exotic Guppies', 'fish', 'exotic guppies.jpg', [('Moscow Blue Guppy (pair)', 120, 150), ('Dumbo Ear Guppy (pair)', 150, None)]),
    ('Aquatic Plants', 'plant', 'p1.jpg', [('Anubias Nana', 140, 180), ('Java Fern', 110, None)]),
    ('Plant Carpets', 'plant', 'Aqu plant.jpg', [('Dwarf Hairgrass Tray', 350, None)]),
]

BLOGS = [
    ('How to acclimatise new fish the right way', 'aq1.jpg',
     'A simple 20-minute routine that dramatically reduces stress when you bring new fish home.',
     'Bringing new fish home is exciting, but the first hour matters most.\n\n'
     'Turn off the tank light and float the sealed bag on the surface for 20 minutes so the temperature matches.\n\n'
     'Open the bag and add a small cup of tank water every five minutes, three or four times. This slowly adjusts the fish to your water chemistry.\n\n'
     'Finally, net the fish into the tank. Do not pour the bag water in. Keep lights dim and skip feeding for the first few hours.'),
    ('5 beginner-friendly aquatic plants', 'p1.jpg',
     'No CO2, no fancy lighting: these plants thrive in almost any tank.',
     'Planted tanks look beautiful and keep water cleaner.\n\n'
     'Anubias Nana and Java Fern are tied to wood or rock instead of planted in gravel, and tolerate low light.\n\n'
     'Fast-growing stem plants soak up excess nutrients and help prevent algae.\n\n'
     'Start with two or three species, trim regularly and add more as you gain confidence.'),
    ('Betta care: tank size, food and tank mates', 'Betta fish.jpg',
     'Bettas are hardy but not hardy enough for tiny bowls. Here is what they really need.',
     'A 20-litre tank with a gentle filter and a heater is a good start for one betta.\n\n'
     'Feed a quality pellet once or twice a day, only what is eaten in two minutes.\n\n'
     'Choose peaceful tank mates only, and keep only one male per tank.'),
]


def attach(field, name):
    with open(IMG / name, 'rb') as fh:
        field.save(name.replace(' ', '_'), File(fh), save=False)


class Command(BaseCommand):
    help = 'Load sample categories, products and blog posts using the bundled images.'

    def handle(self, *a, **kw):
        for cname, kind, img, prods in DATA:
            cat, new = Category.objects.get_or_create(slug=slugify(cname), defaults={'name': cname, 'kind': kind})
            if new:
                attach(cat.image, img)
                cat.save()
            for i, (pname, price, mrp) in enumerate(prods):
                p, pnew = Product.objects.get_or_create(
                    category=cat, name=pname,
                    defaults={'price': Decimal(price), 'old_price': Decimal(mrp) if mrp else None, 'stock': 20,
                              'featured': i == 0,
                              'description': f'Healthy, quarantined {pname}. Live arrival guaranteed.'})
                if pnew:
                    attach(p.image, img)
                    p.save()
        for title, img, excerpt, content in BLOGS:
            b, new = BlogPost.objects.get_or_create(slug=slugify(title)[:45], defaults={
                'title': title, 'excerpt': excerpt, 'content': content})
            if new:
                attach(b.image, img)
                b.save()
        self.stdout.write(self.style.SUCCESS('Seeded categories, products and blog posts.'))
