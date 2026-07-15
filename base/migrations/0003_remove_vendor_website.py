from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0002_alter_vendor_user'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='vendor',
            name='website',
        ),
    ]
