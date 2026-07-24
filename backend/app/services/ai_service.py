import json
from openai import OpenAI, AsyncOpenAI
from app.core.config import settings
from app.services.rag_service import rag_service
from typing import Dict, AsyncGenerator, Any
from app.services.latex_parser import parse_latex_resume
import uuid
import logging
import re

logger = logging.getLogger(__name__)

OPENROUTER_MODEL_MAPPING = {
    "DEEPSEEK_V4_PRO": "DeepSeek-V4-Pro",
    "GLM_5_2": "glm-5.2",
    "DEEPSEEK_V4_FLASH": "DeepSeek-V4-Flash",
}

HCNSEC_MODEL_MAPPING = {
    "DEEPSEEK_V4_PRO": "DeepSeek-V4-Pro",
    "GLM_5_2": "glm-5.2",
    "DEEPSEEK_V4_FLASH": "DeepSeek-V4-Flash",
    "AUTO": "auto",
}


def normalize_provider(provider: str | None) -> str:
    provider = (provider or "openrouter").strip().lower()
    if provider not in {"openrouter", "hcnsec"}:
        raise ValueError(f"Unsupported provider: {provider}")
    return provider


def get_ai_client(provider: str | None) -> OpenAI:
    provider = normalize_provider(provider)
    if provider == "hcnsec":
        return OpenAI(
            base_url=settings.hcnsec_base_url,
            api_key=settings.hcnsec_api_key,
        )
    return OpenAI(
        base_url=settings.openai_base_url,
        api_key=settings.openai_api_key,
    )


def get_async_ai_client(provider: str | None) -> AsyncOpenAI:
    provider = normalize_provider(provider)
    if provider == "hcnsec":
        return AsyncOpenAI(
            base_url=settings.hcnsec_base_url,
            api_key=settings.hcnsec_api_key,
        )
    return AsyncOpenAI(
        base_url=settings.openai_base_url,
        api_key=settings.openai_api_key,
    )


def create_chat_completion(provider: str | None, model: str, messages: list[dict], extra_headers: dict | None = None):
    client = get_ai_client(provider)
    kwargs = {
        "model": model,
        "messages": messages,
    }
    if normalize_provider(provider) == "openrouter":
        kwargs["extra_headers"] = extra_headers or {
            "X-Title": "Resume Tailor AI"}
    logger.info(f"Starting API call to {provider} with model {model} (sync)")
    response = client.chat.completions.create(**kwargs)
    logger.info(f"Finished API call to {provider} with model {model} (sync)")
    return response


async def create_chat_completion_stream(provider: str | None, model: str, messages: list[dict], extra_headers: dict | None = None) -> AsyncGenerator[str, None]:
    client = get_async_ai_client(provider)
    kwargs = {
        "model": model,
        "messages": messages,
    }
    if normalize_provider(provider) == "openrouter":
        kwargs["extra_headers"] = extra_headers or {
            "X-Title": "Resume Tailor AI"}
    
    logger.info(f"Starting API stream to {provider} with model {model}")
    stream = await client.chat.completions.create(**kwargs, stream=True)
    async for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content is not None:
            yield chunk.choices[0].delta.content
    logger.info(f"Finished API stream to {provider} with model {model}")


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


def _get_content(completion) -> str:
    if not completion.choices:
        raise ValueError("API returned no choices in response.")
    message = completion.choices[0].message
    content = message.content
    refusal = getattr(message, "refusal", None)
    if refusal:
        logger.warning(f"Model refused request: {refusal}")
    if content is None:
        if refusal:
            raise ValueError(f"Model refused request: {refusal}")
        raise ValueError("Model returned empty content (None).")
    return content.strip()


def resolve_provider_model(selected: str, mapping: Dict[str, str], default_model: str) -> str:
    """Resolve a frontend-provided model to a provider id.
    - If `selected` is already a full provider id (contains a slash), return it
    - Else, look up the friendly key in `mapping`, default to default_model
    """
    default_provider_model = mapping.get(default_model, default_model)
    if not selected:
        return default_provider_model
    if "/" in selected:
        return selected
    return mapping.get(selected, default_provider_model)


def _provider_mapping(provider: str | None) -> Dict[str, str]:
    provider = normalize_provider(provider)
    return HCNSEC_MODEL_MAPPING if provider == "hcnsec" else OPENROUTER_MODEL_MAPPING


