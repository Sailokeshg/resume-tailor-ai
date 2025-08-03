from sentence_transformers import SentenceTransformer
import chromadb
from typing import List, Dict
import logging
import os

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Create chroma_db directory if it doesn't exist
        os.makedirs("./chroma_db", exist_ok=True)
        
        # Use the new ChromaDB client configuration
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.client.get_or_create_collection("resume_job_matches")
        
        logger.info("RAG service initialized successfully")
    
    def embed_text(self, text: str) -> List[float]:
        """Embed text using sentence transformers"""
        try:
            embedding = self.model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error embedding text: {str(e)}")
            return []
    
    def store_resume_sections(self, resume_id: str, sections: List[Dict]) -> None:
        """Store resume sections with embeddings"""
        try:
            documents = []
            metadatas = []
            ids = []
            
            for i, section in enumerate(sections):
                documents.append(section['content'])
                metadatas.append({
                    'type': 'resume_section',
                    'section_type': section['section_type'],
                    'resume_id': resume_id
                })
                ids.append(f"{resume_id}_section_{i}")
            
            if documents:
                embeddings = [self.embed_text(doc) for doc in documents]
                self.collection.add(
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                logger.info(f"Stored {len(documents)} resume sections for {resume_id}")
        except Exception as e:
            logger.error(f"Error storing resume sections: {str(e)}")
    
    def store_job_description(self, job_id: str, job_description: str) -> None:
        """Store job description with embedding"""
        try:
            embedding = self.embed_text(job_description)
            self.collection.add(
                embeddings=[embedding],
                documents=[job_description],
                metadatas=[{
                    'type': 'job_description',
                    'job_id': job_id
                }],
                ids=[job_id]
            )
            logger.info(f"Stored job description for {job_id}")
        except Exception as e:
            logger.error(f"Error storing job description: {str(e)}")
    
    def find_relevant_sections(self, job_description: str, resume_id: str, top_k: int = 5) -> List[Dict]:
        """Find resume sections most relevant to job description"""
        try:
            # Embed job description
            job_embedding = self.embed_text(job_description)
            
            # Query for relevant resume sections
            results = self.collection.query(
                query_embeddings=[job_embedding],
                n_results=top_k,
                where={"resume_id": resume_id, "type": "resume_section"}
            )
            
            relevant_sections = []
            for i in range(len(results['documents'][0])):
                relevant_sections.append({
                    'content': results['documents'][0][i],
                    'section_type': results['metadatas'][0][i]['section_type'],
                    'similarity': results['distances'][0][i] if 'distances' in results else 0.0
                })
            
            logger.info(f"Found {len(relevant_sections)} relevant sections for {resume_id}")
            return relevant_sections
        except Exception as e:
            logger.error(f"Error finding relevant sections: {str(e)}")
            return []
    
    def extract_job_keywords(self, job_description: str) -> List[str]:
        """Extract key terms and skills from job description"""
        # Simple keyword extraction - can be enhanced with NLP
        keywords = []
        
        # Common technical skills
        tech_skills = [
            'python', 'javascript', 'java', 'c++', 'sql', 'react', 'node.js',
            'aws', 'docker', 'kubernetes', 'git', 'mongodb', 'postgresql',
            'machine learning', 'ai', 'data science', 'web development',
            'agile', 'scrum', 'devops', 'ci/cd', 'rest api', 'graphql'
        ]
        
        job_lower = job_description.lower()
        for skill in tech_skills:
            if skill in job_lower:
                keywords.append(skill)
        
        return keywords

# Global RAG service instance
rag_service = RAGService()
