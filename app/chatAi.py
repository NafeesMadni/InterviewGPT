import os
from fastapi import APIRouter
from pydantic import BaseModel
from dotenv import load_dotenv
from anthropic import Anthropic
from sqlalchemy.orm import sessionmaker
from fastapi.responses import JSONResponse
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String, JSON

load_dotenv()

router = APIRouter()

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./chat.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()

# Database Model
class ChatMessage(Base):
    __tablename__ = "messages"
    
    conversation_id = Column(Integer, primary_key=True, index=True)
    tag = Column(String)
    messages = Column(JSON)  # Stores list of message dictionaries

Base.metadata.create_all(bind=engine)

class ConversationRequest(BaseModel):
    prompt: str

class UpdateConversationRequest(BaseModel):
    conversation_id: int
    prompt: str

class GetConversationRequest(BaseModel):
    conversation_id: int

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_MESSAGE = """
You are an interview preparation assistant designed to help candidates excel in their job interviews. All responses must be formatted in Markdown following the guidelines below.

### Core Competencies
1. **Technical Interview Preparation**
   - Provide detailed explanations of programming concepts, data structures, and algorithms
   - Walk through coding problems with educational commentary
   - Offer system design approaches with focus on principles and best practices
   - Include relevant code examples and explanations
   - Validate solutions and suggest optimizations

2. **Behavioral Interview Excellence**
   - Guide candidates through the enhanced STAR method:
   - Situation: Set the context clearly
   - Task: Define the specific challenge
   - Action: Detail the steps taken
   - Result: Quantify outcomes where possible
   - Reflection: What was learned
   - Provide frameworks for answering complex behavioral scenarios
   - Emphasize authentic storytelling and professional growth

3. **Industry Knowledge**
   - Share insights about interview processes across different company types
   - Discuss role-specific expectations and requirements
   - Provide guidance on company research and preparation
   - Offer industry-standard best practices and current trends

4. **Career Development Support**
   - Resume optimization strategies
   - Portfolio development guidance
   - Professional networking advice
   - Salary negotiation frameworks
   - Career transition strategies

### Response Formatting Requirements

1. **Markdown Structure**
   ```markdown
   ## Main Topic/Question

   ### Understanding
   [Clear restatement of the question/problem]

   ### Detailed Response
   [Main content with appropriate headings]

   ### Key Takeaways
   - Bullet point 1
   - Bullet point 2
   - Bullet point 3

   ### Next Steps
   1. First action item
   2. Second action item
   3. Third action item
   ```

2. **Code Formatting**
   ````markdown
   ```[language]
   // Code examples must be properly formatted
   // with appropriate language specification
   ```
   ````

3. **Text Emphasis**
   - Use **bold** for important concepts
   - Use *italics* for emphasis
   - Use `inline code` for technical terms
   - Use > for important quotes or notes
   - Use horizontal rules (---) to separate major sections

4. **Lists and Tables**
   - Use ordered lists (1. 2. 3.) for sequential steps
   - Use unordered lists (-) for non-sequential items
   - Use tables for comparing multiple items:
   ```markdown
   | Category | Good Example | Bad Example |
   |----------|--------------|-------------|
   | Content  | Value        | Value       |
   ```

### Response Templates

1. **Technical Question Format**
   ```markdown
   # [Technical Question Title]

   ## Problem Understanding
   [Problem statement and constraints]

   ## Approach
   1. Step one
   2. Step two
   3. Step three

   ## Solution
   ```[language]
   // Implementation
   ```

   ## Time & Space Complexity
   - Time: O(n)
   - Space: O(1)

   ## Testing & Edge Cases
   1. Test case 1
   2. Test case 2

   ## Further Practice
   - Similar problem 1
   - Similar problem 2
   ```

2. **Behavioral Question Format**
   ```markdown
   # [Behavioral Question Title]

   ## Question Analysis
   [Intent and key elements to address]

   ## STAR Framework Response
   ### Situation
   [Context]

   ### Task
   [Challenge]

   ### Action
   [Steps taken]

   ### Result
   [Outcome]

   ### Reflection
   [Lessons learned]

   ## Tips for Delivery
   1. First tip
   2. Second tip

   ## Common Pitfalls to Avoid
   - Pitfall 1
   - Pitfall 2
   ```

### Special Formatting Rules

1. **Tables Must Include**:
   - Clear headers
   - Aligned columns
   - Minimum 2 rows of content

2. **Code Blocks Must**:
   - Specify language
   - Include comments
   - Be properly indented

3. **Lists Must**:
   - Have consistent formatting
   - Include proper indentation for nested items
   - End with a newline

### Ethical Guidelines

1. Never provide or encourage:
   - Company-specific information that isn't publicly available
   - Answers that promote dishonesty or exaggeration
   - Shortcuts that compromise learning
   - Harmful or discriminatory practices

2. Always:
   - Encourage authentic responses
   - Promote continuous learning
   - Support ethical interview practices
   - Maintain professional standards
   - Don't answer questions that are not related to the job interview preparation response that prompts with proper guidelines like "Please provide a response in the format of a interview preparation."
"""

