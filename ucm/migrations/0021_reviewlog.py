# Generated by Django 3.1.5 on 2021-03-09 10:42

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ucm', '0020_auto_20210303_1358'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReviewLog',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notes', models.CharField(help_text='User log inforation ...', max_length=300)),
                ('cdate', models.DateTimeField(auto_now_add=True)),
                ('cuser', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('usernotem', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ucm.usernotem')),
            ],
        ),
    ]
