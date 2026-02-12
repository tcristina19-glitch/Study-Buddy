from pypdf import PdfReader
from openai import AzureOpenAI
import json
from datetime import datetime
import os
import glob

# Fișier pentru salvare conversații
HISTORY_FILE = "study_sessions.json"
# ===== CONFIGURARE AZURE =====
client = AzureOpenAI(
    api_key="YOUR-API-KEY-HERE",  # ← Replace with your Azure OpenAI API key
    api_version="2024-08-01-preview",
    azure_endpoint="YOUR-ENDPOINT-HERE"  # ← Replace with your Azure endpoint
)
# ===== FUNCȚII SALVARE/ÎNCĂRCARE =====
def save_session(conversation, pdf_name):
    """Salvează sesiunea de studiu în fișier JSON"""
    try:
        # Încarcă sesiuni existente
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                sessions = json.load(f)
        else:
            sessions = []
        
        # Adaugă sesiunea curentă
        session = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "pdf_document": pdf_name,
            "conversation": conversation,
           "num_questions": len([m for m in conversation if m["role"] == "user"])  
        }
        
        sessions.append(session)
        
        # Salvează
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(sessions, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Sesiune salvată! Total sesiuni: {len(sessions)}")
        return True
        
    except Exception as e:
        print(f"\n⚠️ Nu am putut salva sesiunea: {e}")
        return False

def view_history():
    """Afișează istoricul sesiunilor de studiu"""
    try:
        if not os.path.exists(HISTORY_FILE):
            print("\n📭 Nu există încă sesiuni salvate!")
            return
        
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            sessions = json.load(f)
        
        if not sessions:
            print("\n📭 Nu există încă sesiuni salvate!")
            return
        
        print("\n" + "="*60)
        print(f"📚 ISTORIC SESIUNI DE STUDIU ({len(sessions)} sesiuni)")
        print("="*60)
        
        for i, session in enumerate(sessions, 1):
            print(f"\n{i}. 📅 {session['timestamp']}")
            print(f"   📄 Document: {session['pdf_document']}")
            print(f"   💬 Întrebări puse: {session['num_questions']}")
            
            # Afișează primele 2 întrebări
            user_messages = [m for m in session['conversation'] if m['role'] == 'user']
            if user_messages:
                print(f"   🔹 Prima întrebare: {user_messages[0]['content'][:60]}...")
        
        print("\n" + "="*60)
        
    except Exception as e:
        print(f"\n⚠️ Eroare la citirea istoricului: {e}")
# ===== ALEGERE PDF =====
print("\n" + "="*70)
print("  📚 STUDY BUDDY - Asistentul tău inteligent de învățare")
print("="*70)
print("\n📁 Fișiere PDF disponibile în folder:")
print("─"*70)

# Listăm PDF-urile din folder
import glob
pdf_files = glob.glob("*.pdf")

if not pdf_files:
    print("❌ Nu am găsit niciun PDF în folderul curent!")
    print("💡 Pune un fișier PDF în folderul hackathon și încearcă din nou.")
    exit()

for i, pdf_file in enumerate(pdf_files, 1):
    # Calculăm dimensiunea
    size_bytes = os.path.getsize(pdf_file)
    size_mb = size_bytes / (1024 * 1024)
    print(f"  {i}. 📄 {pdf_file} ({size_mb:.2f} MB)")

print("─"*70)

# User alege PDF-ul
while True:
    choice = input("\n🔹 Alege numărul PDF-ului (sau scrie numele complet): ").strip()
    
    # Verificăm dacă e număr
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(pdf_files):
            pdf_name = pdf_files[idx]
            break
        else:
            print(f"❌ Alege un număr între 1 și {len(pdf_files)}!")
    # Verificăm dacă e nume fișier
    elif choice in pdf_files:
        pdf_name = choice
        break
    elif choice + ".pdf" in pdf_files:
        pdf_name = choice + ".pdf"
        break
    else:
        print(f"❌ Nu găsesc '{choice}'. Încearcă din nou!")

print(f"\n📖 Încarcă documentul: {pdf_name}...")

# ===== CITIM PDF-UL =====
try:
    reader = PdfReader(pdf_name)
    
    # Extragem tot textul din PDF
    full_text = ""
    for page in reader.pages:
        full_text += page.extract_text() + "\n"
    
    # Limităm la primele 3000 caractere (pentru început)
    document_text = full_text[:12000]
    
    print("\n" + "="*70)
    print("  📚 STUDY BUDDY - Asistentul tău inteligent de învățare")
    print("="*70)
    print(f"\n✅ Document încărcat: {pdf_name}")
    print(f"📄 Pagini: {len(reader.pages)}")
    print(f"📊 Text procesat: {len(document_text):,} caractere (din {len(full_text):,} total)")
    
    print("\n" + "─"*70)
    print("💡 COMENZI DISPONIBILE:")
    print("─"*70)
    print("  🔹 Scrie orice întrebare despre document")
    print("  📝 'summary'  → Rezumat document în 3-4 propoziții")
    print("  🎯 'quiz'     → Generează quiz cu 5 întrebări")
    print("  📚 'history'  → Vezi sesiunile tale anterioare")
    print("  🚪 'exit'     → Salvează și ieși")
    print("─"*70 + "\n")
    
    # ===== CONVERSAȚIE CU AI =====
    conversation_history = [
        {
            "role": "system",
            "content": f"""Ești un asistent de învățare care ajută utilizatorul să înțeleagă un document.

DOCUMENTUL:
{document_text}

INSTRUCȚIUNI:
- Răspunde în ROMÂNĂ
- Bazează-te DOAR pe informațiile din document
- Dacă întrebarea nu e în document, spune "Nu găsesc informația în document"
- Fii concis și clar
- Folosește exemple din document când explici"""
        }
    ]
    
    # Loop conversație
    while True:
        user_input = input("Tu: ").strip()
        
        if not user_input:
            continue
            
        if user_input.lower() == "history":
            view_history()
            continue   
        if user_input.lower() == "exit":
            print("\n💾 Salvez sesiunea...")
            save_session(conversation_history, pdf_name)
            print("\n" + "="*70)
            print("  👋 LA REVEDERE! Învățare plăcută!")
            print("  💡 Sesiunea ta a fost salvată. Rulează din nou pentru a continua!")
            print("="*70 + "\n")
            break
        if user_input.lower() == "summary":
            user_input = "Fă un rezumat al documentului în 3-4 propoziții."
        if user_input.lower() == "quiz":
            user_input = """Generează un quiz cu 5 întrebări tip grilă pe baza documentului.

FORMATUL EXACT:
📝 QUIZ pe baza documentului:

1. [Întrebarea 1]
   a) [Răspuns greșit]
   b) [Răspuns corect]
   c) [Răspuns greșit]
   d) [Răspuns greșit]

2. [Întrebarea 2]
   ...

📊 Răspunsuri corecte: 1-b, 2-c, 3-a, 4-d, 5-b

REGULI:
- Întrebările să fie bazate STRICT pe informații din document
- Fiecare întrebare să aibă UN SINGUR răspuns corect
- Răspunsurile greșite să fie plauzibile
- Întrebările să acopere concepte diferite din document"""
            
        
        # Adăugăm mesajul utilizatorului
        conversation_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Loading indicator
        print("\n🤔 AI gândește", end="", flush=True)
        import time
        
        # Apelăm AI-ul
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=conversation_history,
                temperature=0.7,
                max_tokens=2000
            )
            
            ai_response = response.choices[0].message.content
            
            # Adăugăm răspunsul AI-ului
            conversation_history.append({
                "role": "assistant",
                "content": ai_response
            })
            
            # Clear loading
            print("\r" + " " * 50 + "\r", end="")
            
            # Afișare răspuns cu formatare
            print("\n" + "─" * 60)
            print(f"🤖 AI:\n")
            print(ai_response)
            print("─" * 60 + "\n")
            
        except Exception as e:
            print(f"\n❌ Eroare API: {e}\n")

except FileNotFoundError:
    print("❌ EROARE: Nu găsesc python_modules.pdf!")
    print("Verifică că fișierul e în folderul hackathon!")
    
except Exception as e:
    print(f"❌ EROARE: {e}")