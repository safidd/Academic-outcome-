# Generated migration for snapshot isolation feature

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('grades', '0002_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Add timestamps to Grade model
        migrations.AddField(
            model_name='grade',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='grade',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        # Add indexes for performance
        migrations.AddIndex(
            model_name='grade',
            index=models.Index(fields=['created_at'], name='grades_grad_created_idx'),
        ),
        migrations.AddIndex(
            model_name='grade',
            index=models.Index(fields=['updated_at'], name='grades_grad_updated_idx'),
        ),
        migrations.AddIndex(
            model_name='grade',
            index=models.Index(fields=['course', 'created_at'], name='grades_grad_course_created_idx'),
        ),
        # Create GradeAuditLog model
        migrations.CreateModel(
            name='GradeAuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('snapshot_time', models.DateTimeField(help_text='Point in time snapshot used for the report')),
                ('accessed_at', models.DateTimeField(auto_now_add=True, help_text='When the report was accessed')),
                ('report_type', models.CharField(default='grade_audit', help_text='Type of report generated', max_length=50)),
                ('filters_applied', models.JSONField(blank=True, default=dict, help_text='Filters applied to the report (course, date range, etc.)')),
                ('records_count', models.IntegerField(default=0, help_text='Number of records in the snapshot')),
                ('accessed_by', models.ForeignKey(limit_choices_to={'role': 'department_head'}, on_delete=django.db.models.deletion.CASCADE, related_name='grade_audit_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-accessed_at'],
            },
        ),
        migrations.AddIndex(
            model_name='gradeauditlog',
            index=models.Index(fields=['accessed_by', 'accessed_at'], name='grades_grad_accessed_idx'),
        ),
        migrations.AddIndex(
            model_name='gradeauditlog',
            index=models.Index(fields=['snapshot_time'], name='grades_grad_snapshot_idx'),
        ),
    ]

