# Generated by Django 3.1.5 on 2021-02-19 18:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ucm', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='notem',
            name='topic',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='ucm.topic'),
            preserve_default=False,
        ),
    ]