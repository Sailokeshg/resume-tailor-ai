import json
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
    - Else, look up the friendly key in `mapping`, default to settings.default_tailor_model
    """
    default_key = settings.default_tailor_model
    if not selected:
        return mapping.get(default_key, default_key)
    if "/" in selected:
        return selected
    return mapping.get(selected, mapping.get(default_key, default_key))


def tailor_resume(resume: str, job_description: str, model: str | None = None) -> str:
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

        # Extract job keywords using AI
        job_keywords = extract_job_keywords_with_ai(job_description)

        # Create enhanced prompt with RAG context
        prompt = create_tailoring_prompt(
            resume, job_description, relevant_sections, job_keywords)

        # Generate tailored resume
        # Friendly keys → provider model ids (extend easily here)
        model_mapping = {
            "GEMMA_4_31B_IT": "google/gemma-4-31b-it:free",
            "DEEPSEEK_V3_0324": "deepseek/deepseek-chat-v3-0324:free",
            "QWEN3_235B_A22B": "qwen/qwen3-235b-a22b:free",
            "Z.AI_GLM_4_5_AIR": "z-ai/glm-4.5-air:free",
            "MOONSHOTAI_KIMI_VL_A3B_THINKING": "moonshotai/kimi-vl-a3b-thinking:free",
        }

        provider_model = resolve_provider_model(model or "", model_mapping)

        system_prompt = (
            "You are an expert resume writer and LaTeX formatting specialist.\n"
            "Your objective is to tailor the candidate's LaTeX resume to align with a target job description.\n\n"
            "CRITICAL FORMATTING RULES:\n"
            "1. Output ONLY valid, compile-ready LaTeX code representing the tailored resume.\n"
            "2. Do NOT use markdown code fences (e.g. ```latex) or pre/post commentary within the LaTeX section.\n"
            "3. Preserve all existing LaTeX packages, layouts, structure, and headers. Only modify contents inside the document.\n"
            "4. Be extremely careful with special character escaping. Ensure %, &, $, _, #, {, } are correctly escaped unless they form valid LaTeX commands.\n"
            "5. Immediately after the \\end{document} tag, write a detailed, structured plain-text/markdown summary of the improvements made. Format it nicely (e.g. list modified sections, added keywords, and explanation)."
        )

        completion = client.chat.completions.create(
            extra_headers={
                "X-Title": "Resume Tailor AI",
            },
            model=provider_model,
            messages=[
                {"role": "system", "content": system_prompt},
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
    focus_sections = ", ".join(set([sec['section_type'].replace('_', ' ').title(
    ) for sec in relevant_sections])) if relevant_sections else "All sections"

    prompt = f"""
You are a professional resume writer. Tailor the original LaTeX resume to match the target job description.

<job_description>
{job_description}
</job_description>

<target_keywords>
{', '.join(job_keywords)}
</target_keywords>

<focus_sections>
Focus your tailoring efforts on the following key sections: {focus_sections}. Ensure other sections remain intact unless adjustments are necessary.
</focus_sections>

<original_resume>
{resume}
</original_resume>

INSTRUCTIONS & CONSTRAINTS:
1. PRESERVE LATEX SYNTAX: Keep the exact LaTeX document structure, including the documentclass, packages, layout, and document environment. Do not introduce compile errors.
2. ESCAPE SPECIAL CHARACTERS: Ensure special characters like '%', '&', '$', '_', '#', '{{', '}}' are escaped correctly (e.g. use \\& instead of & for ampersands, \\_ instead of _ for underscores, etc.) inside text content.
3. ZERO HALLUCINATION: Do NOT invent new jobs, roles, dates, companies, degree credentials, or certifications. Only optimize, rephrase, and align existing experiences to emphasize matching skills.
4. INTEGRATE KEYWORDS: Seamlessly incorporate target keywords into relevant bullet points. Focus on describing achievements using action verbs (e.g., Designed, Led, Automated) and quantifying impact (e.g., increased performance by 15%) without fabricating facts.
5. LENGTH CONSTRAINT: Keep the tailored resume layout clean and page-length identical to the original resume.

