import requests, json
from io import BytesIO
from main import app  
from fastapi.testclient import TestClient

client = TestClient(app)

URL = "http://127.0.0.1:8000"

# ! Chat Bot tests

def validate_message_structure(messages):
    """Helper function to validate message structure"""
    assert isinstance(messages, list), "Messages should be a list"
    for i, message in enumerate(messages):
        assert "role" in message, f"Message {i} missing role"
        assert "content" in message, f"Message {i} missing content"
        assert message["role"] in ["user", "assistant"], f"Invalid role in message {i}"
        assert isinstance(message["content"], str), f"Content should be string in message {i}"
        assert len(message["content"]) > 0, f"Content empty in message {i}"
        
        if i % 2 == 0:
            assert message["role"] == "user", f"Even-indexed message {i} should be user"
        else:
            assert message["role"] == "assistant", f"Odd-indexed message {i} should be assistant"

def test_create_conversation():
    url = URL + "/create-conversation"
    payload = {"prompt": "How should I prepare for a coding interview?"}
    
    response = client.post(url, json=payload)
    
    assert response.status_code == 200
    
    data = response.json()
    
    assert data["error"] == False
    assert "conversation_id" in data["data"]
    assert "tag" in data["data"]
    assert "messages" in data["data"]
    
    messages = data['data']['messages']
    validate_message_structure(messages)
    
def test_get_conversation():
    url = URL + "/create-conversation"
    payload = {"prompt": "How do I answer behavioral questions?"}
    
    create_response = client.post(url, json=payload)
   
    conversation_id = create_response.json()["data"]["conversation_id"]
    
    url = URL + "/get-conversation"
    payload = {"conversation_id": conversation_id}
    
    response = client.post(url, json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["error"] == False
    assert data["data"]["conversation_id"] == conversation_id

def test_get_nonexistent_conversation():
    url = URL + "/get-conversation"
    payload = {"conversation_id": 999999}
    
    response = client.post(url, json = payload)
    
    assert response.status_code == 404
    
    data = response.json()
    
    assert data["error"] == True
    assert data["message"] == "Conversation not found"

def test_update_conversation():
    # First create a conversation
    url = URL + "/create-conversation"
    payload = {"prompt": "What are common coding interview questions?"}
    
    create_response = client.post(url, json = payload)
   
    conversation_id = create_response.json()["data"]["conversation_id"]
    
    # Then update it
    url = URL + "/update-conversation"
    payload = {"conversation_id": conversation_id, "prompt": "Can you give more specific examples?"}
    
    response = client.put(url, json = payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["error"] == False
    assert "data" in data
    
    assert isinstance(data['data'], str), f"'data' field should be a str"
     
def test_update_nonexistent_conversation():
    url = URL + "/update-conversation"
    payload = {"conversation_id": 999999, "prompt": "This conversation doesn't exist"}
    
    response = client.put(url, json = payload)
    
    assert response.status_code == 404
    
    data = response.json()
    assert data["error"] == True
    assert data["message"] == "Conversation not found"

def test_delete_conversation():
    create_response = client.post(
        url=URL + "/create-conversation",
        json={"prompt": "How do I prepare for a coding interview?"}
    )
    
    conversation_id = create_response.json()["data"]["conversation_id"]
    
    delete_response = client.request(
        method="DELETE",
        url=URL + "/delete-conversation",
        json={"conversation_id": conversation_id},
    )
    
    assert delete_response.status_code == 200
    data = delete_response.json()
    assert data["error"] == False
    assert data["message"] == "Success"
    assert data["data"]["conversation_id"] == conversation_id
    
    # Verify conversation is deleted by trying to get it
    get_response = client.post(
        url=URL + "/get-conversation",
        json={"conversation_id": conversation_id}
    )
    assert get_response.status_code == 404
    assert get_response.json()["error"] == True

def test_delete_nonexistent_conversation():
    response = client.request(
        method="DELETE",
        url=URL + "/delete-conversation",
        json={"conversation_id": 999999},
    )
    assert response.status_code == 404
    data = response.json()
    assert data["error"] == True
    assert data["message"] == "Conversation not found"

def test_invalid_conversation_id_format():
    url = URL + "/get-conversation"
    payload = {"conversation_id": "invalid"}
    
    response = client.post(url, json = payload)
    
    assert response.status_code == 422

# def helper_func(url, payload, status_code, message, error, data_type):
#     response = requests.post(url, data=payload)

#     assert response.status_code == status_code, f"Unexpected status code: {response.status_code}"
    
#     response_data = response.json()

#     assert "data" in response_data, "Missing 'data' field in response"
#     assert "message" in response_data, "Missing 'message' field in response"
#     assert "error" in response_data, "Missing 'error' field in response"
    
#     assert response_data["message"] == message
#     assert response_data["error"] is error, "Error field value mismatch"
    
#     assert isinstance(response_data["data"], data_type), f"'data' field should be a {data_type}"

# def test_resume_review():
#     url = URL + "/resume-review"
#     job_description = "Software Engineer position with 5+ years of experience..."
    
#     payload = {
#         'file': open('resume.pdf', 'rb'),
#         'job_description': (None, job_description)  # None means no filename for form field
#     }
    
#     helper_func(url=url, payload=payload, status_code=200, message="Success", error=False, data_type=str)


# def test_cover_letter_generator():
    
#     job_description = "We are looking for a talented software engineer with expertise in Python and experience with cloud-based systems."

#     with open("resume.pdf", "rb") as pdf_file:
#         pdf_content = pdf_file.read()

#     # Mock file object
#     file = ("file", ("resume.pdf", BytesIO(pdf_content), "application/pdf"))
    
#     # Make a POST request to the cover letter generator endpoint
#     response = client.post(
#         "/cover-letter-generator",
#         files={"file": file},
#         data={"job_description": job_description},
#     )
    
#     # Assertions to check the response
#     assert response.status_code == 200, f"Unexpected status code: {response.status_code}"
#     response_data = response.json()
#     assert not response_data["error"], f"Error occurred: {response_data['message']}"
#     assert response_data["data"], "Cover letter was not generated successfully."

#     print("Generated Cover Letter:", response_data["data"])
    
