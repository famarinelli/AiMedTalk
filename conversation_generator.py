import os
import time
import argparse
from dotenv import load_dotenv
from google import genai
from google.genai import types
# --------------------------------------------------------------------------
# --- CONFIGURATION PARAMETERS ---
# --------------------------------------------------------------------------

parser = argparse.ArgumentParser(description="Generate synthetic clinical dialogues using Gemini AI.")
    
# General Settings
parser.add_argument("-n", "--num-conversations", type=int, default=1, 
                    help="Number of conversations to generate.")
parser.add_argument("-o", "--output-dir", type=str, default="generated_conversations", 
                    help="Directory to save the generated conversation files.")

# args.language Settings
parser.add_argument("-l", "--language", type=str, default="en", choices=['en', 'it'], 
                    help="language for the generation prompts (en or it).")

# Model and Generation Settings
parser.add_argument("-m", "--model", type=str, default="gemini-2.5-flash", 
                    help="Name of the Gemini model to use.")
parser.add_argument("--max-tokens", type=int, default=10000, 
                    help="Maximum number of tokens to generate per API request.")

# Conversation Logic Settings
parser.add_argument("--max-exchanges", type=int, default=5, 
                    help="Total number of exchanges (doctor-patient pair) per conversation.")
parser.add_argument("--exchanges-per-call", type=int, default=5, 
                    help="Number of exchanges to request in a single API call (chunk size).")

# API Limit Settings
parser.add_argument("--rpm", type=int, default=9, 
                    help="Maximum API requests per minute (for rate limiting).")

args = parser.parse_args()

# --------------------------------------------------------------------------
# --- PROMPT TEMPLATES (MULTI-args.language) ---
# --------------------------------------------------------------------------

PROMPT_TEMPLATES = {
    "en": {
        "main": """
You are a clinical dialogue simulator. Your task is to generate a realistic, detailed, and lengthy conversation between a hematologist and a patient with Leukemia.

CONTEXT:
- Disease: Leukemia. The patient is undergoing treatment or is in a follow-up phase.
- Dialogue Goal: The conversation must explore not only the clinical aspects (test results, therapy) but also, and more importantly, the psychological and emotional impact on the patient. Touch on topics related to:
  - Physical symptoms (fatigue, pain, nausea - related to ESAS).
  - Emotional state (anxiety, depression, fears, hopes - related to HADS).
  - Quality of life (impact on family, work, social life - related to FACT-Leu).
  - Coping strategies (how the patient deals with stress and the illness - related to COPE).

MANDATORY FORMATTING RULES:
1.  Each turn must start with ">dr: " for the doctor or ">pz: " for the patient, followed by a newline.
2.  Each exchange (a dr/pz pair) must be numbered, starting with "#" followed by the number, something like:
    '''
    #1
    >dr: <first doc message>
    >pz: <first patient message>
    #2
    >dr: <second doc message>
    >pz: <second patient message>
    ...
    '''
3.  Never generate more than {exchanges_per_call} exchanges in this response.

INSTRUCTIONS:
{instruction}

{conversation_history}
""",
        "final": """
This is a conversation between a doctor and a patient. The appointment is about to end.
Generate one final exchange, number #{final_exchange_number}, where the doctor and patient say goodbye and conclude the meeting naturally. Maintain the same format as before.

CONVERSATION SO FAR:
---
{conversation_history}
---
"""
    },
    "it": {
        "main": """
Sei un simulatore di dialoghi clinici. Il tuo compito è generare una conversazione realistica, dettagliata e lunga tra un medico ematologo e un paziente affetto da Leucemia.

CONTESTO:
- Malattia: Leucemia. Il paziente è in una fase di trattamento o follow-up.
- Obiettivo del dialogo: La conversazione deve esplorare non solo gli aspetti clinici (risultati degli esami, terapia), ma anche e soprattutto l'impatto psicologico ed emotivo sul paziente. Tocca argomenti relativi a:
  - Sintomi fisici (stanchezza, dolore, nausea - legati a ESAS).
  - Stato emotivo (ansia, depressione, paure, speranze - legati a HADS).
  - Qualità della vita (impatto sulla famiglia, lavoro, socialità - legati a FACT-Leu).
  - Strategie di coping (come il paziente affronta lo stress e la malattia - legati a COPE).

REGOLE DI FORMATTAZIONE OBBLIGATORIE:
1.  Ogni intervento deve iniziare con ">dr: " per il medico o ">pz: " per il paziente, seguito da un a capo.
2.  Ogni scambio (coppia dr/pz) deve essere numerato, iniziando con "#" seguito dal numero. Esempio:
    '''
    #1
    >dr: <primo messaggio dottore>
    >pz: <primo messaggio paziente>
    #2
    >dr: <secondo messaggio dottore>
    >pz: <secondo messaggio paziente>
    ...
    '''
3.  Non generare mai più di {exchanges_per_call} scambi in questa risposta.
ISTRUZIONI:
{instruction}

{conversation_history}
""",
        "final": """
Questa è una conversazione tra un medico e un paziente. La visita sta per finire.
Genera un ultimo scambio, il numero #{final_exchange_number}, in cui il medico e il paziente si salutano e concludono l'incontro in modo naturale. Mantieni lo stesso formato di prima.

CONVERSAZIONE FINO AD ORA:
---
{conversation_history}
---
"""
    }
}