def resolve_tailor_model(selected: str | None, provider: str | None) -> str:
    return resolve_provider_model(
        selected or "",
        _provider_mapping(provider),
        settings.default_tailor_model,
    )


def resolve_auxiliary_model(provider: str | None, model: str) -> str:
    # For hcnsec, always use 'auto' for auxiliary (non-tailor) calls
    if normalize_provider(provider) == "hcnsec":
        return "auto"
    return resolve_provider_model(
        model,
        _provider_mapping(provider),
        model,
    )


def tailor_resume(resume: str, job_description: str, model: str | None = None, provider: str | None = None, job_keywords: list | None = None) -> str:
    """
    Tailor resume using AI.
    Accepts optional pre-extracted job_keywords to skip an extra LLM call.
    """
    try:
        # Use pre-extracted keywords if provided, else fall back to LLM extraction
        if not job_keywords:
            job_keywords = extract_job_keywords_with_ai(
                job_description, provider)

        # Create enhanced prompt
        prompt = create_tailoring_prompt(
            resume, job_description, job_keywords)

        provider_model = resolve_tailor_model(model, provider)

        system_prompt = (
            "You are an expert resume writer and LaTeX formatting specialist.\n"
            "Your objective is to tailor the candidate's LaTeX resume to align with a target job description.\n\n"
            "CRITICAL FORMATTING RULES:\n"
            "1. Output ONLY valid, compile-ready LaTeX code representing the tailored resume. DO NOT include any conversational filler.\n"
            "2. YOU MUST OUTPUT THE ENTIRE LATEX DOCUMENT FROM START TO FINISH. Do NOT omit, truncate, or abbreviate the preamble, packages, or unchanged sections. Start exactly with \\documentclass and end exactly with \\end{document}.\n"
            "3. Do NOT use markdown code fences (e.g. ```latex) or pre/post commentary within the LaTeX section.\n"
            "4. Preserve all existing LaTeX packages, layouts, structure, and headers. Only modify contents inside the document.\n"
            "5. Be extremely careful with special character escaping. Ensure %, &, $, _, #, {, } are correctly escaped unless they form valid LaTeX commands.\n"
            "6. Immediately after the \\end{document} tag, write a detailed, structured plain-text/markdown summary of the improvements made. Format it nicely (e.g. list modified sections, added keywords, and explanation).\n\n"
            "STRICT LENGTH RULES (MANDATORY):\n"
            "6. The tailored resume MUST NOT exceed the page length of the original resume. The input resume is at most 2 pages; the output MUST also be at most 2 pages.\n"
            "7. Keep the Professional Summary / Objective section to a MAXIMUM of 2-3 concise lines. Never expand it into a paragraph.\n"
            "8. For each work experience role, output the SAME number of bullet points as the original resume (±1 at most). Do NOT add extra bullets.\n"
            "9. Do NOT add new sections, roles, projects, or certifications that were not in the original resume.\n"
            "10. Prefer concise, impactful rephrasing over verbose expansion. Replace weak words with strong keywords — do not add more text.\n\n"
            "HUMAN TONE RULES (CRITICAL — the resume must read like a real person wrote it):\n"
            "11. BAN these overused AI words entirely: 'leveraged', 'utilized', 'spearheaded', 'orchestrated', 'synergy', 'cutting-edge', 'state-of-the-art', 'best-in-class', 'holistic', 'robust', 'scalable solutions', 'streamlined', 'cross-functional', 'paradigm'. Use plain, natural alternatives instead (e.g., 'used' not 'utilized', 'led' not 'spearheaded', 'built' not 'architected a robust solution').\n"
            "12. VARY sentence structure. Not every bullet should start with a past-tense action verb. Mix patterns: some bullets start with context ('As the lead on X, built...'), some with results ('Reduced latency by 40% by rewriting...'), some with the action verb. Aim for no more than 3 consecutive bullets starting the same way.\n"
            "13. PRESERVE the candidate's original voice and writing style. If the original resume uses casual phrasing, keep it casual. If formal, stay formal. Do not impose a uniform corporate tone.\n"
            "14. USE SPECIFIC details over vague claims. 'Built a data pipeline processing 2M events/day' beats 'Developed a scalable data processing solution'. Concrete numbers and technologies sound human; buzzword soup sounds AI-generated.\n"
            "15. KEEP the summary/objective natural and conversational — it should sound like how the candidate would introduce themselves in an interview, not like a marketing blurb."
        )

        completion = create_chat_completion(
            provider,
            provider_model,
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )

        # Sanitize model output to remove any chain-of-thought blocks
        tailored_resume = sanitize_model_output(_get_content(completion))
        return tailored_resume

    except Exception as e:
        logger.error(f"Error tailoring resume: {str(e)}")
        raise


