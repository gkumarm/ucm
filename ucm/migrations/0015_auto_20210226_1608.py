# Generated by Django 3.1.5 on 2021-02-26 12:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ucm', '0014_userlearningdeck'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='userlearningdeck',
            name='currdeck',
        ),
        migrations.RemoveField(
            model_name='userlearningdeck',
            name='notem',
        ),
        migrations.RemoveField(
            model_name='userlearningdeck',
            name='usertopic',
        ),
        migrations.AddField(
            model_name='userlearningdeck',
            name='usernotem',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='ucm.usernotem'),
            preserve_default=False,
        ),
    ]