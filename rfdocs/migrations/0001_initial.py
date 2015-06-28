# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
from django.conf import settings
import model_utils.fields
import rfdocs.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='HtmlElement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, unique=True, null=True)),
                ('locator', models.TextField(help_text='Use xpath syntax.', verbose_name='Element to remove from HTML document', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='RFKeyword',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=256)),
                ('arguments', models.TextField(help_text='Keyword arguments.', null=True, blank=True)),
                ('documentation', models.TextField(help_text='Keyword documentation.', null=True, blank=True)),
            ],
            options={
                'ordering': ('name',),
                'verbose_name': 'Keyword',
                'verbose_name_plural': 'Keywords',
            },
        ),
        migrations.CreateModel(
            name='RFLibrary',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=64, db_index=True)),
                ('codename', models.CharField(help_text='Optionally define a codename.', max_length=64, null=True, blank=True)),
                ('slug', rfdocs.fields.AutoSlugField(help_text="Automatically built from the 'name' field. A slug is a short label generally used in URLs.", max_length=64, verbose_name='slug')),
            ],
            options={
                'ordering': ('name',),
                'verbose_name': 'Library',
                'verbose_name_plural': 'Libraries',
            },
        ),
        migrations.CreateModel(
            name='RFLibraryVersion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64)),
                ('slug', rfdocs.fields.AutoSlugField(help_text='Automatically built from the name. A slug is a short label generally used in URLs.', max_length=64, verbose_name='slug')),
                ('source_url', rfdocs.fields.ContentTypeRestrictedURLField(verbose_name='Source URL')),
                ('use_source_url', models.BooleanField(default=True, verbose_name='Use source URL as a location of library documentation')),
                ('original_doc', models.CharField(max_length=5242880, verbose_name='Original HTML document', blank=True)),
                ('parsed_doc', models.CharField(max_length=5242880, verbose_name='Parsed HTML document', blank=True)),
                ('parser', models.CharField(help_text='Select parser to be used for parsing the document.', max_length=64, verbose_name='Parser', choices=[('RobotFrameworkLibraryParser2_5', 'Robot Framework 2.5'), ('RobotFrameworkLibraryParser2_6', 'Robot Framework 2.6'), ('RobotFrameworkLibraryParser2_7', 'Robot Framework 2.7'), ('RobotFrameworkLibraryParser2_8', 'Robot Framework 2.8')])),
                ('clean_js', models.BooleanField(default=True, help_text='Use it for documents that were generated with JQuery Templates Plugin.', verbose_name='Clean JavaScript tags in HTML document.')),
                ('date_generated', models.DateTimeField(help_text=b'The timestamp from HTML document.', null=True, verbose_name='Document generated on', blank=True)),
                ('date_added', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='Date added', editable=False, db_index=True)),
                ('date_modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, help_text='The date and time when the library was last saved.', verbose_name='Date modified', editable=False, db_index=True)),
                ('date_deprecate', models.DateTimeField(help_text="Leave blank if the library should not be marked as 'Deprecated' in the future.", null=True, verbose_name='Deprecate date', blank=True)),
                ('status', model_utils.fields.StatusField(default=b'published', max_length=100, no_check_for_status=True, choices=[(b'published', 'Published'), (b'draft', 'Draft'), (b'deprecated', 'Deprecated')])),
                ('added_by', models.ForeignKey(editable=False, to=settings.AUTH_USER_MODEL, verbose_name='Added by user')),
                ('html_elements', models.ManyToManyField(help_text='HTML elements to remove from Library documentation.', related_name='+', to='rfdocs.HtmlElement', blank=True)),
                ('library', models.ForeignKey(related_name='versions', to='rfdocs.RFLibrary')),
                ('similar', models.ManyToManyField(related_name='similar_rel_+', verbose_name='Related Libraries', to='rfdocs.RFLibraryVersion', blank=True)),
            ],
            options={
                'get_latest_by': 'date_added',
                'ordering': ['-date_modified'],
                'verbose_name_plural': 'Versions',
                'verbose_name': 'Version',
            },
        ),
        migrations.CreateModel(
            name='RFTag',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=64, db_index=True)),
                ('slug', models.SlugField(help_text='Automatically built from the name. A slug is a short label generally used in URLs.', verbose_name='slug')),
            ],
            options={
                'ordering': ['-name'],
                'verbose_name': 'Tag',
                'verbose_name_plural': 'Tags',
            },
        ),
        migrations.AddField(
            model_name='rflibraryversion',
            name='tags',
            field=models.ManyToManyField(help_text='Tags.', related_name='versions', to='rfdocs.RFTag', blank=True),
        ),
        migrations.AddField(
            model_name='rfkeyword',
            name='version',
            field=models.ForeignKey(related_name='keywords', to='rfdocs.RFLibraryVersion'),
        ),
        migrations.AlterUniqueTogether(
            name='rflibraryversion',
            unique_together=set([('name', 'library')]),
        ),
        migrations.AlterIndexTogether(
            name='rflibraryversion',
            index_together=set([('name', 'library')]),
        ),
        migrations.AlterUniqueTogether(
            name='rfkeyword',
            unique_together=set([('name', 'version')]),
        ),
        migrations.AlterIndexTogether(
            name='rfkeyword',
            index_together=set([('name', 'version')]),
        ),
    ]
