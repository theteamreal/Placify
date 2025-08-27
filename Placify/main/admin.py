from django.contrib import admin
from .models import ResumeGeneration, ATSAnalysis
from django.shortcuts import render, redirect
from django.contrib import messages

@admin.register(ResumeGeneration)
class ResumeGenerationAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'target_position', 'estimated_ats_score', 'created_at']
    list_filter = ['target_industry', 'created_at', 'estimated_ats_score']
    search_fields = ['full_name', 'email', 'target_position']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'full_name', 'email', 'target_position', 'target_industry')
        }),
        ('Content', {
            'fields': ('job_description', 'generated_resume'),
            'classes': ('collapse',)
        }),
        ('ATS Metrics', {
            'fields': ('estimated_ats_score', 'keywords_matched')
        }),
        ('Metadata', {
            'fields': ('form_data', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ATSAnalysis)
class ATSAnalysisAdmin(admin.ModelAdmin):
    list_display = ['resume_generation', 'keyword_density', 'readability_score', 'created_at']
    list_filter = ['created_at', 'readability_score']
    readonly_fields = ['created_at']

# Additional view functions for history and detail
def resume_history(request):
    """Display user's resume generation history"""
    if request.user.is_authenticated:
        resumes = ResumeGeneration.objects.filter(user=request.user)
    else:
        # For anonymous users, show session-based history
        session_resumes = request.session.get('resume_history', [])
        resumes = ResumeGeneration.objects.filter(id__in=session_resumes)
    
    context = {'resumes': resumes}
    return render(request, 'resume_history.html', context)

def resume_detail(request, pk):
    """Display detailed view of a specific resume"""
    try:
        if request.user.is_authenticated:
            resume = ResumeGeneration.objects.get(pk=pk, user=request.user)
        else:
            # Check if resume ID is in session history
            session_resumes = request.session.get('resume_history', [])
            if pk not in session_resumes:
                messages.error(request, 'Resume not found or access denied.')
                return redirect('resume_history')
            resume = ResumeGeneration.objects.get(pk=pk)
        
        # Get ATS analysis if available
        ats_analysis = None
        try:
            ats_analysis = ATSAnalysis.objects.get(resume_generation=resume)
        except ATSAnalysis.DoesNotExist:
            pass
        
        context = {
            'resume': resume,
            'ats_analysis': ats_analysis
        }
        return render(request, 'resume_detail.html', context)
        
    except ResumeGeneration.DoesNotExist:
        messages.error(request, 'Resume not found.')
        return redirect('resume_history')