TAILORED RESUME:
"""
    return prompt


def extract_job_keywords_with_ai(job_description: str) -> list:
    """
    Extract key terms and skills from job description using LLM
    """
    try:
        completion = client.chat.completions.create(
            extra_headers={
                "X-Title": "Resume Tailor AI",
            },
            model=settings.keyword_extraction_model,
            messages=[
                {"role": "system", "content": "You are an expert recruiter. Extract a list of the top 15 most important technical skills, tools, frameworks, methodologies, and requirements from the job description. Output only a comma-separated list of these keywords. Do not include any introductory text or explanation."},
                {"role": "user", "content": job_description}
            ]
        )
        content = completion.choices[0].message.content.strip()
        # Clean and split keywords
        keywords = [kw.strip().lower()
                    for kw in content.split(",") if kw.strip()]
        # Filter out generic/too short words if any, but preserve main keywords
        return [kw for kw in keywords if len(kw) > 1]
    except Exception as e:
        logger.error(f"Error extracting keywords with AI: {str(e)}")
        # Fallback to hardcoded list in RAG service
        return rag_service.extract_job_keywords(job_description)


def analyze_resume_job_match(resume: str, job_description: str) -> dict:
    """
    Analyze how well resume matches job description using LLM
    """
    try:
        # Extract dynamic keywords with AI
        job_keywords = extract_job_keywords_with_ai(job_description)

        prompt = f"""
Analyze the match between the following candidate LaTeX resume and the target job description.

Target Job Description:
{job_description}

Key Keywords requested:
{', '.join(job_keywords)}

Candidate Resume:
{resume}

Provide your analysis in JSON format with the following keys:
1. "match_percentage": an integer from 0 to 100 representing how well the candidate matches the job description based on experience, skills, and match relevance.
2. "matching_keywords": list of keywords from the key keywords list that are present in the resume.
3. "missing_keywords": list of keywords from the key keywords list that are missing from the resume.
4. "suggested_improvements": list of specific suggestions for how the candidate can improve their resume to better match the job description (e.g. rephrasing, highlighting specific experiences, etc.).

Return ONLY the raw JSON object. Do not include markdown code fences or any other text.
"""
        completion = client.chat.completions.create(
            extra_headers={
                "X-Title": "Resume Tailor AI",
            },
            model=settings.match_analysis_model,
            messages=[
                {"role": "system", "content": "You are a professional ATS scanner and career coach. You only output valid JSON matching the requested schema."},
                {"role": "user", "content": prompt}
            ]
        )
        content = completion.choices[0].message.content.strip()

        # Clean any potential code fences
        if content.startswith("```"):
            lines = content.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()

        analysis_data = json.loads(content)
        return {
            "match_percentage": int(analysis_data.get("match_percentage", 0)),
            "matching_keywords": list(analysis_data.get("matching_keywords", [])),
            "missing_keywords": list(analysis_data.get("missing_keywords", [])),
            "suggested_improvements": list(analysis_data.get("suggested_improvements", []))
        }

    except Exception as e:
        logger.error(f"Error analyzing resume-job match: {str(e)}")
        # Fallback to rule-based analysis
        return fallback_resume_job_match(resume, job_description)


def fallback_resume_job_match(resume: str, job_description: str) -> dict:
    """
    Fallback rule-based resume job match analysis
    """
    try:
        resume_sections = parse_latex_resume(resume)
        job_keywords = rag_service.extract_job_keywords(job_description)

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
        logger.error(f"Error in fallback matching: {str(e)}")
        return {"error": "Failed to analyze match"}


def generate_improvement_suggestions(matches: set, job_keywords: list) -> list:
    """
    Generate specific improvement suggestions for fallback case
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


def extract_company_name_with_ai(job_description: str) -> str:
    """
    Extract company name from job description using LLM
    """
    if not job_description or not job_description.strip():
        return ""
    try:
        completion = client.chat.completions.create(
            extra_headers={
                "X-Title": "Resume Tailor AI",
            },
            model=settings.keyword_extraction_model,
            messages=[
                {"role": "system", "content": "You are an assistant that extracts the employing company name from a job description. Output ONLY the company name (1-3 words). If the company name is not mentioned or cannot be found, output 'Unknown'. Do not include any punctuation or extra words."},
                {"role": "user", "content": job_description}
            ]
        )
        name = completion.choices[0].message.content.strip()
        if name.lower() == "unknown":
            return ""
        # Clean any quotes or extra characters
        name = name.replace('"', '').replace("'", "").strip()
        # Clean characters that are invalid in filenames
        name = re.sub(r'[\\/*?:"<>|]', "", name)
        return name
    except Exception as e:
        logger.error(f"Error extracting company name: {str(e)}")
        return ""


