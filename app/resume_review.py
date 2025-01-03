import os, fitz, json
from dotenv import load_dotenv
from anthropic import Anthropic
from fastapi.responses import JSONResponse
from fastapi import APIRouter, File, UploadFile, Form

load_dotenv()

router = APIRouter()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_MESSAGE = """
You are an AI resume reviewer tasked with analyzing resumes and providing feedback. Your goal is to help job seekers improve their resumes by offering constructive criticism and suggestions. You will be provided with two potential inputs: a job description and resume content. Your task is to analyze these inputs and generate a response based on the available information.

Analyze the provided inputs carefully. Consider the following scenarios:

1. If both the job description and resume content are valid:
   - Compare the resume content to the job description
   - Evaluate how well the resume matches the job requirements
   - Provide feedback based on both the job description and resume content

2. If the job description is invalid or empty, but the resume content is valid:
   - Focus on analyzing the resume content independently
   - Provide general feedback on the resume's structure, content, and effectiveness

3. If the job description is valid, but the resume content is invalid:
   - Use the job description to provide guidelines on creating a resume tailored to that position
   - Offer general advice on resume writing best practices

4. If both the job description and resume content are invalid:
   - Provide general guidelines on how to create an effective resume
   - Offer advice on job search strategies and resume writing best practices

Based on your analysis, generate a response in JSON format with the following structure:

{
    "categories_and_improvements": [
        {
            "name": "Content Quality",
            "score": 0,
            "suggestions": []
        },
        {
            "name": "Achievements and Impact",
            "score": 0,
            "suggestions": []
        },
        {
            "name": "Grammar and Language",
            "score": 0,
            "suggestions": []
        },
        {
            "name": "Experience and Skills Relevance",
            "score": 0,
            "suggestions": []
        }
    ],
    "feedback": ""
}

For each category:
    1. Evaluate the resume content in relation to the category
    2. Assign a score between 0 and 100 based on your evaluation
    3. Provide two specific one-line improvement suggestions for each category

When assigning scores and providing suggestions:
    - If the resume content is valid, base your evaluation on the actual content
    - If the resume content is invalid or empty, set all category scores to 0 and provide generic but helpful improvement suggestions

In the "feedback" field:
    - If both inputs are valid, provide a summary of how well the resume matches the job description and overall improvement areas
    - If only the resume is valid, offer general feedback on the resume's effectiveness
    - If only the job description is valid, provide guidance on creating a resume tailored to the position
    - If both inputs are invalid, include a standard message about missing information and general resume-writing advice

Ensure that feedback key content in the JSON response is formatted in markdown with proper formatting and is error-free. Always use "\n" for proper line breaks.


If the job description is not provided, include a message in the feedback suggesting that including a job description would allow for more tailored and specific feedback.

Your final output should be a valid JSON object containing the categories_and_improvements array and the feedback string, with categories_and_improvements as simple strings and the feedback content properly formatted in markdown.
"""

