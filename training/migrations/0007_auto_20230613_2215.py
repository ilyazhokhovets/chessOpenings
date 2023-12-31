# Generated by Django 3.2 on 2023-06-13 22:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('training', '0006_auto_20230405_2124'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='trainingstats',
            name='successful_branch_runs',
        ),
        migrations.RemoveField(
            model_name='trainingstats',
            name='total_branch_runs',
        ),
        migrations.AlterField(
            model_name='trainingstats',
            name='successful_runs',
            field=models.IntegerField(default=0, verbose_name='successful_runs'),
        ),
        migrations.AlterField(
            model_name='trainingstats',
            name='total_runs',
            field=models.IntegerField(default=0, verbose_name='total_runs'),
        ),
    ]