def generate_outreach(resume: str, job_description: str, recipient: str, channel: str) -> dict:
    """
    Generate outreach message to a recruiter or CEO based on job description and resume.
    """
    try:
        recip_label = "Recruiter" if recipient.lower() == "recruiter" else "CEO"
        chan_label = "Email" if channel.lower() == "email" else "LinkedIn InMail"

        model_mapping = {
            "GEMMA_4_31B_IT": "google/gemma-4-31b-it:free",
            "DEEPSEEK_V3_0324": "deepseek/deepseek-chat-v3-0324:free",
            "QWEN3_235B_A22B": "qwen/qwen3-235b-a22b:free",
            "Z.AI_GLM_4_5_AIR": "z-ai/glm-4.5-air:free",
            "MOONSHOTAI_KIMI_VL_A3B_THINKING": "moonshotai/kimi-vl-a3b-thinking:free",
        }

        provider_model = resolve_provider_model(settings.outreach_model, model_mapping)

        system_prompt = (
            "You are an expert career coach and professional copywriter.\n"
            "Your task is to draft a personalized, highly effective outreach message (Email or LinkedIn InMail) "
            "to a Recruiter or CEO, demonstrating the candidate's fit based on their resume and interest in the job description.\n\n"
            "CRITICAL GUIDELINES:\n"
            "1. TONE: Write in a natural, warm, human, and professional tone. Avoid stiff, robotic, or overly formal language. "
            "Do NOT use typical AI clichés (e.g., 'I hope this email finds you well', 'Dear [Name]', 'I am thrilled to apply', 'As a testament to', 'plethora of skills', 'delighted to connect', etc.).\n"
            "2. LENGTH: Keep it extremely brief, concise, and scannable. Busy recruiters and CEOs only scan messages. "
            "If channel is 'LinkedIn InMail', it must be under 150 words. If 'Email', it must be under 200 words.\n"
            "3. VALUE PITCH: Focus on 1 or 2 specific highlights from the tailored resume that directly match the core requirements of the job description. Do not list everything; focus on the highest impact alignment.\n"
            "4. CALL TO ACTION (CTA): Keep the CTA low-friction and direct (e.g., asking if they have 5 minutes for a quick chat next week, or if you can send over a calendar link).\n"
            "5. OUTPUT FORMAT: Return ONLY a valid JSON object with the following keys:\n"
            "   - 'subject': A catchy, simple, non-clickbait subject line (only if channel is Email; return empty string if LinkedIn InMail).\n"
            "   - 'body': The message body, using placeholders like '[Name]' for the recipient's name or '[Company Name]' for the company name where appropriate."
        )

        user_prompt = f"""
Target Recipient: {recip_label}
Target Channel: {chan_label}

Job Description:
{job_description}

Tailored Resume (LaTeX/Text):
{resume}

Please generate the outreach message in the requested JSON format. Output ONLY the raw JSON object. Do not include markdown code fences or any other text.
"""

        completion = client.chat.completions.create(
            extra_headers={
                "X-Title": "Resume Tailor AI",
            },
            model=provider_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        content = completion.choices[0].message.content.strip()

        # Clean any potential code fences
        if content.startswith("```"):
            lines = content.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()

        data = json.loads(content)
        return {
            "subject": data.get("subject", ""),
            "body": data.get("body", "")
        }
    except Exception as e:
        logger.error(f"Error generating outreach message: {str(e)}")
        # Simple fallback message
        return {
            "subject": "Quick question regarding the opening" if channel.lower() == "email" else "",
            "body": f"Hi [Name],\n\nI noticed the opening at [Company Name] and wanted to reach out. Based on my background, I believe I could be a great fit for your team. Let me know if you have a few minutes to connect.\n\nBest,\n[Your Name]"
        }


def check_visa_sponsorship(job_description: str) -> dict:
    """
    Analyze job description to determine if company explicitly denies visa sponsorship.
    """
    if not job_description or not job_description.strip():
        return {"sponsorship_denied": False, "reason": ""}
    try:
        prompt = f"""
Analyze the job description below and determine if the company explicitly states they will NOT provide visa sponsorship (e.g., require existing unrestricted work authorization, state 'no visa sponsorship', require US citizenship or Green Card, state 'will not sponsor H-1B', require no sponsorship to work, etc.).

Job Description:
{job_description}

Rules for determination:
1. sponsorship_denied should be true ONLY if there is an explicit statement denying visa sponsorship or requiring citizenship/unrestricted authorization.
2. If there is no mention of visa sponsorship, or if it says they sponsor, sponsorship_denied should be false.

Output ONLY a JSON object with:
- "sponsorship_denied": boolean (true/false)
- "reason": string (brief explanation or quote from the job description if denied, empty if not denied)

Do not include any markdown fences or other text.
"""
        completion = client.chat.completions.create(
            extra_headers={
                "X-Title": "Resume Tailor AI",
            },
            model=settings.match_analysis_model,
            messages=[
                {"role": "system", "content": "You are a professional recruiting compliance assistant. You only output valid JSON."},
                {"role": "user", "content": prompt}
            ]
        )
        content = completion.choices[0].message.content.strip()
        # clean code fences
        if content.startswith("```"):
            lines = content.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()

        data = json.loads(content)
        return {
            "sponsorship_denied": bool(data.get("sponsorship_denied", False)),
            "reason": str(data.get("reason", ""))
        }
    except Exception as e:
        logger.error(f"Error checking visa sponsorship: {str(e)}")
        return {"sponsorship_denied": False, "reason": ""}


