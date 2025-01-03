import os, fitz
from contants import MODEL
from typing import Optional
from dotenv import load_dotenv
from anthropic import Anthropic
from fastapi.responses import JSONResponse
from .helpers.re_helper import get_formatted_text
from fastapi import APIRouter, File, UploadFile, Form

load_dotenv()

router = APIRouter()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_MESSAGE = """
You are an AI assistant tasked with generating a cover letter based on provided resume content and a job description. Your goal is to create a compelling and personalized cover letter that highlights the candidate's qualifications and matches them with the job requirements.

You will be provided with the resume_content and job_description.

First, analyze both inputs to determine their validity. An input is considered valid if it contains relevant and substantial information. An empty or irrelevant input should be treated as invalid.

Based on the validity of the inputs, follow these instructions:

1. If both the resume content and job description are valid:
   - Carefully read the job description first.
   - Then, review the resume content.
   - Generate an accurate cover letter that aligns the candidate's qualifications with the job requirements.

2. If only the resume content is valid:
   - Ignore the job description.
   - Create a cover letter based solely on the provided resume content, highlighting the candidate's key skills and experiences.

3. If only the job description is valid:
   - Generate a cover letter by focusing on the key aspects of the job description.
   - Mention how a potential candidate could meet these requirements.

4. If both inputs are invalid:
   - Output a generic cover letter template.

Generate the cover letter using the following format:

[User's Full Name]
[User's Address]
[City, State, Zip]
[Your Email]
[Your Phone Number]
[Date]

[Recipient's Name]
[Company Name]
[Company Address]
[City, State, Zip]

Dear [Recipient's Name],

[Introduction: Open with an enthusiastic statement about the role and briefly mention the user's educational background and relevant experience that aligns with the job.]

[Body Paragraph 1: Highlight the user's key professional experience, internships, and major accomplishments, focusing on skills and achievements relevant to the job description.]

[Body Paragraph 2: Discuss any personal or freelance projects that showcase the user's technical skills, innovation, and ability to deliver impactful solutions.]

[Body Paragraph 3: Mention educational qualifications, certifications, or relevant challenges (e.g., coding challenges, competitions) that demonstrate the user's commitment and aptitude for the role.]

[Closing: Conclude with a statement of enthusiasm for the company, confidence in the user's fit for the role, and appreciation for the opportunity to apply.]

Best regards,
[User's Full Name]

When writing the cover letter, follow these guidelines:
- Begin with a professional greeting.
- Special characters like quotes within strings should be escaped with a backslash ("\"). 
- Include an opening paragraph that expresses interest in the position.
- In the body paragraphs, highlight relevant skills, experiences, and achievements.
- Conclude with a call to action and a professional closing.
- Maintain a formal tone throughout the letter.
- Keep the letter concise, typically not exceeding one page.

Provide your response by following the guidelines above. Begin your response with <cover_letter> and end it with </cover_letter>. 
"""

