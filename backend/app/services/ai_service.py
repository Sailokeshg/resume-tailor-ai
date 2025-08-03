from openai import OpenAI 
from app.core.config import settings
from app.services.rag_service import rag_service
from app.services.latex_parser import parse_latex_resume
import uuid
import logging

logger = logging.getLogger(__name__)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.openai_api_key,
)

def tailor_resume(resume: str, job_description: str) -> str:
    """
    Tailor resume using RAG and AI
    """
    try:
        # Generate unique IDs
        resume_id = str(uuid.uuid4())
        job_id = str(uuid.uuid4())
        
        # Parse resume sections
        sections = parse_latex_resume(resume)
        
        # Store resume sections in vector DB
        section_dicts = [section.dict() for section in sections]
        rag_service.store_resume_sections(resume_id, section_dicts)
        
        # Store job description
        rag_service.store_job_description(job_id, job_description)
        
        # Find relevant sections
        relevant_sections = rag_service.find_relevant_sections(job_description, resume_id)
        
        # Extract job keywords
        job_keywords = rag_service.extract_job_keywords(job_description)
        
        # Create enhanced prompt with RAG context
        prompt = create_tailoring_prompt(resume, job_description, relevant_sections, job_keywords)
        
        # Generate tailored resume
        completion = client.chat.completions.create(
            extra_headers={
                "X-Title": "Resume Tailor AI",
            },
            model="deepseek/deepseek-r1-0528:free",
            messages=[
                {"role": "system", "content": "You are a professional resume writer specializing in LaTeX formatting. Always preserve LaTeX syntax and formatting."},
                {"role": "user", "content": prompt}
            ]
        )
        
        tailored_resume = completion.choices[0].message.content.strip()
        return tailored_resume
        
    except Exception as e:
        logger.error(f"Error tailoring resume: {str(e)}")
        raise

def create_tailoring_prompt(resume: str, job_description: str, relevant_sections: list, job_keywords: list) -> str:
    """
    Create a comprehensive prompt for resume tailoring
    """
    relevant_context = "\n".join([f"- {section['section_type']}: {section['content'][:200]}..." for section in relevant_sections[:3]])
    
    prompt = f"""
You are a professional resume writer. Tailor the following LaTeX resume to better match the job description.

JOB DESCRIPTION:
{job_description}

KEY JOB REQUIREMENTS:
{', '.join(job_keywords)}

RELEVANT RESUME SECTIONS (most important for this job):
{relevant_context}

ORIGINAL RESUME:
{resume}

INSTRUCTIONS:
1. Preserve all LaTeX formatting and syntax exactly
2. Enhance sections to better match the job requirements
3. Add relevant keywords naturally into the content
4. Keep the same structure and length
5. Focus on the most relevant sections identified above
6. Maintain professional tone and formatting

TAILORED RESUME:
"""
    return prompt

def analyze_resume_job_match(resume: str, job_description: str) -> dict:
    """
    Analyze how well resume matches job description
    """
    try:
        # Extract keywords from both
        resume_sections = parse_latex_resume(resume)
        job_keywords = rag_service.extract_job_keywords(job_description)
        
        # Count keyword matches
        resume_keywords = []
        for section in resume_sections:
            resume_keywords.extend(section.keywords)
        
        resume_keywords = [kw.lower() for kw in resume_keywords]
        job_keywords = [kw.lower() for kw in job_keywords]
        
        matches = set(resume_keywords) & set(job_keywords)
        match_percentage = len(matches) / len(job_keywords) * 100 if job_keywords else 0
        
        return {
            "match_percentage": match_percentage,
            "matching_keywords": list(matches),
            "missing_keywords": [kw for kw in job_keywords if kw not in resume_keywords],
            "suggested_improvements": generate_improvement_suggestions(matches, job_keywords)
        }
        
    except Exception as e:
        logger.error(f"Error analyzing resume-job match: {str(e)}")
        return {"error": "Failed to analyze match"}

def generate_improvement_suggestions(matches: set, job_keywords: list) -> list:
    """
    Generate specific improvement suggestions
    """
    suggestions = []
    missing = [kw for kw in job_keywords if kw not in matches]
    
    if missing:
        suggestions.append(f"Add these keywords to your resume: {', '.join(missing[:5])}")
    
    if len(matches) < len(job_keywords) * 0.5:
        suggestions.append("Consider adding more relevant experience or skills")
    
    if len(matches) > len(job_keywords) * 0.8:
        suggestions.append("Good keyword match! Focus on quantifying achievements")
    
    return suggestions