async def tailor_resume_stream(resume: str, job_description: str, model: str | None = None, provider: str | None = None, job_keywords: list | None = None) -> AsyncGenerator[str, None]:
    """
    Tailor resume using AI, streaming the response back.
    """
    try:
        if not job_keywords:
            job_keywords = extract_job_keywords_with_ai(
                job_description, provider)

        prompt = create_tailoring_prompt(
            resume, job_description, job_keywords)

        provider_model = resolve_tailor_model(model, provider)

        system_prompt = (
            "You are an expert resume writer and LaTeX formatting specialist.\n"
            "Your objective is to tailor the candidate's LaTeX resume to align with a target job description.\n\n"
            "CRITICAL FORMATTING RULES:\n"
            "1. Output ONLY valid, compile-ready LaTeX code representing the tailored resume. DO NOT include any conversational filler.\n"
            "2. YOU MUST OUTPUT THE ENTIRE LATEX DOCUMENT FROM START TO FINISH. Do NOT omit, truncate, or abbreviate the preamble, packages, or unchanged sections. Start exactly with \\documentclass and end exactly with \\end{document}.\n"
            "3. Do NOT use markdown code fences (e.g. ```latex) or pre/post commentary within the LaTeX section.\n"
            "4. Preserve all existing LaTeX packages, layouts, structure, and headers. Only modify contents inside the document.\n"
            "5. Be extremely careful with special character escaping. Ensure %, &, $, _, #, {, } are correctly escaped unless they form valid LaTeX commands.\n"
            "6. Immediately after the \\end{document} tag, write a detailed, structured plain-text/markdown summary of the improvements made. Format it nicely (e.g. list modified sections, added keywords, and explanation).\n\n"
            "STRICT LENGTH RULES (MANDATORY):\n"
            "6. The tailored resume MUST NOT exceed the page length of the original resume. The input resume is at most 2 pages; the output MUST also be at most 2 pages.\n"
            "7. Keep the Professional Summary / Objective section to a MAXIMUM of 2-3 concise lines. Never expand it into a paragraph.\n"
            "8. For each work experience role, output the SAME number of bullet points as the original resume (±1 at most). Do NOT add extra bullets.\n"
            "9. Do NOT add new sections, roles, projects, or certifications that were not in the original resume.\n"
            "10. Prefer concise, impactful rephrasing over verbose expansion. Replace weak words with strong keywords — do not add more text.\n\n"
            "HUMAN TONE RULES (CRITICAL — the resume must read like a real person wrote it):\n"
            "11. BAN these overused AI words entirely: 'leveraged', 'utilized', 'spearheaded', 'orchestrated', 'synergy', 'cutting-edge', 'state-of-the-art', 'best-in-class', 'holistic', 'robust', 'scalable solutions', 'streamlined', 'cross-functional', 'paradigm'. Use plain, natural alternatives instead (e.g., 'used' not 'utilized', 'led' not 'spearheaded', 'built' not 'architected a robust solution').\n"
            "12. VARY sentence structure. Not every bullet should start with a past-tense action verb. Mix patterns: some bullets start with context ('As the lead on X, built...'), some with results ('Reduced latency by 40% by rewriting...'), some with the action verb. Aim for no more than 3 consecutive bullets starting the same way.\n"
            "13. PRESERVE the candidate's original voice and writing style. If the original resume uses casual phrasing, keep it casual. If formal, stay formal. Do not impose a uniform corporate tone.\n"
            "14. USE SPECIFIC details over vague claims. 'Built a data pipeline processing 2M events/day' beats 'Developed a scalable data processing solution'. Concrete numbers and technologies sound human; buzzword soup sounds AI-generated.\n"
            "15. KEEP the summary/objective natural and conversational — it should sound like how the candidate would introduce themselves in an interview, not like a marketing blurb."
        )

        stream = create_chat_completion_stream(
            provider,
            provider_model,
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )

        buffer = ""
        in_think = False
        think_ended = False

        async for chunk in stream:
            if not chunk:
                continue
                
            buffer += chunk
            
            if not think_ended:
                if "<think>" in buffer and not in_think:
                    in_think = True
                    pre_think = buffer.split("<think>")[0]
                    if pre_think:
                        clean_pre = re.sub(r"```[a-zA-Z]*\n?", "", pre_think)
                        clean_pre = clean_pre.replace("```", "")
                        yield clean_pre
                
                if in_think:
                    if "</think>" in buffer:
                        in_think = False
                        think_ended = True
                        buffer = buffer.split("</think>")[-1].lstrip()
                    else:
                        continue
            
            if not in_think:
                buffer = re.sub(r"```[a-zA-Z]*\n?", "", buffer)
                buffer = buffer.replace("```", "")
                
                if len(buffer) > 15:
                    yield buffer[:-15]
                    buffer = buffer[-15:]
                    
        if buffer:
            buffer = re.sub(r"```[a-zA-Z]*\n?", "", buffer)
            buffer = buffer.replace("```", "")
            if buffer.strip():
                yield buffer

    except Exception as e:
        logger.error(f"Error streaming tailored resume: {str(e)}")
        raise