@router.post("/resume-review")
async def resume_review(job_description: str = Form(...), file: UploadFile = File(...)):
    try:
        if file.content_type != "application/pdf":
            return JSONResponse(content={
                "data": "",
                "message": "File isn't a PDF",
                "error": True
            }, status_code=400)
        
        pdf_bytes = await file.read()

        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

        resume_text = ""
        
        for page_num in range(pdf_document.page_count):
            page = pdf_document.load_page(page_num)  
            resume_text += page.get_text("text")  
            
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1500,
            temperature=0.5,
            system=SYSTEM_MESSAGE,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "<examples>\n<example>\n<RESUME_CONTENT>\nJohn Doe\n123 Tech Lane, Silicon Valley, CA 94000\nPhone: (555) 123-4567 | Email: john.doe@email.com\n\nProfessional Summary:\nDedicated and innovative Full Stack Developer with 4 years of experience in designing and implementing web applications. Proficient in front-end and back-end technologies, with a strong focus on creating efficient, scalable, and user-friendly solutions.\n\nSkills:\n- Programming Languages: JavaScript (ES6+), Python, HTML5, CSS3\n- Front-end: React.js, Vue.js, Angular\n- Back-end: Node.js, Express.js, Django\n- Databases: MongoDB, MySQL, PostgreSQL\n- API Development: RESTful APIs, GraphQL\n- Version Control: Git, GitHub\n- Cloud Platforms: AWS, Google Cloud Platform\n- DevOps: Docker, Jenkins, Travis CI\n\nWork Experience:\n\nSenior Full Stack Developer\nTechSolutions Inc., San Francisco, CA\nJune 2019 - Present\n\n- Led the development of a high-traffic e-commerce platform using React.js and Node.js, resulting in a 30% increase in user engagement\n- Implemented RESTful APIs and integrated with various third-party services, improving system functionality and data flow\n- Optimized database queries and implemented caching strategies, reducing page load times by 40%\n- Mentored junior developers and conducted code reviews to ensure best practices and maintain code quality\n\nFull Stack Developer\nWebInnovate Corp., San Jose, CA\nJuly 2017 - May 2019\n\n- Developed and maintained multiple web applications using Angular and Express.js\n- Designed and implemented responsive user interfaces, ensuring cross-browser compatibility and mobile-first approach\n- Collaborated with UX/UI designers to create intuitive and visually appealing user experiences\n- Participated in Agile development processes, including daily stand-ups and sprint planning meetings\n\nEducation:\nBachelor of Science in Computer Science\nStanford University, Stanford, CA\nGraduated: May 2017\n\nProjects:\n- Personal Portfolio Website: Designed and developed a responsive portfolio website using React.js and CSS Grid\n- Task Management App: Created a full-stack task management application using Vue.js, Node.js, and MongoDB\n\nCertifications:\n- AWS Certified Developer - Associate\n- MongoDB Certified Developer\n\nLanguages:\n- English (Native)\n- Spanish (Conversational)\n</RESUME_CONTENT>\n<JOB_DESCRIPTION>\nSoftware Engineer - Full Stack Developer\n\nTechInnovate Solutions is seeking a talented and motivated Full Stack Developer to join our growing team. The ideal candidate will have a strong background in both front-end and back-end development, with a passion for creating innovative and user-friendly web applications.\n\nResponsibilities:\n- Develop and maintain web applications using modern JavaScript frameworks (React, Angular, or Vue.js) and Node.js\n- Design and implement RESTful APIs and integrate with various databases (SQL and NoSQL)\n- Collaborate with cross-functional teams to define, design, and ship new features\n- Ensure the performance, quality, and responsiveness of applications\n- Identify and correct bottlenecks and fix bugs\n- Help maintain code quality, organization, and automatization\n\nRequirements:\n- Bachelor's degree in Computer Science, Software Engineering, or related field\n- 3+ years of experience in full stack development\n- Strong proficiency in JavaScript, HTML5, and CSS3\n- Experience with modern JavaScript frameworks (React, Angular, or Vue.js)\n- Familiarity with server-side languages such as Node.js, Python, or Ruby\n- Knowledge of database technologies (MySQL, MongoDB, PostgreSQL)\n- Understanding of RESTful API design and implementation\n- Experience with version control systems (e.g., Git)\n- Strong problem-solving skills and attention to detail\n- Excellent communication and teamwork abilities\n\nNice to have:\n- Experience with cloud platforms (AWS, Azure, or Google Cloud)\n- Knowledge of DevOps practices and tools (CI/CD, Docker, Kubernetes)\n- Familiarity with Agile development methodologies\n\nWe offer competitive salary, excellent benefits, and opportunities for professional growth. If you're passionate about technology and want to work on cutting-edge projects, we'd love to hear from you!\n\nTo apply, please submit your resume and a brief cover letter detailing your relevant experience and why you're interested in joining our team.\n\nTechInnovate Solutions is an equal opportunity employer. We celebrate diversity and are committed to creating an inclusive environment for all employees.\n</JOB_DESCRIPTION>\n<ideal_output>\n{\n    \"categories_and_improvements\": [\n        {\n            \"name\": \"Content Quality\",\n            \"score\": 90,\n            \"suggestions\": [\n                \"Add specific metrics or quantifiable achievements for the WebInnovate Corp. position\",\n                \"Include more details about specific contributions to team projects and leadership initiatives\"\n            ]\n        },\n        {\n            \"name\": \"Achievements and Impact\",\n            \"score\": 85,\n            \"suggestions\": [\n                \"Expand on the impact of mentoring junior developers with specific outcomes\",\n                \"Add performance metrics or business impact for the implemented caching strategies\"\n            ]\n        },\n        {\n            \"name\": \"Grammar and Language\",\n            \"score\": 95,\n            \"suggestions\": [\n                \"Consider using more action verbs to begin bullet points in the WebInnovate Corp. experience\",\n                \"Add more technical terminology specific to the e-commerce platform development\"\n            ]\n        },\n        {\n            \"name\": \"Experience and Skills Relevance\",\n            \"score\": 95,\n            \"suggestions\": [\n                \"Highlight experience with CI/CD tools more prominently as mentioned in job requirements\",\n                \"Add examples of cross-functional team collaboration and project outcomes\"\n            ]\n        }\n    ],\n    \"feedback\": \"# Resume Analysis for TechInnovate Solutions Position\\n\\n## Overall Match: Excellent (91/100)\\n\\nYour resume demonstrates an exceptional match with the requirements for the Full Stack Developer position at TechInnovate Solutions. Here's a detailed breakdown:\\n\\n### Strengths:\\n- Your experience (4 years) exceeds the required 3+ years in full stack development\\n- Strong alignment with required technical skills, including JavaScript frameworks, Node.js, and database technologies\\n- Demonstrated experience with both front-end and back-end development\\n- Impressive quantifiable achievements, particularly in performance optimization and user engagement\\n\\n### Areas for Enhancement:\\n1. **DevOps Experience**\\n   - While you have Docker and CI tools experience, consider expanding on your practical experience with Kubernetes\\n   - More emphasis on your experience with Agile methodologies would be beneficial\\n\\n2. **Technical Leadership**\\n   - Your mentoring experience is valuable; consider adding more details about team size and specific outcomes\\n   - Include examples of architectural decisions and their business impact\\n\\n3. **Project Scope**\\n   - Add more context about the scale of the applications you've worked on\\n   - Include information about team sizes and your role in project planning\\n\\n### Additional Recommendations:\\n- Consider adding a brief section about your experience with code quality tools and automated testing\\n- Highlight any experience with performance monitoring and optimization tools\\n- Include examples of how you've contributed to maintaining code quality and organization\\n\\nYour resume is well-structured and effectively demonstrates your qualifications for this position. The quantifiable achievements and clear technical expertise make you a strong candidate for the role.\"\n}\n</ideal_output>\n</example>\n<example>\n<RESUME_CONTENT>\nSarah Johnson\n123 Tech Boulevard, San Francisco, CA 94105\nPhone: (415) 555-7890 | Email: sarah.johnson@email.com\n\nProfessional Summary:\nResults-driven Product Manager with 6 years of experience in developing and launching innovative technology products. Skilled in AI and machine learning applications, with a proven track record of delivering successful products that drive business growth and enhance user experience.\n\nSkills:\n- Product Management: Agile methodologies, roadmap development, feature prioritization\n- AI/ML: Natural Language Processing, Computer Vision, Predictive Analytics\n- Technical: Python (basic), SQL, API integrations\n- Business: Market analysis, competitive intelligence, ROI modeling\n- Tools: JIRA, Confluence, Tableau, Google Analytics\n\nWork Experience:\n\nSenior Product Manager\nAI Innovations Inc., San Francisco, CA\nJanuary 2019 - Present\n\n- Led the development and launch of an AI-powered customer service chatbot, resulting in a 30% reduction in support tickets and 95% customer satisfaction rate\n- Collaborated with data science team to implement machine learning algorithms for predictive maintenance, reducing equipment downtime by 25%\n- Developed and executed go-to-market strategies for AI products, achieving 150% of revenue targets in the first year\n- Conducted user research and A/B testing to optimize product features, increasing user engagement by 40%\n- Managed a cross-functional team of 15 members, including engineers, data scientists, and designers\n\nProduct Manager\nTechSolutions Corp., Palo Alto, CA\nJune 2015 - December 2018\n\n- Spearheaded the development of a computer vision-based quality control system for manufacturing clients, improving defect detection accuracy by 35%\n- Created comprehensive product roadmaps and prioritized features based on market demand and business impact\n- Collaborated with UX designers to improve product usability, resulting in a 50% increase in user retention\n- Implemented Agile methodologies, increasing team productivity by 25% and reducing time-to-market by 30%\n\nEducation:\nMaster of Business Administration\nStanford University, Stanford, CA\nGraduated: May 2015\n\nBachelor of Science in Computer Engineering\nUniversity of California, Berkeley, CA\nGraduated: May 2011\n\nCertifications:\n- Certified Scrum Product Owner (CSPO)\n- Google Cloud Certified - Professional Cloud Architect\n\nProjects:\n- AI Ethics Workshop: Organized and led a company-wide workshop on ethical considerations in AI product development\n- Hackathon Winner: Led a team that developed an AI-powered personal finance assistant, winning first place in a company hackathon\n\nLanguages:\n- English (Native)\n- Mandarin Chinese (Professional working proficiency)\n</RESUME_CONTENT>\n<JOB_DESCRIPTION>\n \n</JOB_DESCRIPTION>\n<ideal_output>\n{\n    \"categories_and_improvements\": [\n        {\n            \"name\": \"Content Quality\",\n            \"score\": 92,\n            \"suggestions\": [\n                \"Consider adding specific metrics for the AI Ethics Workshop impact and outcomes\",\n                \"Include more details about leadership methodologies used in managing the cross-functional team\"\n            ]\n        },\n        {\n            \"name\": \"Achievements and Impact\",\n            \"score\": 95,\n            \"suggestions\": [\n                \"Add quantifiable results from the computer vision project's long-term business impact\",\n                \"Include specific revenue figures or market share gains from the AI products launched\"\n            ]\n        },\n        {\n            \"name\": \"Grammar and Language\",\n            \"score\": 98,\n            \"suggestions\": [\n                \"Consider using more action verbs at the start of achievement statements\",\n                \"Vary sentence structure in the Professional Summary to make it more engaging\"\n            ]\n        },\n        {\n            \"name\": \"Experience and Skills Relevance\",\n            \"score\": 90,\n            \"suggestions\": [\n                \"Add more specific details about Python programming projects or applications\",\n                \"Include examples of specific AI/ML models or frameworks used in projects\"\n            ]\n        }\n    ],\n    \"feedback\": \"# Resume Analysis\\n\\nYour resume demonstrates strong professional experience in product management with a focus on AI and technology. Here's a detailed analysis of your resume:\\n\\n## Strengths\\n- Excellent quantification of achievements with specific metrics and percentages\\n- Strong technical background combined with business acumen\\n- Clear progression in career path with increasing responsibilities\\n- Relevant certifications and educational background\\n\\n## Areas for Enhancement\\n- While your technical skills are well-presented, consider providing more specific examples of hands-on technical work\\n- The Professional Summary could be more impactful by highlighting your most significant achievement\\n- Consider adding a section on thought leadership or publications if available\\n\\n## Additional Recommendations\\n1. Your resume is well-structured and achievement-oriented, making it highly effective for technology and product management roles\\n2. Consider tailoring the technical skills section based on specific job requirements\\n3. The inclusion of both AI ethics and practical implementation shows valuable perspective\\n\\n*Note: To provide more targeted feedback, consider sharing a specific job description. This would allow me to evaluate how well your resume aligns with particular role requirements and suggest more specific customizations.*\"\n}\n</ideal_output>\n</example>\n<example>\n<RESUME_CONTENT>\n  \n</RESUME_CONTENT>\n<JOB_DESCRIPTION>\nData Scientist - Machine Learning Specialist\n\nDataTech Solutions is seeking an experienced Data Scientist specializing in Machine Learning to join our innovative team. The ideal candidate will have a strong background in developing and implementing machine learning models to solve complex business problems.\n\nResponsibilities:\n- Design, develop, and deploy machine learning models for various business applications\n- Collaborate with cross-functional teams to identify and prioritize data science opportunities\n- Perform data preprocessing, feature engineering, and model selection\n- Evaluate model performance and iterate on improvements\n- Communicate findings and insights to both technical and non-technical stakeholders\n- Stay up-to-date with the latest advancements in machine learning and AI technologies\n\nRequirements:\n- Master's or Ph.D. in Computer Science, Statistics, or related field\n- 3+ years of experience in applied machine learning and data science\n- Strong programming skills in Python, with experience in libraries such as scikit-learn, TensorFlow, and PyTorch\n- Proficiency in SQL and experience working with large datasets\n- Familiarity with cloud computing platforms (AWS, GCP, or Azure)\n- Experience with version control systems (e.g., Git) and CI/CD pipelines\n- Excellent problem-solving skills and attention to detail\n- Strong communication skills and ability to explain complex concepts to non-technical audiences\n\nNice to have:\n- Experience with natural language processing (NLP) or computer vision\n- Knowledge of big data technologies (Hadoop, Spark)\n- Familiarity with MLOps practices and tools\n- Published research papers or contributions to open-source projects\n\nWe offer a competitive salary, comprehensive benefits package, and opportunities for professional growth. If you're passionate about pushing the boundaries of machine learning and want to make a significant impact, we'd love to hear from you!\n\nTo apply, please submit your resume, a cover letter highlighting your relevant experience, and any notable projects or publications.\n\nDataTech Solutions is an equal opportunity employer committed to diversity and inclusion in the workplace.\n</JOB_DESCRIPTION>\n<ideal_output>\n{\n    \"categories_and_improvements\": [\n        {\n            \"name\": \"Content Quality\",\n            \"score\": 0,\n            \"suggestions\": [\n                \"Create a strong summary section highlighting your expertise in machine learning and data science\",\n                \"Include specific technical skills section featuring Python libraries, cloud platforms, and ML frameworks\"\n            ]\n        },\n        {\n            \"name\": \"Achievements and Impact\",\n            \"score\": 0,\n            \"suggestions\": [\n                \"Quantify ML project outcomes using metrics like accuracy improvements or business impact\",\n                \"Highlight successful deployments of machine learning models in production environments\"\n            ]\n        },\n        {\n            \"name\": \"Grammar and Language\",\n            \"score\": 0,\n            \"suggestions\": [\n                \"Use action verbs specific to data science roles (e.g., developed, implemented, optimized)\",\n                \"Incorporate relevant technical terminology aligned with machine learning positions\"\n            ]\n        },\n        {\n            \"name\": \"Experience and Skills Relevance\",\n            \"score\": 0,\n            \"suggestions\": [\n                \"Focus on demonstrating experience with required technologies: Python, scikit-learn, TensorFlow, and SQL\",\n                \"Emphasize any MLOps, cloud computing, or big data technology experience\"\n            ]\n        }\n    ],\n    \"feedback\": \"# Resume Creation Guidelines for DataTech Solutions Data Scientist Position\\n\\n## Key Areas to Address\\n\\nBased on the job description, here are the essential elements your resume should include:\\n\\n### Technical Skills Section\\n- Highlight proficiency in Python, scikit-learn, TensorFlow, and PyTorch\\n- Emphasize experience with SQL and cloud platforms (AWS/GCP/Azure)\\n- List relevant big data technologies and MLOps tools\\n\\n### Education\\n- Prominently feature your Master's or Ph.D. in a relevant field\\n- Include any specialized machine learning or AI coursework\\n\\n### Professional Experience\\n- Focus on hands-on machine learning project experience\\n- Demonstrate cross-functional collaboration\\n- Quantify impacts of your ML solutions\\n- Show experience with model deployment and monitoring\\n\\n### Projects and Publications\\n- Include relevant research papers or publications\\n- Highlight contributions to open-source projects\\n- Showcase end-to-end ML projects\\n\\n## Additional Recommendations\\n\\n1. Tailor your resume specifically to emphasize machine learning expertise\\n2. Include examples of communication with non-technical stakeholders\\n3. Demonstrate continuous learning and staying current with ML trends\\n4. Highlight any experience with NLP or computer vision if applicable\\n\\nTo create a compelling application, ensure your resume clearly demonstrates alignment with both the technical requirements and soft skills mentioned in the job description. Consider including a portfolio link or GitHub profile to showcase your practical ML work.\\n\\nNote: Since no resume content was provided, these recommendations are based solely on the job description. Please submit your resume for a detailed, personalized review.\"\n}\n</ideal_output>\n</example>\n<example>\n<RESUME_CONTENT>\nlhkuyjdf\n</RESUME_CONTENT>\n<JOB_DESCRIPTION>\n blkkjhgfd\n</JOB_DESCRIPTION>\n<ideal_output>\n{\n    \"categories_and_improvements\": [\n        {\n            \"name\": \"Content Quality\",\n            \"score\": 0,\n            \"suggestions\": [\n                \"Structure your resume with clear sections including Summary, Experience, Education, and Skills\",\n                \"Include detailed work experiences with specific responsibilities and accomplishments\"\n            ]\n        },\n        {\n            \"name\": \"Achievements and Impact\",\n            \"score\": 0,\n            \"suggestions\": [\n                \"Quantify your achievements using specific metrics and numbers\",\n                \"Include specific examples of projects or initiatives you've led\"\n            ]\n        },\n        {\n            \"name\": \"Grammar and Language\",\n            \"score\": 0,\n            \"suggestions\": [\n                \"Use strong action verbs to begin each bullet point\",\n                \"Ensure consistent formatting and punctuation throughout the resume\"\n            ]\n        },\n        {\n            \"name\": \"Experience and Skills Relevance\",\n            \"score\": 0,\n            \"suggestions\": [\n                \"Highlight relevant technical and soft skills specific to your industry\",\n                \"Tailor your experience descriptions to match job requirements\"\n            ]\n        }\n    ],\n    \"feedback\": \"# Resume Review Feedback\\n\\n## Overall Assessment\\nI notice that both the job description and resume content provided appear to be invalid or incomplete. To provide you with meaningful and targeted feedback, I'll need more detailed information.\\n\\n## General Recommendations\\n\\n### 1. Content Structure\\n- Organize your resume into clear, distinct sections\\n- Include contact information, professional summary, work experience, education, and skills\\n\\n### 2. Professional Presentation\\n- Maintain consistent formatting throughout\\n- Use a clean, professional font\\n- Keep your resume to 1-2 pages\\n\\n### 3. Content Development\\n- Use bullet points to highlight achievements\\n- Include quantifiable results where possible\\n- Focus on relevant experience and skills\\n\\n## Next Steps\\nTo receive more specific and tailored feedback, please provide:\\n- A complete resume with your actual experience and qualifications\\n- A specific job description you're targeting\\n\\nThis will allow me to provide more targeted recommendations and help you better align your resume with your career goals.\\n\\n*Note: The current review is based on general best practices due to limited input content.*\"\n}\n</ideal_output>\n</example>\n</examples>\n\n"
                        },
                        {
                            "type": "text",
                            "text": f"<job_description>\n{job_description}\n</job_description>\n\n<resume_content>\n{resume_text}\n</resume_content>"
                        }
                    ]
                }
            ]
        )
        try: 
            data = json.loads(response.content[0].text)
            
            return JSONResponse(content={
                "data": data,
                "message": "Success",
                "error": False
            }, status_code=200)
            
        except json.JSONDecodeError:
            return JSONResponse(content={
                "data": {},
                "message": "Invalid response format",
                "error": True
            }, status_code=400)
            
    except Exception as e:
        return JSONResponse(content={
            "data": {},
            "message": str(e),
            "error": True
        }, status_code=500)