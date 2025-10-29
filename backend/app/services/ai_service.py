from openai import OpenAI
from app.core.config import settings
from app.services.rag_service import rag_service
from typing import Dict
from app.services.latex_parser import parse_latex_resume
import uuid
import logging
import re

logger = logging.getLogger(__name__)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.openai_api_key,
)


def sanitize_model_output(text: str) -> str:
    """Remove chain-of-thought and code fences if present, return clean LaTeX."""
    try:
        # Remove <think>...</think>
        text = re.sub(r"<think>[\s\S]*?</think>",
                      "", text, flags=re.IGNORECASE)
        # Remove surrounding triple backtick fences (optionally with language)
        fence_open = re.match(r"^```[a-zA-Z]*\n", text)
        if fence_open:
            closing_index = text.rfind("```")
            if closing_index > len(fence_open.group(0)):
                text = text[len(fence_open.group(0)):closing_index]
        return text.strip()
    except Exception:
        return text


def resolve_provider_model(selected: str, mapping: Dict[str, str]) -> str:
    """Resolve a frontend-provided model to a provider id.
    - If `selected` is already a full provider id (contains a slash), return it
    - Else, look up the friendly key in `mapping`, default to DEEPSEEK_R1_0528
    """
    if not selected:
        return mapping["DEEPSEEK_R1_0528"]
    if "/" in selected:
        return selected
    return mapping.get(selected, mapping["DEEPSEEK_R1_0528"])


def tailor_resume(resume: str, job_description: str, model: str | None = "DEEPSEEK_R1_0528") -> str:
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
        relevant_sections = rag_service.find_relevant_sections(
            job_description, resume_id)

        # Extract job keywords
        job_keywords = rag_service.extract_job_keywords(job_description)

        # Create enhanced prompt with RAG context
        prompt = create_tailoring_prompt(
            resume, job_description, relevant_sections, job_keywords)

        # Generate tailored resume
        # Friendly keys → provider model ids (extend easily here)
        model_mapping = {
            "DEEPSEEK_R1_0528": "deepseek/deepseek-r1-0528:free",
            "DEEPSEEK_V3_0324": "deepseek/deepseek-chat-v3-0324:free",
            "QWEN3_235B_A22B": "qwen/qwen3-235b-a22b:free",
            "Z.AI_GLM_4_5_AIR": "z-ai/glm-4.5-air:free",
            "DeepSeek R1T2": "tngtech/deepseek-r1t2-chimera:free",
            "MICROSOFT_MAI_DS_R1": "microsoft/mai-ds-r1:free",
            "MOONSHOTAI_KIMI_VL_A3B_THINKING": "moonshotai/kimi-vl-a3b-thinking:free",
        }

        provider_model = resolve_provider_model(model or "", model_mapping)

        completion = client.chat.completions.create(
            extra_headers={
                "X-Title": "Resume Tailor AI",
            },
            model=provider_model,
            messages=[
                {"role": "system", "content": "You are a professional resume writer specializing in LaTeX formatting. Always preserve LaTeX syntax and formatting. Output only the final LaTeX content of the resume without any analysis, commentary, chain-of-thought, or <think>...</think> blocks. Do not use code fences. If you need to include any notes, put them after \\end{document}."},
                {"role": "user", "content": prompt}
            ]
        )

        # Sanitize model output to remove any chain-of-thought blocks
        tailored_resume = sanitize_model_output(
            completion.choices[0].message.content.strip())
        return tailored_resume

    except Exception as e:
        logger.error(f"Error tailoring resume: {str(e)}")
        raise


def create_tailoring_prompt(resume: str, job_description: str, relevant_sections: list, job_keywords: list) -> str:
    """
    Create a comprehensive prompt for resume tailoring
    """
    relevant_context = "\n".join(
        [f"- {section['section_type']}: {section['content'][:200]}..." for section in relevant_sections[:3]])

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
        match_percentage = len(matches) / \
            len(job_keywords) * 100 if job_keywords else 0

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
        suggestions.append(
            f"Add these keywords to your resume: {', '.join(missing[:5])}")

    if len(matches) < len(job_keywords) * 0.5:
        suggestions.append(
            "Consider adding more relevant experience or skills")

    if len(matches) > len(job_keywords) * 0.8:
        suggestions.append(
            "Good keyword match! Focus on quantifying achievements")

    return suggestions