def create_tailoring_prompt(resume: str, job_description: str, job_keywords: list) -> str:
    """
    Create a comprehensive prompt for resume tailoring
    """
    prompt = f"""
You are a professional resume writer. Tailor the original LaTeX resume to match the target job description.

<job_description>
{job_description}
</job_description>

<target_keywords>
{', '.join(job_keywords)}
</target_keywords>

<original_resume>
{resume}
</original_resume>

INSTRUCTIONS & CONSTRAINTS:
1. PRESERVE LATEX SYNTAX: Keep the exact LaTeX document structure, including the documentclass, packages, layout, and document environment. Do not introduce compile errors.
2. OUTPUT FULL DOCUMENT: You must output the ENTIRE LaTeX code from start to finish. DO NOT truncate, omit, or use placeholders for unchanged sections. DO NOT include conversational filler like 'Here is your resume'.
3. ESCAPE SPECIAL CHARACTERS: Ensure special characters like '%', '&', '$', '_', '#', '{', '}' are escaped correctly (e.g. use \\& instead of & for ampersands, \\_ instead of _ for underscores, etc.) inside text content.
4. ZERO HALLUCINATION: Do NOT invent new jobs, roles, dates, companies, degree credentials, or certifications. Only optimize, rephrase, and align existing experiences to emphasize matching skills.
5. INTEGRATE KEYWORDS: Weave target keywords into bullet points naturally — they should read like the candidate genuinely used those technologies, not like keywords were stuffed in. Place keywords where they make contextual sense (e.g., mention 'Kubernetes' when describing deployment work, not in a UI bullet).

LENGTH & DENSITY RULES (CRITICAL — violating these is a failure):
6. The output resume MUST NOT exceed the page count of the original resume. If the original is 1 page, output 1 page. If 2 pages, output at most 2 pages.
7. SUMMARY / OBJECTIVE: Keep it to 2-3 short, punchy lines maximum. Never write a full paragraph. Distill the candidate's value proposition into one concise statement aligned to the target role.
7. BULLET POINT COUNT: For each job/project, keep the exact same number of bullet points as the original (±1). Do NOT add new bullets to pad content.
8. BULLET POINT LENGTH: Each bullet should be 1-2 lines max. If the original bullet was 1 line, the tailored version should also be ~1 line. Do not expand single-line bullets into multi-line ones.
9. NO NEW SECTIONS OR ENTRIES: Do not add new work experience entries, projects, education entries, or skill categories that were not in the original resume.
10. TECHNIQUE: Achieve keyword integration by replacing or rephrasing existing words — not by appending extra text. Swap weak verbs for strong action verbs, swap generic nouns for target keywords. The total character count of each section should be approximately the same as the original (±10%).

HUMAN TONE RULES (the resume MUST NOT sound AI-generated):
11. BANNED WORDS — never use these: 'leveraged', 'utilized', 'spearheaded', 'orchestrated', 'synergy', 'cutting-edge', 'state-of-the-art', 'best-in-class', 'holistic', 'robust', 'scalable solutions', 'streamlined', 'cross-functional', 'paradigm', 'innovative solutions'. Use plain equivalents: 'used' not 'utilized', 'led' not 'spearheaded', 'built' not 'architected'.
12. VARY BULLET STRUCTURE — not every bullet should be "[Action verb] [object] [result]". Mix it up:
   - Context-first: "As part of the migration team, rewrote the auth service in Go"
   - Result-first: "Cut deploy time from 20min to 3min by switching to Docker multi-stage builds"
   - Action-first: "Built a real-time analytics dashboard tracking 500K daily events"
   No more than 3 consecutive bullets should start the same way.
13. PRESERVE ORIGINAL VOICE — match the tone and style of the original resume. If informal, stay informal. If technical and detailed, stay technical. Do not flatten everything into generic corporate-speak.
14. PREFER SPECIFICS OVER BUZZWORDS — "Built a Python ETL pipeline processing 2M records/day" sounds human. "Developed a robust, scalable data processing solution" sounds AI. Always choose the concrete version.
15. NATURAL KEYWORD PLACEMENT — keywords should appear where they contextually belong. Don't cluster all keywords into a single bullet or the summary. Spread them across relevant bullets where the technology was actually used.

TAILORED RESUME:
"""
    return prompt


