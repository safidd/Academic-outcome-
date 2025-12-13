from django.contrib import admin
from .models import LearningOutcome, ProgramOutcome, ContributionRate


@admin.register(LearningOutcome)
class LearningOutcomeAdmin(admin.ModelAdmin):
    list_display = ('code', 'course', 'description')
    list_filter = ('course',)
    search_fields = ('code', 'description', 'course__code', 'course__name')


@admin.register(ProgramOutcome)
class ProgramOutcomeAdmin(admin.ModelAdmin):
    list_display = ('code', 'description')
    search_fields = ('code', 'description')


@admin.register(ContributionRate)
class ContributionRateAdmin(admin.ModelAdmin):
    list_display = ('learning_outcome', 'program_outcome', 'percentage')
    list_filter = ('program_outcome', 'learning_outcome__course')
    search_fields = ('learning_outcome__code', 'program_outcome__code')
