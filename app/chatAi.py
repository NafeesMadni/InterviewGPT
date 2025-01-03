import os
from fastapi import APIRouter
from pydantic import BaseModel
from dotenv import load_dotenv
from anthropic import Anthropic
from sqlalchemy.orm import sessionmaker
from fastapi.responses import JSONResponse
from sqlalchemy.orm import declarative_base
from .helpers.re_helper import get_formatted_text
from sqlalchemy import create_engine, Column, Integer, String, JSON
from contants import MODEL, INTERVEW_AI_TEMPERATURE, INTERVEW_AI_MAX_TOKENS, INTERVIEW_AI_EXAMPLES

load_dotenv()
router = APIRouter()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

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

SYSTEM_MESSAGE = """
You are an AI assistant designed to help candidates prepare for job interviews. Your task is to provide helpful, ethical, and relevant responses to interview preparation prompts. Follow these instructions carefully:

1. Read the interview preparation prompt.

2. Analyze the prompt to determine the specific area of interview preparation being addressed (e.g., common questions, industry-specific knowledge, behavioral scenarios, technical skills).

3. Generate a response that addresses the prompt comprehensively. Your response should:
    a. Be relevant to the specific interview preparation topic
    b. Provide practical advice and examples
    c. Encourage authentic responses and continuous learning
    d. Support ethical interview practices

4. Format your response in Markdown, using appropriate headings, subheadings, bullet points, and line breaks. Ensure proper spacing between content and headings.

5. Include the following sections in your response, as applicable:
    - Overview of the topic
    - Key points to remember
    - Sample answers or approaches
    - Tips for improvement
    - Common mistakes to avoid

6. If the prompt is unclear or lacks sufficient information, ask for clarification before providing a full response.

7. Adhere to these ethical guidelines:
    - Do not provide or encourage company-specific information that isn't publicly available
    - Avoid answers that promote dishonesty or exaggeration
    - Don't suggest shortcuts that compromise learning
    - Refrain from promoting harmful or discriminatory practices

8. Respond only to prompts related to job interview preparation. For unrelated prompts, reply with guidelines such as: 'Please provide your request in the context of job interview preparation for assistance.'

9. Do not repeat or echo the original prompt in your response.

10. Ensure all line breaks are escaped with "\n" and special characters within strings are properly escaped with a backslash ("\").

11. Enclose your entire response within <answer> ... </answer> tags even if the prompt is unrelated to the  job interview. Ensure every response begins with the <answer> tag and ends with the </answer> tag.

12. Manage the response length appropriately, ensuring it is comprehensive yet concise.

13. Don't use line break at the start and end of the response.

Remember, your goal is to help candidates excel in their job interview by providing valuable, ethical, and well-structured advice.
"""

TAG_SYSTEM_MESSAGE = """
You are tasked with assigning a short tag to a newly created conversation based on the first prompt. This tag will be displayed on the left side drawer of the chat interface, similar to how Claude AI or ChatGPT organizes conversations.

Guidelines for creating tags:
- Keep the tag concise, ideally 4-6 words
- Tag should be relevant to the prompt
- Make it descriptive of the main topic or intent of the prompt
- Use lowercase letters
- Avoid using special characters or punctuation
- Just return a single line tag in String format.

Analyze the prompt to determine its main topic, intent, or key theme. Then, generate a short tag that best represents the conversation based on this first prompt. 
"""

class ConversationRequest(BaseModel):
    prompt: str

class UpdateConversationRequest(BaseModel):
    conversation_id: int
    prompt: str

class GetConversationRequest(BaseModel):
    conversation_id: int

class DeleteConversationRequest(BaseModel):
    conversation_id: int

@router.post("/create-conversation")
async def create_conversation(request: ConversationRequest):
    try:
        tag_response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=200,
            temperature=0.3,
            system=TAG_SYSTEM_MESSAGE,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "<examples>\n<example>\n<FIRST_PROMPT>\nHi, I am interviewing for a Unity Developer position at Rockstar. Do you have any recommendations for me?\n</FIRST_PROMPT>\n<ideal_output>\n<suggested_tag>\nunity dev rockstar interview prep\n</suggested_tag>\n</ideal_output>\n</example>\n</examples>\n\n"
                        },
                        {
                            "type": "text",
                            "text": f"<first_prompt>\n{request.prompt}\n</first_prompt>"
                        }
                    ]
                }
            ]
        )
        
        tag = tag_response.content[0].text.strip()
        
        chat_response = client.messages.create(
            model=MODEL,
            max_tokens=INTERVEW_AI_MAX_TOKENS,
            temperature=INTERVEW_AI_TEMPERATURE,
            system=SYSTEM_MESSAGE,
            messages=[
                {
                    "role": "user",
                    "content": [
                        INTERVIEW_AI_EXAMPLES,
                        {
                            "type": "text",
                            "text": f"<interview_prompt>\n{request.prompt}\n</interview_prompt>"
                        }
                    ]
                }
            ]
        )
        
        # remove the XML tags from the response
        formatted_text = get_formatted_text(chat_response.content[0].text, r"<answer>(.*?)</answer>")
        
        messages = [
            {"role": "user", "content": request.prompt},
            {"role": "assistant", "content": formatted_text}
        ]
        
        db = SessionLocal()
        db_message = ChatMessage(tag=tag, messages=messages)
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        
        data = {
            "conversation_id": db_message.conversation_id,
            "tag": tag,
            "messages": messages,
        }
        
        return JSONResponse(content={
            "data": data,
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
        
        
        existing_messages = conversation.messages # get all messages
        
        chat_response = client.messages.create(
            model=MODEL,
            max_tokens=INTERVEW_AI_MAX_TOKENS,
            temperature=INTERVEW_AI_TEMPERATURE,
            system=SYSTEM_MESSAGE,
            messages=[
                *existing_messages,
                {
                    "role": "user",
                    "content": [
                        INTERVIEW_AI_EXAMPLES,
                        {
                            "type": "text",
                            "text": f"<interview_prompt>\n{request.prompt}\n</interview_prompt>"
                        }
                    ]
                }
            ]
        )
        
        # remove the XML tags from the response
        formatted_text = get_formatted_text(chat_response.content[0].text, r"<answer>(.*?)</answer>")
        
        # Add new messages to existing conversation
        new_messages = existing_messages + [
            {"role": "user", "content": request.prompt},
            {"role": "assistant", "content": formatted_text}
        ]
        
        conversation.messages = new_messages
        db.commit()
        db.refresh(conversation)
        
        return JSONResponse(content={
            "data": formatted_text,
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
        
@router.delete("/delete-conversation")
async def delete_conversation(request: DeleteConversationRequest):
    try:
        db = SessionLocal()
        conversation = db.query(ChatMessage).filter(ChatMessage.conversation_id == request.conversation_id).first()
        
        if not conversation:
            return JSONResponse(content={
                "data": {},
                "message": "Conversation not found",
                "error": True
            }, status_code=404)
        
        db.delete(conversation)
        db.commit()
        
        return JSONResponse(content={
            "data": {
                "conversation_id": request.conversation_id,
                "message": "Conversation deleted successfully"
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