def extract_job_keywords_with_ai(job_description: str, provider: str | None = None) -> list:
    """
    Extract key terms and skills from job description using LLM
    """
    try:
        completion = create_chat_completion(
            provider,
            resolve_auxiliary_model(
                provider, settings.keyword_extraction_model),
            [
                {"role": "system", "content": "You are an expert recruiter. Extract a list of the top 15 most important technical skills, tools, frameworks, methodologies, and requirements from the job description. Output only a comma-separated list of these keywords. Do not include any introductory text or explanation."},
                {"role": "user", "content": job_description}
            ]
        )
        content = _get_content(completion)
        # Clean and split keywords
        keywords = [kw.strip().lower()
                    for kw in content.split(",") if kw.strip()]
        # Filter out generic/too short words if any, but preserve main keywords
        return [kw for kw in keywords if len(kw) > 1]
    except Exception as e:
        logger.error(f"Error extracting keywords with AI: {str(e)}")
        # Fallback to hardcoded list in RAG service
        return rag_service.extract_job_keywords(job_description)


def analyze_resume_job_match(resume: str, job_description: str, provider: str | None = None) -> dict:
    """
    Analyze how well resume matches job description using LLM
    """
    try:
        # Extract dynamic keywords with AI
        job_keywords = extract_job_keywords_with_ai(job_description, provider)

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
        completion = create_chat_completion(
            provider,
            resolve_auxiliary_model(provider, settings.match_analysis_model),
            [
                {"role": "system", "content": "You are a professional ATS scanner and career coach. You only output valid JSON matching the requested schema."},
                {"role": "user", "content": prompt}
            ]
        )
        content = _get_content(completion)

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


def extract_company_name_with_ai(job_description: str, provider: str | None = None) -> str:
    """
    Extract company name from job description using LLM
    """
    if not job_description or not job_description.strip():
        return ""
    try:
        completion = create_chat_completion(
            provider,
            resolve_auxiliary_model(
                provider, settings.keyword_extraction_model),
            [
                {"role": "system",
                    "content": "You are an assistant that extracts the employing company name from a job description. Output ONLY the company name (1-3 words). If the company name is not mentioned or cannot be found, output 'Unknown'. Do not include any punctuation or extra words."},
                {"role": "user", "content": job_description}
            ]
        )
        name = _get_content(completion)
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


