# Generated by Django 5.1.5 on 2025-02-05 11:36

import django.db.models.deletion
import mptt.fields
import products.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Brand',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=15, unique=True)),
                ('description', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name_sort', models.CharField(blank=True, editable=False, max_length=15)),
                ('popularity', models.PositiveIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Brand',
                'verbose_name_plural': 'Brands',
                'ordering': ['name_sort'],
                'indexes': [models.Index(fields=['created_at'], name='products_br_created_61604d_idx'), models.Index(fields=['name_sort'], name='products_br_name_so_f0a4f1_idx')],
            },
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=15, unique=True, validators=[products.validators.validate_name])),
                ('slug', models.SlugField(blank=True, max_length=20, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('top_level_category', models.CharField(blank=True, choices=[('shoes', 'Shoes'), ('clothing', 'Clothing'), ('accessories', 'Accessories'), ('electronics', 'Electronics'), ('home', 'Home'), ('toys', 'Toys'), ('beauty', 'Beauty'), ('food', 'Food'), ('books', 'Books'), ('sports', 'Sports'), ('outdoors', 'Outdoors'), ('automotive', 'Automotive'), ('music', 'Music'), ('games', 'Games'), ('art', 'Art'), ('collectibles', 'Collectibles'), ('other', 'Other')], help_text='Required only for top-level categories', max_length=20, null=True)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('active', 'active'), ('inactive', 'inactive'), ('archived', 'Archived')], default='active', max_length=20)),
                ('order', models.PositiveIntegerField(default=0, editable=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('lft', models.PositiveIntegerField(editable=False)),
                ('rght', models.PositiveIntegerField(editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(editable=False)),
                ('parent', mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='products.category')),
            ],
            options={
                'verbose_name_plural': 'Categories',
                'ordering': ['order'],
                'indexes': [models.Index(fields=['name'], name='products_ca_name_693421_idx'), models.Index(fields=['parent'], name='products_ca_parent__f3c24e_idx'), models.Index(fields=['status'], name='products_ca_status_f9f890_idx'), models.Index(fields=['order'], name='products_ca_order_ac6215_idx')],
            },
        ),
    ]
