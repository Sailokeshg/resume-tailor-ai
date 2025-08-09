import re
from typing import List
from app.schemas.resume import ResumeSection

def parse_latex_resume(latex_content: str) -> List[ResumeSection]:
    """
    Parse LaTeX resume content into structured sections
    """
    sections = []
    
    # Define section patterns
    section_patterns = {
        'personal_info': r'\\begin\{document\}.*?\\maketitle(.*?)(?=\\section|\\subsection|$)',
        'education': r'\\section\{Education\}.*?(?=\\section|\\subsection|$)',
        'experience': r'\\section\{Experience\}.*?(?=\\section|\\subsection|$)',
        'skills': r'\\section\{Skills\}.*?(?=\\section|\\subsection|$)',
        'projects': r'\\section\{Projects\}.*?(?=\\section|\\subsection|$)',
        'certifications': r'\\section\{Certifications\}.*?(?=\\section|\\subsection|$)',
        'awards': r'\\section\{Awards\}.*?(?=\\section|\\subsection|$)',
        'publications': r'\\section\{Publications\}.*?(?=\\section|\\subsection|$)',
        'languages': r'\\section\{Languages\}.*?(?=\\section|\\subsection|$)',
        'interests': r'\\section\{Interests\}.*?(?=\\section|\\subsection|$)',
    }
    
    # Extract sections
    for section_type, pattern in section_patterns.items():
        matches = re.findall(pattern, latex_content, re.DOTALL | re.IGNORECASE)
        if matches:
            content = matches[0].strip()
            if content:
                # Extract keywords from content
                keywords = extract_keywords(content)
                sections.append(ResumeSection(
                    section_type=section_type,
                    content=content,
                    keywords=keywords
                ))
    
    # If no structured sections found, try to extract any content
    if not sections:
        # Extract content between \begin{document} and \end{document}
        doc_match = re.search(r'\\begin\{document\}(.*?)\\end\{document\}', latex_content, re.DOTALL)
        if doc_match:
            content = doc_match.group(1).strip()
            keywords = extract_keywords(content)
            sections.append(ResumeSection(
                section_type='general',
                content=content,
                keywords=keywords
            ))
    
    return sections

#TODO: Need to improve the keywords list dynamically rather than hardcoding it
def extract_keywords(content: str) -> List[str]:
    """
    Extract potential keywords from LaTeX content
    """
    # Remove LaTeX commands
    clean_content = re.sub(r'\\[a-zA-Z]+(\{[^}]*\})?', '', content)
    clean_content = re.sub(r'\\[a-zA-Z]+', '', clean_content)
    
    # Extract words that might be skills/technologies
    words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', clean_content)
    
    # Filter for likely technical terms
    technical_terms = [
        'Python', 'JavaScript', 'React', 'Node.js', 'Java', 'C++', 'SQL',
        'AWS', 'Docker', 'Kubernetes', 'Git', 'MongoDB', 'PostgreSQL',
        'Machine Learning', 'AI', 'Data Science', 'Web Development',
        'Agile', 'Scrum', 'DevOps', 'CI/CD', 'REST API', 'GraphQL'
    ]
    
    keywords = [word for word in words if any(term.lower() in word.lower() for term in technical_terms)]
    
    return list(set(keywords))[:10]  # Limit to 10 keywords

def clean_latex_content(content: str) -> str:
    """
    Clean LaTeX content for processing
    """
    # Remove comments
    content = re.sub(r'%.*$', '', content, flags=re.MULTILINE)
    
    # Remove extra whitespace
    content = re.sub(r'\s+', ' ', content)
    
    return content.strip()
