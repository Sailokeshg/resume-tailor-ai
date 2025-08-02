from openai import OpenAI 
from app.core.config import settings

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.OPENAI_API_KEY,
)


def tailor_resume(resume: str, job_description: str) -> str:
    prompt = (
        "You are a professional resume writer. Given the following resume and job description, "
        "tailor the resume to better fit the job.\n\n"
        f"Resume:\n{resume}\n\n"
        f"Job Description:\n{job_description}\n\n"
        "Tailored Resume:"
    )
    completion = client.chat.completions.create(
        extra_headers={
            # Optional: update to your deployed site if needed
            # "HTTP-Referer": "http://localhost:5173",
            # Optional: update to your site name if needed
            "X-Title": "Resume Tailor AI",
        },
        extra_body={},
        model="deepseek/deepseek-r1-0528:free",
        messages=[
            {"role": "system", "content": "You are a professional resume writer."},
            {"role": "user", "content": prompt}
        ]
    )
    tailored_resume = completion.choices[0].message.content.strip()
    return tailored_resume
