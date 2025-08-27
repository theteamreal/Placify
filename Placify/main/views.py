from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.conf import settings
import json
import os
from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
from langchain.llms import OpenAI
from typing import List, Dict, Any
import re
from datetime import datetime
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from .models import *


def home(request):
    return render(request, 'home.html')
def login_page(request):
    if request.method== "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not User.objects.filter(username = username).exists():
             messages.info(request, 'Invalid Data')
             return redirect('/login/')
        user = authenticate(username = username, password = password)

        if user is None:
             messages.info(request, 'Invalid Data')
             return redirect('/home/')
        else :
            login(request, user)
            return redirect('/home/')

    return render(request, 'login.html')
    
def register_page(request):

    if request.method== "POST":
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = User.objects.filter(username = username)
        if user.exists():
            messages.info(request, 'Username already Taken')
            return redirect('/register/')

        user=User.objects.create(
            first_name = first_name,
            last_name = last_name,
            username = username,
        )
        user.set_password(password)
        user.save()


        messages.info(request, 'Account Created Successfully')

        return redirect("/login/")

    return render(request, 'register.html')

def logout_page(request):
    logout(request)
    return redirect('/login/')


def index(request):
    return render(request, 'index.html')
class ATSAnalyzerTool(BaseTool):
    name: str = "ATS Analyzer"
    description: str = "Analyzes job descriptions and extracts key requirements for ATS optimization"

    def _run(self, job_description: str) -> Dict[str, List[str]]:
        """Extract keywords and requirements from job description"""
        # Simple keyword extraction - you can enhance this with NLP libraries
        keywords = []
        skills = []
        requirements = []
        
        # Extract common sections
        lines = job_description.lower().split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if any(word in line for word in ['requirements', 'qualifications', 'must have']):
                current_section = 'requirements'
            elif any(word in line for word in ['skills', 'technologies', 'experience with']):
                current_section = 'skills'
            elif line and current_section:
                if current_section == 'requirements':
                    requirements.append(line)
                elif current_section == 'skills':
                    skills.append(line)
        
        # Extract technical terms and tools
        tech_patterns = [
            r'\b(Python|Java|JavaScript|React|Django|Flask|AWS|Azure|Docker|Kubernetes|SQL|NoSQL|Git|Agile|Scrum)\b',
            r'\b(\d+\+?\s*years?)\b',
            r'\b(Bachelor|Master|PhD|degree)\b'
        ]
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, job_description, re.IGNORECASE)
            keywords.extend(matches)
        
        return {
            'keywords': list(set(keywords)),
            'skills': skills,
            'requirements': requirements
        }