# --------------------------------------------------------------------------
# --- SCRIPT LOGIC ---
# --------------------------------------------------------------------------

def get_last_exchange_number(text):
    """Extracts the last exchange number from the generated text."""
    last_num = 0
    lines = text.strip().split('\n')
    for line in lines:
        if line.startswith('#'):
            try:
                num = int(line.replace('#', '').strip())
                if num > last_num:
                    last_num = num
            except ValueError:
                continue
    return last_num

def generate_chunk(client:genai.Client, prompt_text):
    """
    Function to make a single API call to Gemini using a Client object and return the text.
    """
    print("   > Sending request to the model...")
    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt_text)],
        ),
    ]    
    
    generation_config = types.GenerateContentConfig(
        max_output_tokens=args.max_tokens
    )

    # try:
    # Usiamo generate_content (non-stream) invece di generate_content_stream
    response = client.models.generate_content(
        model=f"models/{args.model}", # Il client richiede il prefisso "models/"
        contents=contents,
        config=generation_config,
    )

    tokens_generated = response.usage_metadata.candidates_token_count

    time.sleep(1)
    return response.text, tokens_generated
    # except Exception as e:
    #     print(f"   !!! An error occurred during the API call: {e}")
    #     return ""


def main():
    """
    Main pipeline for generating the conversations.
    """
    

    load_dotenv()

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("The GEMINI_API_KEY environment variable is not set.")
    client = genai.Client(api_key=api_key)

    if args.language not in PROMPT_TEMPLATES:
        raise ValueError(f"args.language '{args.language}' not supported. Available args.languages are: {list(PROMPT_TEMPLATES.keys())}")

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
        print(f"Directory '{args.output_dir}' created.")

    rate_limit_delay = 60.0 / args.rpm

    for i in range(1, args.num_conversations + 1):
        print(f"\n--- Starting Generation for Conversation #{i} (args.language: {args.language.upper()}) ---")
        
        full_conversation_text = ""
        current_exchange = 1
        total_tokens_generated = 0
        
        # --- Loop to generate the body of the conversation ---
        while current_exchange < args.max_exchanges:
            print(f"  Generating exchanges starting from #{current_exchange}...")
            
            history_keyword = "CONVERSATION SO FAR" if args.language == "en" else "CONVERSAZIONE FINO AD ORA"

            if not full_conversation_text:
                # Prompt for the first call
                instruction = "Start the conversation from the first exchange (#1)." if args.language == "en" else "Inizia la conversazione dal primo scambio (#1)."
                history = ""
            else:
                # Prompt for subsequent calls
                instruction = f"Continue the conversation starting from the next exchange (#{current_exchange})." if args.language == "en" else f"Continua la conversazione partendo dal prossimo scambio (#{current_exchange})."
                history = f"{history_keyword}:\n---\n{full_conversation_text}\n---"

            prompt = PROMPT_TEMPLATES[args.language]['main'].format(
                exchanges_per_call=args.exchanges_per_call,
                instruction=instruction,
                conversation_history=history
            )
            
            generated_text, tokens_in_chunk = generate_chunk(client, prompt)
            total_tokens_generated += tokens_in_chunk
            
            if generated_text:
                full_conversation_text += generated_text.strip() + "\n\n"
                last_num = get_last_exchange_number(generated_text)
                if last_num > 0:
                    current_exchange = last_num + 1
                else:
                    # Failsafe to prevent infinite loops
                    print("   !!! Warning: Could not parse the last exchange number.")
                    current_exchange += args.exchanges_per_call
            else:
                print("   !!! API response was empty. Stopping this conversation.")
                break # Exit the while loop if the API fails

            # Apply rate limiting
            print(f"   Waiting for {rate_limit_delay:.1f} seconds to respect API limits...")
            time.sleep(rate_limit_delay)

        # --- Generate the final closing exchange ---
        print(f"  Generating final closing exchange (#{args.max_exchanges})...")
        final_prompt = PROMPT_TEMPLATES[args.language]['final'].format(
            final_exchange_number=args.max_exchanges,
            conversation_history=full_conversation_text
        )
        
        final_chunk, tokens_in_chunk = generate_chunk(client, final_prompt)
        total_tokens_generated += tokens_in_chunk

        full_conversation_text += final_chunk.strip()
        
        # --- Save the file ---
        output_filename = os.path.join(args.output_dir, f"conversation_leukemia_{args.language}_{i}.txt")
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(full_conversation_text)
            
        print(f"   Total tokens generated for this conversation: {total_tokens_generated}")
        print(f"--- Conversation #{i} completed and saved to '{output_filename}' ---")

if __name__ == "__main__":
    main()