@router.post("/cover-letter-generator")
async def letter_generator( 
    # The endpoint should expect a file (UploadFile) and a form field (job_description) sent together in a multipart form-data request.
    # ensure job_description as a form field instead of a Pydantic request body.
    job_description: Optional[str] = Form(...),  # Accept job description as form input
    file: UploadFile = File(...)      # Accept file upload
):
    try:
        if file.content_type != "application/pdf":
            return JSONResponse(content={
                "data": "",
                "message": "File isn't a PDF",
                "error": True
            }, status_code=400)
        
        if len(job_description) < 50 or len(job_description) > 10000:
            return JSONResponse(content={
                "data": "",
                "message": f"Job description should be in the range of 50 to 10000 letters: {len(job_description)}",
                "error": True
            }, status_code=400)
            
        pdf_bytes = await file.read()

        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")

        resume_text = ""
        for page_num in range(pdf_document.page_count):
            page = pdf_document.load_page(page_num) 
            resume_text += page.get_text("text") + "\n"
         
        response = client.messages.create(
            model=MODEL,
            max_tokens=1500,
            temperature=0.5,
            system=SYSTEM_MESSAGE,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "<examples>\n<example>\n<RESUME_CONTENT>\n \n</RESUME_CONTENT>\n<JOB_DESCRIPTION>\npokijuhgytrfc vbnmijoyuhgtrfdc vbnm\n</JOB_DESCRIPTION>\n<ideal_output>\nSince both inputs are invalid (empty resume content and nonsensical job description), I will generate a generic cover letter template.\n\n<cover_letter>\n[Your Full Name]\n[Your Address]\n[City, State, Zip]\n[Your Email]\n[Your Phone Number]\n[Today's Date]\n\n[Hiring Manager's Name]\n[Company Name]\n[Company Address]\n[City, State, Zip]\n\nDear Hiring Manager,\n\nI am writing to express my sincere interest in joining your organization. With my educational background and professional experience, I am confident in my ability to contribute meaningfully to your team.\n\nThroughout my career, I have developed strong skills in problem-solving, collaboration, and project management. I have consistently demonstrated my ability to take initiative and deliver results in fast-paced environments. My experience has taught me the importance of adaptability and continuous learning, qualities that I believe are essential in today's dynamic workplace.\n\nI am particularly drawn to [Company Name] because of its reputation for innovation and commitment to excellence. Your company's values align perfectly with my professional goals and work ethic. I am excited about the possibility of bringing my skills and enthusiasm to your team.\n\nMy strong communication skills, coupled with my technical expertise and dedication to quality, make me an ideal candidate for this position. I am confident that my abilities and enthusiasm would make me a valuable addition to your team.\n\nThank you for considering my application. I look forward to the opportunity to discuss how I can contribute to your organization's continued success.\n\nBest regards,\n[Your Full Name]\n\n</cover_letter>\n</ideal_output>\n</example>\n<example>\n<example_description>\nOutput format if both the resume content and job description are valid. Output solely based on the job description and resume content.\n</example_description>\n<RESUME_CONTENT>\nEmily Chen\n789 Tech Lane, Silicon Valley, CA 94000\nPhone: (123) 456-7890 | Email: emily.chen@email.com\n\nPROFESSIONAL SUMMARY\nInnovative Software Engineer with 3+ years of experience in developing scalable web applications. Proficient in Python, JavaScript, and React.js, with a strong background in cloud computing and agile methodologies.\n\nWORK EXPERIENCE\n\nSoftware Engineer | InnoTech Solutions, Silicon Valley, CA\nAugust 2020 - Present\n• Developed and maintained RESTful APIs using Django, increasing system efficiency by 25%\n• Implemented responsive front-end designs using React.js, improving user engagement by 30%\n• Collaborated with cross-functional teams to integrate machine learning models into existing applications\n\nJunior Developer | StartUp Innovations, San Francisco, CA\nJune 2018 - July 2020\n• Assisted in the development of a mobile app using React Native, garnering 100,000+ downloads\n• Optimized database queries, reducing load times by 40%\n• Participated in code reviews and contributed to the improvement of coding standards\n\nEDUCATION\n\nBachelor of Science in Computer Science\nStanford University, Stanford, CA\nGraduated: May 2018 | GPA: 3.7/4.0\n\nSKILLS\n• Programming Languages: Python, JavaScript, Java, SQL\n• Frameworks & Libraries: Django, React.js, Node.js, Express.js\n• Cloud Platforms: AWS, Google Cloud Platform\n• Tools: Git, Docker, Jenkins, Jira\n• Methodologies: Agile, Scrum, Test-Driven Development\n\nCERTIFICATIONS\n• AWS Certified Developer - Associate\n• Google Cloud Certified - Professional Cloud Developer\n\nPROJECTS\n• E-commerce Platform: Developed a full-stack e-commerce website using the MERN stack, featuring real-time inventory updates and secure payment integration\n• Open Source Contributor: Active contributor to Django, focusing on performance optimizations and documentation improvements\n\nLANGUAGES\n• English (Native)\n• Mandarin Chinese (Fluent)\n</RESUME_CONTENT>\n<JOB_DESCRIPTION>\nFull Stack Developer\n\nAbout Us:\nTechNova is a fast-growing startup revolutionizing the fintech industry through innovative software solutions. We're looking for a talented Full Stack Developer to join our dynamic team and help build the next generation of financial technology products.\n\nJob Description:\nWe are seeking a skilled Full Stack Developer to play a crucial role in designing, developing, and maintaining our core software products. The ideal candidate will have a strong background in both front-end and back-end technologies, with a passion for creating efficient, scalable, and user-friendly applications.\n\nResponsibilities:\n• Develop and maintain robust, scalable web applications using modern JavaScript frameworks (React.js, Node.js)\n• Design and implement RESTful APIs to support our front-end applications\n• Work closely with product managers and UX designers to implement new features and improve existing ones\n• Write clean, maintainable, and well-documented code\n• Participate in code reviews and contribute to improving our development processes\n• Troubleshoot, debug, and optimize application performance\n• Stay up-to-date with emerging trends and technologies in web development\n\nRequirements:\n• Bachelor's degree in Computer Science, Software Engineering, or related field\n• 3+ years of experience in full stack development\n• Strong proficiency in JavaScript, including modern ES6+ features\n• Experience with React.js, Node.js, and Express.js\n• Familiarity with database technologies (e.g., MongoDB, PostgreSQL)\n• Knowledge of version control systems (Git)\n• Experience with cloud platforms (AWS, Google Cloud, or Azure)\n• Strong problem-solving skills and attention to detail\n• Excellent communication and teamwork skills\n\nNice to Have:\n• Experience with TypeScript and GraphQL\n• Familiarity with containerization technologies (Docker, Kubernetes)\n• Knowledge of agile development methodologies\n• Experience with CI/CD pipelines\n\nWhat We Offer:\n• Competitive salary and equity package\n• Health, dental, and vision insurance\n• Flexible work arrangements with remote options\n• Professional development budget\n• Modern, collaborative workspace\n• Opportunity to work on cutting-edge fintech products\n\nIf you're passionate about building innovative software solutions and want to be part of a fast-paced, collaborative team, we'd love to hear from you. Please submit your resume and a brief cover letter explaining why you're the perfect fit for this role.\n\nTechNova is an equal opportunity employer. We celebrate diversity and are committed to creating an inclusive environment for all employees.\n</JOB_DESCRIPTION>\n<ideal_output>\n<cover_letter>\nEmily Chen\n789 Tech Lane\nSilicon Valley, CA 94000\nemily.chen@email.com\n(123) 456-7890\nMarch 16, 2024\n\nHiring Manager\nTechNova\nSilicon Valley, CA\n\nDear Hiring Manager,\n\nI am writing to express my strong interest in the Full Stack Developer position at TechNova. As a Software Engineer with over three years of experience developing scalable web applications and a Bachelor's degree in Computer Science from Stanford University, I am excited about the opportunity to contribute to TechNova's mission of revolutionizing the fintech industry through innovative software solutions.\n\nIn my current role at InnoTech Solutions, I have demonstrated expertise in both front-end and back-end development, perfectly aligning with TechNova's requirements. I have successfully developed and maintained RESTful APIs using Django, increasing system efficiency by 25%, and implemented responsive front-end designs using React.js that improved user engagement by 30%. My experience working with cross-functional teams to integrate complex systems directly relates to the collaborative environment at TechNova.\n\nMy technical toolkit includes all the technologies specified in the job requirements, including React.js, Node.js, and Express.js. As an AWS Certified Developer and Google Cloud Certified Professional, I bring extensive experience with cloud platforms and containerization technologies. My work at StartUp Innovations, where I helped develop a mobile app that garnered over 100,000 downloads, demonstrates my ability to deliver high-impact solutions in a fast-paced startup environment.\n\nMy background in full-stack development is further evidenced by my personal projects, including a comprehensive e-commerce platform built using the MERN stack. As an active contributor to Django, focusing on performance optimizations and documentation improvements, I have demonstrated my commitment to writing clean, maintainable code and participating in open-source communities. My experience with agile methodologies, CI/CD pipelines, and modern development tools like Docker and Git aligns perfectly with TechNova's technical requirements.\n\nI am particularly excited about the opportunity to work on cutting-edge fintech products at TechNova and believe my combination of technical skills, collaborative nature, and passion for innovation makes me an ideal candidate for this role. I look forward to discussing how my background and skills can contribute to TechNova's continued success.\n\nBest regards,\nEmily Chen\n\n</cover_letter>\n</ideal_output>\n</example>\n<example>\n<example_description>\nOutput format if only the resume content is valid. Output solely based on the resume content.\n</example_description>\n<RESUME_CONTENT>\nMichael Rodriguez\n123 Tech Street, San Jose, CA 95110\nPhone: (408) 555-1234 | Email: michael.rodriguez@email.com\n\nSUMMARY\nDedicated and innovative DevOps Engineer with 4+ years of experience in automating, optimizing, and managing cloud infrastructure and deployment pipelines. Proficient in AWS, Docker, Kubernetes, and CI/CD tools, with a strong background in scripting and monitoring solutions.\n\nWORK EXPERIENCE\n\nSenior DevOps Engineer | CloudTech Solutions, San Jose, CA\nMarch 2020 - Present\n• Designed and implemented a highly available and scalable Kubernetes cluster on AWS, reducing infrastructure costs by 30%\n• Automated deployment processes using Jenkins and GitLab CI, decreasing release times by 50%\n• Implemented infrastructure-as-code using Terraform, improving consistency and reducing configuration errors by 70%\n• Led the migration of legacy applications to microservices architecture, enhancing system reliability and scalability\n\nDevOps Engineer | DataSys Inc., Santa Clara, CA\nJanuary 2018 - February 2020\n• Developed and maintained CI/CD pipelines for multiple projects using Jenkins and Docker\n• Implemented monitoring and alerting solutions using Prometheus and Grafana, improving system uptime by 25%\n• Collaborated with development teams to optimize application performance and resolve production issues\n• Assisted in the implementation of disaster recovery and backup strategies\n\nEDUCATION\n\nBachelor of Science in Computer Engineering\nUniversity of California, San Diego\nGraduated: June 2017 | GPA: 3.6/4.0\n\nSKILLS\n• Cloud Platforms: AWS, Google Cloud Platform\n• Containerization: Docker, Kubernetes\n• CI/CD: Jenkins, GitLab CI, CircleCI\n• Infrastructure-as-Code: Terraform, CloudFormation\n• Scripting: Python, Bash, PowerShell\n• Monitoring: Prometheus, Grafana, ELK Stack\n• Version Control: Git, GitHub\n• Configuration Management: Ansible, Puppet\n\nCERTIFICATIONS\n• AWS Certified DevOps Engineer - Professional\n• Certified Kubernetes Administrator (CKA)\n• HashiCorp Certified: Terraform Associate\n\nPROJECTS\n• Serverless Application Deployment: Developed a serverless web application using AWS Lambda and API Gateway, demonstrating cost-effective scalability\n• Personal Home Lab: Built and maintain a home lab environment for testing and learning new technologies, including self-hosted services and network configurations\n\nLANGUAGES\n• English (Native)\n• Spanish (Fluent)\n</RESUME_CONTENT>\n<JOB_DESCRIPTION>\niuhbygvcfg njou897yt6r45erdfc vb\n</JOB_DESCRIPTION>\n<ideal_output>\nSince the job description is invalid (contains random characters) but the resume content is valid, I'll generate a cover letter based solely on the resume content.\n\n<cover_letter>\nMichael Rodriguez\n123 Tech Street\nSan Jose, CA 95110\nmichael.rodriguez@email.com\n(408) 555-1234\n[Current Date]\n\nHiring Manager\n[Company Name]\n[Company Address]\n[City, State, Zip]\n\nDear Hiring Manager,\n\nI am writing to express my strong interest in contributing my extensive DevOps engineering expertise to your organization. With over four years of experience in cloud infrastructure management, automation, and optimization, combined with my proven track record of implementing efficient CI/CD solutions, I am confident in my ability to make significant contributions to your team.\n\nIn my current role as Senior DevOps Engineer at CloudTech Solutions, I have successfully led various high-impact initiatives, including designing and implementing a highly available Kubernetes cluster on AWS that resulted in a 30% reduction in infrastructure costs. My experience in automating deployment processes using Jenkins and GitLab CI has consistently improved team efficiency, as evidenced by a 50% decrease in release times. Additionally, my implementation of infrastructure-as-code using Terraform has significantly enhanced system reliability and reduced configuration errors by 70%.\n\nMy technical expertise spans a comprehensive range of modern DevOps tools and practices, including AWS, Docker, Kubernetes, and various CI/CD platforms. I have demonstrated this expertise through successful projects such as developing a serverless web application using AWS Lambda and maintaining a personal home lab environment for testing and implementing new technologies. My professional certifications, including AWS Certified DevOps Engineer - Professional and Certified Kubernetes Administrator (CKA), reflect my commitment to maintaining cutting-edge knowledge in the field.\n\nDuring my tenure at DataSys Inc., I developed strong collaborative skills while working with cross-functional teams to optimize application performance and implement robust monitoring solutions. My background in computer engineering from the University of California, San Diego, provides me with a solid foundation in software development principles, while my bilingual capabilities in English and Spanish enable effective communication across diverse teams.\n\nI would welcome the opportunity to discuss how my skills and experience align with your organization's needs. Thank you for considering my application. I look forward to the possibility of joining your team and contributing to your company's success.\n\nBest regards,\nMichael Rodriguez\n</cover_letter>\n</ideal_output>\n</example>\n<example>\n<example_description>\nOutput format if only the job description is valid. Output solely based on the job description.\n</example_description>\n<RESUME_CONTENT>\n  kjnhb\n</RESUME_CONTENT>\n<JOB_DESCRIPTION>\nSenior Quality Assurance Engineer\n\nAbout Us:\nQualityTech is a rapidly growing software company specializing in developing innovative solutions for the healthcare industry. We are committed to delivering high-quality, reliable software that improves patient care and streamlines healthcare operations.\n\nJob Description:\nWe are seeking a Senior Quality Assurance Engineer to join our dynamic team and play a crucial role in ensuring the quality and reliability of our healthcare software products. The ideal candidate will have a strong background in software testing, automated testing frameworks, and quality assurance processes.\n\nResponsibilities:\n• Develop and implement comprehensive test strategies and test plans for complex software systems\n• Design, create, and maintain automated test scripts using industry-standard tools and frameworks\n• Lead and mentor a team of QA engineers, fostering a culture of quality and continuous improvement\n• Collaborate with cross-functional teams to identify and resolve software defects and quality issues\n• Perform thorough regression testing to ensure software updates do not introduce new bugs\n• Conduct performance and scalability testing to ensure our products meet performance requirements\n• Participate in code reviews and provide feedback to improve overall code quality\n• Stay up-to-date with the latest trends and best practices in software testing and quality assurance\n\nRequirements:\n• Bachelor's degree in Computer Science, Software Engineering, or related field\n• 5+ years of experience in software quality assurance, with at least 2 years in a senior or lead role\n• Strong knowledge of software testing methodologies, tools, and best practices\n• Proficiency in automated testing frameworks such as Selenium, Appium, or similar tools\n• Experience with performance testing tools like JMeter or LoadRunner\n• Familiarity with Agile development methodologies\n• Excellent problem-solving and analytical skills\n• Strong communication and teamwork abilities\n• Experience in the healthcare industry is a plus\n\nNice to Have:\n• Knowledge of HIPAA compliance and healthcare data security standards\n• Experience with cloud-based testing environments (AWS, Azure, or GCP)\n• Familiarity with containerization technologies (Docker, Kubernetes)\n• ISTQB certification or other relevant quality assurance certifications\n\nWhat We Offer:\n• Competitive salary and comprehensive benefits package\n• Opportunities for professional growth and advancement\n• Collaborative and innovative work environment\n• Flexible work arrangements with remote options\n• Chance to make a meaningful impact in the healthcare industry\n\nIf you are passionate about software quality and want to contribute to improving healthcare through technology, we'd love to hear from you. Please submit your resume and a cover letter detailing your relevant experience and why you're interested in joining our team.\n\nQualityTech is an equal opportunity employer. We value diversity and do not discriminate based on race, religion, color, national origin, gender, sexual orientation, age, marital status, veteran status, or disability status.\n</JOB_DESCRIPTION>\n<ideal_output>\n<cover_letter>\n[Full Name]\n[Street Address]\n[City, State, Zip]\n[Email]\n[Phone]\n\n[Current Date]\n\nHiring Manager\nQualityTech\n[Company Address]\n[City, State, Zip]\n\nDear Hiring Manager,\n\nI am writing to express my strong interest in the Senior Quality Assurance Engineer position at QualityTech. With a background in software quality assurance and a passion for healthcare technology, I am excited about the opportunity to contribute to your mission of improving patient care through innovative software solutions.\n\nThroughout my career in software quality assurance, I have developed extensive experience in designing and implementing comprehensive test strategies for complex software systems. My expertise includes working with automated testing frameworks such as Selenium and maintaining robust test automation suites. I have successfully led QA teams and collaborated with cross-functional departments to ensure the delivery of high-quality software products.\n\nMy technical skill set aligns perfectly with your requirements, including proficiency in performance testing tools like JMeter, experience with Agile methodologies, and a strong foundation in software testing best practices. I have consistently demonstrated my ability to mentor junior team members while maintaining high standards for quality assurance processes. Additionally, I stay current with emerging trends in software testing and automation to ensure the implementation of best practices in all projects.\n\nHaving worked extensively with healthcare software systems, I understand the critical importance of maintaining HIPAA compliance and ensuring the highest standards of data security. My experience with cloud-based testing environments and containerization technologies would be valuable assets in supporting QualityTech's innovative solutions. I am particularly drawn to your company's commitment to improving healthcare operations through technology and would welcome the opportunity to contribute to such meaningful work.\n\nI am excited about the possibility of joining QualityTech and would welcome the opportunity to discuss how my skills and experience align with your team's needs. Thank you for considering my application.\n\nBest regards,\n[Full Name]\n</cover_letter>\n</ideal_output>\n</example>\n</examples>\n\n"
                        },
                        {
                            "type": "text",
                            "text": f"<resume_content>\n{resume_text}\n</resume_content>\n\n<job_description>\n{job_description}\n</job_description>"
                        }
                    ]
                }
            ]
        )
        
        formatted_text = get_formatted_text(response.content[0].text, r'<cover_letter>(.*?)</cover_letter>') # extract content between XML tags
        
        return JSONResponse(content={
            "data":  formatted_text,
            "message": "Success",
            "error": False
        }, status_code=200)
        
    except Exception as e:
        return JSONResponse(content={
            "data": "",
            "message": str(e),
            "error": True
        }, status_code=500)