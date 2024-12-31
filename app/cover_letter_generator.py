import os, fitz
from dotenv import load_dotenv
from anthropic import Anthropic
from fastapi.responses import JSONResponse
from fastapi import APIRouter, File, UploadFile, Form

load_dotenv()

router = APIRouter()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_MESSAGE = """
You are an AI assistant specializing in writing professional and tailored cover letters for users. Generate a cover letter for any user based on the following format, ensuring the output is in plain text with line breaks for readability:

[User's Full Name]
[City, Country]
[Profile Links (if mentioned in the resume)] 

[Date]

Hiring Manager
[Company Name]

Dear Hiring Manager,

[Introduction: Open with an enthusiastic statement about the role and briefly mention the user's educational background and relevant experience that aligns with the job.]

[Body Paragraph 1: Highlight the user's key professional experience, internships, and major accomplishments, focusing on skills and achievements relevant to the job description.]

[Body Paragraph 2: Discuss any personal or freelance projects that showcase the user's technical skills, innovation, and ability to deliver impactful solutions.]

[Body Paragraph 3: Mention educational qualifications, certifications, or relevant challenges (e.g., coding challenges, competitions) that demonstrate the user's commitment and aptitude for the role.]

[Closing: Conclude with a statement of enthusiasm for the company, confidence in the user's fit for the role, and appreciation for the opportunity to apply.]

Sincerely,
[User's Full Name]

Ensure that the content is personalized to the job description provided and reflects the user's skills and experiences effectively while maintaining a professional tone. Always use clear line breaks to improve readability. Don't Echo the Prompt.
"""

@router.post("/cover-letter-generator")
async def letter_generator( 
    # The endpoint should expect a file (UploadFile) and a form field (job_description) sent together in a multipart form-data request.
    # ensure job_description as a form field instead of a Pydantic request body.
    job_description: str = Form(...),  # Accept job description as form input
    file: UploadFile = File(...)      # Accept file upload
):
    try:
        if file.content_type != "application/pdf":
            return JSONResponse(content={
                "data": "",
                "message": "File isn't a PDF",
                "error": True
            }, status_code=400)
        
        if len(job_description) < 50 or len(job_description) > 1000:
            return JSONResponse(content={
                "data": "",
                "message": "Job description should be in the range of 50 to 1000 letters",
                "error": True
            }, status_code=400)
            
        # Read the uploaded PDF file into memory
        pdf_bytes = await file.read()

        # Open the PDF using PyMuPDF
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

        # Extract text from each page
        resume_text = ""
        for page_num in range(pdf_document.page_count):
            page = pdf_document.load_page(page_num)  # Get the page
            resume_text += page.get_text("text")  # Extract text from the page
            
        messages=[
            {
                "role": "user",
                "content": f"Generate a professional cover letter based on the following job description and resume details: Job Description:{job_description}, Resume Context:{resume_text}"
            }
        ]
        
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1200,
            temperature=0.1,
            system=SYSTEM_MESSAGE,
            messages=messages
        )
        
        return JSONResponse(content={
            "data": response.content[0].text,
            "message": "Success",
            "error": False
        }, status_code=200)
        
    except Exception as e:
        return JSONResponse(content={
            "data": "",
            "message": str(e),
            "error": True
        }, status_code=500)