class ResumeOptimizerAgent:
    def __init__(self):
        self.llm = OpenAI(
            temperature=0.7,
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # Initialize CrewAI agents
        self.ats_analyzer = Agent(
            role='ATS Optimization Specialist',
            goal='Analyze job descriptions and optimize resumes for ATS systems',
            backstory="""You are an expert in Applicant Tracking Systems (ATS) and resume optimization. 
            You understand how ATS systems parse and rank resumes, and you know the best practices for 
            keyword optimization, formatting, and content structure to achieve high ATS scores.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm,
            tools=[ATSAnalyzerTool()]
        )
        
        self.content_writer = Agent(
            role='Professional Resume Writer',
            goal='Create compelling and professional resume content',
            backstory="""You are a professional resume writer with 10+ years of experience. You excel at 
            crafting compelling professional summaries, quantifying achievements, and presenting experience 
            in the most impactful way. You know how to highlight transferable skills and make candidates 
            stand out while maintaining professional standards.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        self.quality_reviewer = Agent(
            role='Resume Quality Assurance Specialist',
            goal='Review and improve resume quality and ATS compatibility',
            backstory="""You are a meticulous quality assurance specialist who reviews resumes for 
            grammar, consistency, ATS compatibility, and overall impact. You ensure that resumes 
            meet industry standards and will perform well in both ATS systems and human review.""",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )

    def create_optimized_resume(self, user_data: Dict[str, Any]) -> str:
        """Create an ATS-optimized resume using CrewAI"""
        
        # Task 1: Analyze job description for ATS optimization
        analyze_task = Task(
            description=f"""
            Analyze the following job description and extract:
            1. Key technical skills and technologies
            2. Required qualifications and experience levels
            3. Important keywords that should appear in the resume
            4. Soft skills mentioned in the job posting
            5. Company culture indicators
            
            Job Description:
            {user_data.get('job_description', '')}
            
            Target Position: {user_data.get('target_position', '')}
            Target Industry: {user_data.get('target_industry', '')}
            """,
            agent=self.ats_analyzer,
            expected_output="A detailed analysis of job requirements and ATS optimization keywords"
        )
        
        # Task 2: Create optimized resume content
        write_task = Task(
            description=f"""
            Create an ATS-optimized resume using the analysis from the previous task and the following candidate information:
            
            Personal Information:
            - Name: {user_data.get('full_name', '')}
            - Email: {user_data.get('email', '')}
            - Phone: {user_data.get('phone', '')}
            - Location: {user_data.get('location', '')}
            - LinkedIn: {user_data.get('linkedin', '')}
            - Portfolio: {user_data.get('portfolio', '')}
            
            Experience Level: {user_data.get('years_experience', '')} years
            Career Level: {user_data.get('career_level', '')}
            
            Work Experience: {user_data.get('experience_data', [])}
            Education: {user_data.get('education_data', [])}
            Technical Skills: {user_data.get('technical_skills', '')}
            Soft Skills: {user_data.get('soft_skills', '')}
            Projects: {user_data.get('projects_data', [])}
            Certifications: {user_data.get('certifications', '')}
            Languages: {user_data.get('languages', '')}
            Achievements: {user_data.get('achievements', '')}
            Additional Info: {user_data.get('additional_info', '')}
            Current Summary: {user_data.get('current_summary', '')}
            
            Requirements:
            1. Create a compelling professional summary that incorporates job-specific keywords
            2. Optimize work experience descriptions with action verbs and quantified achievements
            3. Ensure skills section matches job requirements
            4. Use ATS-friendly formatting
            5. Include relevant keywords naturally throughout the resume
            6. Structure the resume for maximum ATS compatibility
            """,
            agent=self.content_writer,
            expected_output="A complete, ATS-optimized resume in professional format",
            context=[analyze_task]
        )
        
        # Task 3: Quality review and final optimization
        review_task = Task(
            description="""
            Review the generated resume and ensure:
            1. ATS compatibility (proper formatting, keyword density, structure)
            2. Grammar and consistency
            3. Professional presentation
            4. Keyword optimization without over-stuffing
            5. Quantified achievements where possible
            6. Proper contact information formatting
            7. Industry-appropriate language and terminology
            
            Provide the final, polished resume ready for submission.
            """,
            agent=self.quality_reviewer,
            expected_output="A final, polished, ATS-optimized resume",
            context=[analyze_task, write_task]
        )
        
        # Create and run the crew
        crew = Crew(
            agents=[self.ats_analyzer, self.content_writer, self.quality_reviewer],
            tasks=[analyze_task, write_task, review_task],
            verbose=2
        )
        
        result = crew.kickoff()
        return result

def resume_builder(request):
    """Main resume builder view"""
    if request.method == 'POST':
        try:
            # Extract form data
            user_data = {
                'full_name': request.POST.get('full_name'),
                'email': request.POST.get('email'),
                'phone': request.POST.get('phone'),
                'location': request.POST.get('location'),
                'linkedin': request.POST.get('linkedin'),
                'portfolio': request.POST.get('portfolio'),
                'target_position': request.POST.get('target_position'),
                'target_industry': request.POST.get('target_industry'),
                'job_description': request.POST.get('job_description'),
                'current_summary': request.POST.get('current_summary'),
                'years_experience': request.POST.get('years_experience'),
                'career_level': request.POST.get('career_level'),
                'technical_skills': request.POST.get('technical_skills'),
                'soft_skills': request.POST.get('soft_skills'),
                'certifications': request.POST.get('certifications'),
                'languages': request.POST.get('languages'),
                'achievements': request.POST.get('achievements'),
                'additional_info': request.POST.get('additional_info'),
            }
            
            # Process experience data
            experience_data = []
            experience_titles = request.POST.getlist('experience_title[]')
            experience_companies = request.POST.getlist('experience_company[]')
            experience_starts = request.POST.getlist('experience_start[]')
            experience_ends = request.POST.getlist('experience_end[]')
            experience_descriptions = request.POST.getlist('experience_description[]')
            
            for i in range(len(experience_titles)):
                if experience_titles[i]:  # Only add if title is provided
                    experience_data.append({
                        'title': experience_titles[i],
                        'company': experience_companies[i] if i < len(experience_companies) else '',
                        'start_date': experience_starts[i] if i < len(experience_starts) else '',
                        'end_date': experience_ends[i] if i < len(experience_ends) else 'Present',
                        'description': experience_descriptions[i] if i < len(experience_descriptions) else ''
                    })
            
            # Process education data
            education_data = []
            education_degrees = request.POST.getlist('education_degree[]')
            education_schools = request.POST.getlist('education_school[]')
            education_years = request.POST.getlist('education_year[]')
            education_gpas = request.POST.getlist('education_gpa[]')
            
            for i in range(len(education_degrees)):
                if education_degrees[i]:  # Only add if degree is provided
                    education_data.append({
                        'degree': education_degrees[i],
                        'school': education_schools[i] if i < len(education_schools) else '',
                        'year': education_years[i] if i < len(education_years) else '',
                        'gpa': education_gpas[i] if i < len(education_gpas) else ''
                    })
            
            # Process projects data
            projects_data = []
            project_names = request.POST.getlist('project_name[]')
            project_techs = request.POST.getlist('project_tech[]')
            project_descriptions = request.POST.getlist('project_description[]')
            project_urls = request.POST.getlist('project_url[]')
            
            for i in range(len(project_names)):
                if project_names[i]:  # Only add if name is provided
                    projects_data.append({
                        'name': project_names[i],
                        'technologies': project_techs[i] if i < len(project_techs) else '',
                        'description': project_descriptions[i] if i < len(project_descriptions) else '',
                        'url': project_urls[i] if i < len(project_urls) else ''
                    })
            
            user_data.update({
                'experience_data': experience_data,
                'education_data': education_data,
                'projects_data': projects_data
            })
            
            # Initialize resume optimizer and generate resume
            optimizer = ResumeOptimizerAgent()
            optimized_resume = optimizer.create_optimized_resume(user_data)
            
            # Store the result in session or return it
            request.session['generated_resume'] = optimized_resume
            request.session['user_data'] = user_data
            
            # Redirect to results page
            return redirect('res_result')
            
        except Exception as e:
            messages.error(request, f'Error generating resume: {str(e)}')
            return render(request, 'ai_resume.html')
    
    return render(request, 'ai_resume.html')

def resume_result(request):
    """Display the generated resume"""
    generated_resume = request.session.get('generated_resume')
    user_data = request.session.get('user_data')
    
    if not generated_resume:
        messages.warning(request, 'No resume found. Please generate a resume first.')
        return redirect('resume_builder')
    
    context = {
        'resume_content': generated_resume,
        'user_data': user_data
    }
    
    return render(request, 'res_result.html', context)

def download_resume(request):
    """Download the generated resume as a text file"""
    generated_resume = request.session.get('generated_resume')
    user_data = request.session.get('user_data')
    
    if not generated_resume:
        messages.warning(request, 'No resume found. Please generate a resume first.')
        return redirect('ai_resume')
    
    response = HttpResponse(generated_resume, content_type='text/plain')
    filename = f"{user_data.get('full_name', 'resume').replace(' ', '_')}_ATS_optimized.txt"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    return response

@csrf_exempt
def analyze_job_description(request):
    """AJAX endpoint to analyze job description and provide real-time feedback"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            job_description = data.get('job_description', '')
            
            if not job_description:
                return JsonResponse({'error': 'Job description is required'})
            
            # Simple analysis for immediate feedback
            analyzer = ATSAnalyzerTool()
            analysis = analyzer._run(job_description)
            
            # Calculate approximate ATS score based on various factors
            score = min(100, len(analysis['keywords']) * 5 + len(analysis['skills']) * 3)
            
            return JsonResponse({
                'success': True,
                'analysis': analysis,
                'estimated_keywords': len(analysis['keywords']),
                'estimated_score': score,
                'suggestions': [
                    'Include these key skills in your resume',
                    'Use exact job title from the posting',
                    'Quantify your achievements with numbers',
                    'Match the company\'s language and terminology'
                ]
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)})
    
    return JsonResponse({'error': 'Invalid request method'})