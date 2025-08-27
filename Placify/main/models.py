from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import User
import json

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    student_id = models.CharField(max_length=20)
    
    class Meta:
        verbose_name = 'Student'
    
    def __str__(self):
        return f"{self.user.username} - {self.student_id}"

class ResumeGeneration(models.Model):
    """Store resume generation history and data"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    target_position = models.CharField(max_length=200)
    target_industry = models.CharField(max_length=200, blank=True)
    
    # Store form data as JSON
    form_data = models.JSONField()
    job_description = models.TextField()
    generated_resume = models.TextField()
    
    # ATS optimization metrics
    estimated_ats_score = models.IntegerField(default=0)
    keywords_matched = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.full_name} - {self.target_position}"

class ATSAnalysis(models.Model):
    """Store ATS analysis results"""
    resume_generation = models.OneToOneField(ResumeGeneration, on_delete=models.CASCADE)
    extracted_keywords = models.JSONField(default=list)
    required_skills = models.JSONField(default=list)
    recommendations = models.JSONField(default=list)
    keyword_density = models.FloatField(default=0.0)
    readability_score = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"ATS Analysis for {self.resume_generation.full_name}"
