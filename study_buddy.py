from pypdf import PdfReader
from openai import AzureOpenAI
import json
from datetime import datetime
import os
import glob

# File for saving conversations
HISTORY_FILE = "study_sessions.json"
# ===== AZURE CONFIGURATION =====
client = AzureOpenAI(
    api_key="YOUR-API-KEY-HERE",  # ← Replace with your Azure OpenAI API key
    api_version="2024-08-01-preview",
    azure_endpoint="YOUR-ENDPOINT-HERE"  # ← Replace with your Azure endpoint
)
# ===== SAVE/LOAD FUNCTIONS =====
def save_session(conversation, pdf_name):
    """Saves study session to JSON file"""
    try:
        # Load existing sessions
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                sessions = json.load(f)
        else:
            sessions = []
        
        # Add current session
        session = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "pdf_document": pdf_name,
            "conversation": conversation,
            "num_questions": len([m for m in conversation if m["role"] == "user"])  
        }
        
        sessions.append(session)
        
        # Save
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(sessions, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Session saved! Total sessions: {len(sessions)}")
        return True
        
    except Exception as e:
        print(f"\n⚠️ Could not save session: {e}")
        return False

def view_history():
    """Displays study session history"""
    try:
        if not os.path.exists(HISTORY_FILE):
            print("\n📭 No saved sessions yet!")
            return
        
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            sessions = json.load(f)
        
        if not sessions:
            print("\n📭 No saved sessions yet!")
            return
        
        print("\n" + "="*60)
        print("📚 STUDY BUDDY - AI Learning Assistant 📚".center(60))
        print("="*60)
        
        for i, session in enumerate(sessions, 1):
            print(f"\n{i}. 📅 {session['timestamp']}")
            print(f"   📄 Document: {session['pdf_document']}")
            print(f"   💬 Questions asked: {session['num_questions']}")
            
            # Display first 2 questions
            user_messages = [m for m in session['conversation'] if m['role'] == 'user']
            if user_messages:
                print(f"   🔹 First question: {user_messages[0]['content'][:60]}...")
        
        print("\n" + "="*60)
        
    except Exception as e:
        print(f"\n⚠️ Error reading history: {e}")

# ===== PDF SELECTION =====
print("\n" + "="*70)
print("  📚 STUDY BUDDY - AI Learning Assistant")
print("="*70)
print(f"\n📁 Available PDFs:")
print("─"*70)

# List PDFs in folder
import glob
pdf_files = glob.glob("*.pdf")

if not pdf_files:
    print("❌ No PDF files found in current folder!")
    print("💡 Place a PDF file in the hackathon folder and try again.")
    exit()

for i, pdf_file in enumerate(pdf_files, 1):
    # Calculate size
    size_bytes = os.path.getsize(pdf_file)
    size_mb = size_bytes / (1024 * 1024)
    print(f"  {i}. 📄 {pdf_file} ({size_mb:.2f} MB)")

print("─"*70)

# User chooses PDF
while True:
    choice = input("\n🔹 Choose PDF number or write full name: ").strip()
    
    # Check if it's a number
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(pdf_files):
            pdf_name = pdf_files[idx]
            break
        else:
            print(f"Choose a number between 1 and {len(pdf_files)}!")
    # Check if it's a file name
    elif choice in pdf_files:
        pdf_name = choice
        break
    elif choice + ".pdf" in pdf_files:
        pdf_name = choice + ".pdf"
        break
    else:
        print(f"Cannot find '{choice}'. Try again!")

print(f"\n📖 Loading document: {pdf_name}...")

# ===== READ PDF =====
try:
    reader = PdfReader(pdf_name)
    
    # Extract all text from PDF
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text() + "\n"
    
    # Limit to first 12000 characters (for start)
    document_text = full_text[:12000]
    
    print("\n" + "="*70)
    print("  📚 STUDY BUDDY - AI Learning Assistant")
    print("="*70)
    print(f"\n✅ Document loaded: {pdf_name}")
    print(f"📄 Pages: {len(reader.pages)}")
    print(f"📊 Text extracted: {len(document_text):,} characters (from {len(full_text):,} total)")
    
    print("\n" + "─"*70)
    print("💡 AVAILABLE COMMANDS:")
    print("─"*70)
    print("  🔹 Write any question about the document")
    print("  📝 'summary'  → Document summary in 3-4 sentences")
    print("  🎯 'quiz'     → Generate quiz with 5 questions")
    print("  📚 'history'  → View your previous sessions")
    print("  🚪 'exit'     → Save and exit")
    print("─"*70 + "\n")
    
    # ===== AI CONVERSATION =====
    conversation_history = [
        {
            "role": "system",
            "content": f"""You are a learning assistant helping the user understand a document.

DOCUMENT:
{document_text}

INSTRUCTIONS:
- Answer in ENGLISH
- Base answers ONLY on information from the document
- If the question is not in the document, say "I cannot find this information in the document"
- Be concise and clear
- Use examples from the document when explaining"""
        }
    ]
  # Conversation loop
    while True:
        user_input = input("You: ").strip()
        
        if not user_input:
            continue
            
        if user_input.lower() == "history":
            view_history()
            continue   
        if user_input.lower() == "exit":
            print("\n💾 Saving session...")
            save_session(conversation_history, pdf_name)
            print("\n" + "="*70)
            print("  👋 GOODBYE! Happy learning!")
            print("  💡 Your session has been saved. Run again to continue!")
            print("="*70 + "\n")
            break
        if user_input.lower() == "summary":
            user_input = "Create a summary of the document in 3-4 sentences."
        if user_input.lower() == "quiz":
            user_input = """Generate a quiz with 5 multiple-choice questions based on the document.

EXACT FORMAT:
📝 QUIZ based on the document:

1. [Question 1]
   a) [Wrong answer]
   b) [Correct answer]
   c) [Wrong answer]
   d) [Wrong answer]

2. [Question 2]
   ...

📊 Correct answers: 1-b, 2-c, 3-a, 4-d, 5-b

RULES:
- Questions must be based STRICTLY on information from the document
- Each question must have ONE CORRECT answer only
- Wrong answers should be plausible
- Questions should cover different concepts from the document"""

       # Add user message
        conversation_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Loading indicator
        print("\n🤔 AI thinking", end="", flush=True)
        import time
        
        # Call AI
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=conversation_history,
                temperature=0.7,
                max_tokens=2000
            )
            
            ai_response = response.choices[0].message.content
            
            # Add AI response
            conversation_history.append({
                "role": "assistant",
                "content": ai_response
            })
            
            # Clear loading
            print("\r" + " " * 50 + "\r", end="")
            
            # Display response with formatting
            print("\n" + "─" * 60)
            print(f"🤖 AI:\n")
            print(ai_response)
            print("─" * 60 + "\n")
            
        except Exception as e:
            print(f"\n❌ API Error: {e}\n")

except FileNotFoundError:
    print("❌ ERROR: Cannot find the PDF file!")
    print("Check that the file is in the hackathon folder!")
    
except Exception as e:
    print(f"❌ ERROR: {e}")