# Backend - Resume Tailor AI

## Setup

1. Copy `.env.example` to `.env` and add your OpenAI API key.
2. Run `npm install` to install dependencies.
3. Start the server with `npm run dev` (for development) or `npm start` (for production).

## API

- POST `/api/tailor`
  - Body: `{ resume: string, jobDesc: string }`
  - Returns: `{ tailoredResume: string }`