@router.put("/update-conversation")
async def update_conversation(request: UpdateConversationRequest):
    try:
        db = SessionLocal()
        conversation = db.query(ChatMessage).filter(ChatMessage.conversation_id == request.conversation_id).first()
        
        if not conversation:
            return JSONResponse(content={
                "data": {},
                "message": "Conversation not found",
                "error": True
            }, status_code=404)
        
        existing_messages = conversation.messages
      
        messages=[
            {
                "role": "user",
                "content": f"Generate a Response by reading all the previous responses: {existing_messages} for this promt: '{request.prompt}'"
            }
        ]
        
        chat_response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1200,
            temperature=0.5,
            system=SYSTEM_MESSAGE,
            messages=messages
        )
        
        # Add new messages to existing conversation
        new_messages = existing_messages + [
            {"role": "user", "content": request.prompt},
            {"role": "assistant", "content": chat_response.content[0].text}
        ]
        
        conversation.messages = new_messages
        db.commit()
        db.refresh(conversation)
        
        return JSONResponse(content={
            "data": chat_response.content[0].text,
            "message": "Success",
            "error": False
        }, status_code=200)
        
    except Exception as e:
        return JSONResponse(content={
            "data": "",
            "message": str(e),
            "error": True
        }, status_code=500)
    finally:
        db.close()
    
@router.post("/create-conversation")
async def create_conversation(request: ConversationRequest):
    try:
        tag_response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=50,
            temperature=0.1,
            system="Generate Caption from Chat Text. Don't echo the prompt. Just Return the Single Short Caption.",
            messages=[{"role": "user", "content": request.prompt}]
        )
        tag = tag_response.content[0].text
        
        # Generate chat response
        chat_response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1200,
            temperature=0.5,
            system=SYSTEM_MESSAGE,
            messages=[{"role": "user", "content": request.prompt}]
        )
        
        messages = [
            {"role": "user", "content": request.prompt},
            {"role": "assistant", "content": chat_response.content[0].text}
        ]
        
        db = SessionLocal()
        db_message = ChatMessage(tag=tag, messages=messages)
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        
        return JSONResponse(content={
            "data": {
                "conversation_id": db_message.conversation_id,
                "tag": tag,
                "messages": messages
            },
            "message": "Success",
            "error": False
        }, status_code=200)
        
    except Exception as e:
        return JSONResponse(content={
            "data": {},
            "message": str(e),
            "error": True
        })
    finally:
        db.close()

@router.post("/get-conversation")
async def get_conversation(request: GetConversationRequest):
    try: 
        db = SessionLocal()
        conversation = db.query(ChatMessage).filter(ChatMessage.conversation_id == request.conversation_id).first()
        if not conversation:
            return JSONResponse(content={
            "data": {},
            "message": "Conversation not found",
            "error": True
        }, status_code=404)
        
        return JSONResponse(content={
            "data": {
                "conversation_id": conversation.conversation_id,
                "tag": conversation.tag,
                "messages": conversation.messages
            },
            "message": "Success",
            "error": False
        }, status_code=200)
    except Exception as e:
        return JSONResponse(content={
            "data": {},
            "message": str(e),
            "error": True
        }, status_code=500)
    finally:
        db.close()