def generate_outreach(resume: str, job_description: str, recipient: str, channel: str, provider: str | None = None) -> dict:
    """
    Generate outreach message to a recruiter or CEO based on job description and resume.
    """
    try:
        recip_label = "Recruiter" if recipient.lower() == "recruiter" else "CEO"
        chan_label = "Email" if channel.lower() == "email" else "LinkedIn InMail"

        provider_model = resolve_auxiliary_model(
            provider, settings.outreach_model)

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

        completion = create_chat_completion(
            provider,
            provider_model,
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        content = _get_content(completion)

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


# Heuristic keywords that signal the job description may mention visa/sponsorship.
_VISA_HINT_PATTERN = re.compile(
    r"\b(sponsor|h[\-\s]?1b|h[\-\s]?1|work\s+auth|work\s+permit|visa|green\s+card|"
    r"citizenship|authorized\s+to\s+work|unrestricted|ead|opt|cpt|immigration)\b",
    re.IGNORECASE,
)


def check_visa_sponsorship(job_description: str, provider: str | None = None) -> dict:
    """
    Check if job description explicitly denies visa sponsorship.
    Uses heuristic regex first - only calls LLM when visa-related terms are found.
    """
    if not job_description or not job_description.strip():
        return {"sponsorship_denied": False, "reason": ""}

    # Fast heuristic: if no visa-related keywords at all, skip the LLM call
    if not _VISA_HINT_PATTERN.search(job_description):
        logger.info("No visa-related terms found - skipping visa LLM check.")
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
        completion = create_chat_completion(
            provider,
            resolve_auxiliary_model(provider, settings.match_analysis_model),
            [
                {"role": "system", "content": "You are a professional recruiting compliance assistant. You only output valid JSON."},
                {"role": "user", "content": prompt}
            ]
        )
        content = _get_content(completion)
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


def analyze_job_and_resume(resume: str, job_description: str, provider: str | None = None) -> dict:
    """
    Single consolidated LLM call that extracts:
    - Target keywords (top 15)
    - Company name
    - Match percentage, matching/missing keywords, suggested improvements
    Replaces 3 separate LLM calls (keyword extraction, company name, match analysis).
    """
    try:
        prompt = f"""
You are an expert ATS scanner, recruiter, and career coach. Analyze the job description and candidate resume below.

Job Description:
{job_description}

Candidate Resume (LaTeX):
{resume}

Return ONLY a valid JSON object with these exact keys:
{{
  "company_name": "<company name, 1-3 words, or empty string if not found>",
  "keywords": ["<top 15 technical skills, tools, frameworks, methodologies from the job description>"],
  "match_percentage": <integer 0-100>,
  "matching_keywords": ["<keywords from the list that appear in the resume>"],
  "missing_keywords": ["<keywords from the list NOT in the resume>"],
  "suggested_improvements": ["<up to 4 specific actionable suggestions to better align resume with job description>"]
}}

Do not include markdown fences or any text outside the JSON object.
"""
        completion = create_chat_completion(
            provider,
            resolve_auxiliary_model(provider, settings.match_analysis_model),
            [
                {"role": "system", "content": "You are a professional ATS scanner and career coach. Output only valid JSON matching the requested schema."},
                {"role": "user", "content": prompt},
            ],
        )
        content = _get_content(completion)
        if content.startswith("```"):
            lines = content.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines).strip()

        data = json.loads(content)
        # Sanitize company name for filename safety
        company_name = str(data.get("company_name", "")).strip()
        company_name = company_name.replace('"', '').replace("'", "").strip()
        company_name = re.sub(r'[\\/*?"<>|]', "", company_name)

        return {
            "company_name": company_name,
            "keywords": [str(k).strip().lower() for k in data.get("keywords", []) if str(k).strip()],
            "match_percentage": int(data.get("match_percentage", 0)),
            "matching_keywords": list(data.get("matching_keywords", [])),
            "missing_keywords": list(data.get("missing_keywords", [])),
            "suggested_improvements": list(data.get("suggested_improvements", [])),
        }
    except Exception as e:
        logger.error(f"Error in consolidated job/resume analysis: {str(e)}")
        # Graceful fallback: use rule-based keyword extraction, empty company name
        fallback_kw = rag_service.extract_job_keywords(job_description)
        fallback_match = fallback_resume_job_match(resume, job_description)
        return {
            "company_name": "",
            "keywords": fallback_kw,
            "match_percentage": fallback_match.get("match_percentage", 0),
            "matching_keywords": fallback_match.get("matching_keywords", []),
            "missing_keywords": fallback_match.get("missing_keywords", []),
            "suggested_improvements": fallback_match.get("suggested_improvements", []),
        }
