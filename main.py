from dotenv import load_dotenv
load_dotenv()
from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarize import summarize, generate_title
from core.extractor import extract_action_items,extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question

def run_pipeline(source:str, language:str ="english") -> dict:
    
    print("Staring AI Video Assistant!")
    print("="*60)

    print("\nStep1: Processing Input Audio...")

    chunks = process_input(source)

    transcript = transcribe_all(chunks,language=language)
    print(f"Raw Transcript(first 300 characters):\n{transcript[:300]}\n")

    title = generate_title(transcript)
    print(f"Generated Title :\n{title}\n")

    summary = summarize(transcript)
    print(f"Generated Summary:\n{summary}\n")

    action_item = extract_action_items(transcript)
    print(f"Generated Action Items:\n{action_item}\n")

    decisions = extract_key_decisions(transcript)
    print(f"Generated Key Decisions:\n{decisions}\n")

    questions = extract_questions(transcript)
    print(f"Generated Questions:\n{questions}\n")

    rag_chain = build_rag_chain(transcript)

    return {
        "title":title,
        "transcript":transcript,
        "summary":summary,
        "action_items":action_item,
        "key_decisions":decisions,
        "open_questions":questions,
        "rag_chain":rag_chain
    }

if __name__=="__main__":
    
    #CLI entry point
    source = input("Enter source path or URL: ").strip()
    language = input("Enter language (default: english)").strip() or "english"
    results = run_pipeline(source,language)
    
    print("\n" + "=" * 60)
    print(f"x Title: {results['title']}")
    print(f"\n Summary:\n{results['summary' ]}")
    print(f"\n Action Items:\n{results['action_items' ]}")
    print(f"\n Key Decisions:\n{results['key_decisions' ]}")
    print(f"\n? Open Questions:\n{results['open_questions' ]}")
    print("=" * 60)

    rag_chain = results["rag_chain"]

    # Phase 2 - Chat with your meeting via RAG
    print("\n Chat with your meeting (type 'exit' .to quit) \n")
    while True:
        question = input("You: ").strip()
        if question. lower() in ["exit", "quit", "q"] :
            print("Thank you for using AI Video Assistant!")
            break

        if not question:
            continue
        answer = ask_question(rag_chain, question)
        print(f"\n Assistant: {answer}\n")

    
    

    