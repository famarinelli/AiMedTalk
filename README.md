# AiMedTalk Dialogue Generator 🗣️ 

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python tool for generating realistic, synthetic clinical dialogues between doctors and patients using the Gemini API. This project aims to create high-quality corpora for NLP research in healthcare.

## Project Overview

This project addresses a common challenge in medical NLP research: the scarcity of real-world conversational data due to strict privacy regulations like GDPR and HIPAA. **AiMedTalk** provides a script to generate a corpus of high-quality synthetic dialogues, specifically focused on conversations between an oncologist/hematologist and a patient with Leukemia.

The goal is to produce data that not only reflects clinical discussions but also captures the patient's emotional and psychological nuances. This makes the generated corpus ideal for training and validating models that aim to correlate language with Patient-Reported Outcomes (PROs).

## Key Features

-   **Realistic Dialogue Generation**: Leverages the power of Google's Gemini models to create fluent and contextually appropriate conversations.
-   **Specific Clinical Focus**: Prompts are engineered to generate dialogues about Leukemia, covering topics related to symptoms, anxiety, depression, and coping strategies.
-   **Long Conversation Handling**: Overcomes the token limits of standard models through a "chunking" logic that breaks down the generation into multiple API calls while maintaining dialogue coherence.
-   **Structured Formatting**: The output is clean and easy to parse, with clear speaker distinction (`>dr:`, `>pz:`) and exchange numbering.
-   **API Rate Limiting**: Includes a built-in rate limiter to avoid exceeding API request quotas.
-   **Flexible Configuration**: All key parameters (number of conversations, length, model, etc.) are configurable via command-line arguments.

## Installation

To run this script, you need Python 3.7+ installed.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/AiMedTalk.git
    cd AiMedTalk
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up your API key:**
    You need to provide your Google Gemini API key. There are two ways to do this:

    **Method 1 (Recommended): Using a `.env` file**

    This is the safest method as it prevents you from accidentally committing your API key to version control.

    1.  Create a file named `.env` in the root directory of the project.
    2.  Add the following line to the file, replacing `YOUR_API_KEY_HERE` with your actual key:
        ```
        GEMINI_API_KEY="YOUR_API_KEY_HERE"
        ```

    **Method 2 (Alternative): Using an Environment Variable**

    You can set the API key directly in your terminal session. This method overrides the `.env` file if both are present.

    *   On macOS/Linux:
        ```bash
        export GEMINI_API_KEY="YOUR_API_KEY_HERE"
        ```
    *   On Windows (Command Prompt):
        ```bash
        set GEMINI_API_KEY="YOUR_API_KEY_HERE"
        ```


## Usage

The script is executed from the command line, and all parameters can be customized using flags. If a flag is not provided, its default value will be used.

**1. See All Available Options**

To get a full list of all configurable parameters, their descriptions, and default values, run:
```bash
python conversation_generator.py --help
```

**2. Run the Script**

**Basic Usage**

Running the script without any arguments will generate one conversation using the default settings (English, 5 exchanges, etc.).
```bash
python conversation_generator.py
```

**Advanced Usage Example**

You can combine multiple flags to customize the generation. Here is an example that generates **5 longer conversations (30 exchanges each) in Italian**, saving them to a custom directory named `italian_dialogues`:
```bash
python conversation_generator.py \
  -n 5 \
  -l it \
  --max-exchanges 30 \
  --exchanges-per-call 15 \
  -o ./italian_dialogues
```

**3. Check the Output**

The script will create a directory named `generated_conversations` (or the custom name you provide) and save each complete dialogue in a separate `.txt` file.

The output inside each file will follow this format:
```
#1
>dr: Good morning, how have you been feeling this week?
>pz: Quite tired, doctor. It's been a tough week.
#2
>dr: I'm sorry to hear that. Let's go over your latest test results.
>pz: Of course, I hope there's good news.
...
```
## Example Outputs

To provide a clear example of the final output, this repository includes two pre-generated conversations located in the `generated_conversations` directory:

-   [`conversation_leukemia_en_1.txt`](./generated_conversations/conversation_leukemia_en_1.txt): A full sample conversation generated in English.
-   [`conversation_leukemia_it_1.txt`](./generated_conversations/conversation_leukemia_it_1.txt): A full sample conversation generated in Italian.

## How It Works

The generator uses an iterative approach:
1.  **Initial Prompt**: It sends a detailed prompt to the Gemini model, asking it to start a conversation and generate a predefined number of exchanges.
2.  **Chunk Generation**: If the target conversation is longer than the number of exchanges generated in a single call, the script captures the generated text.
3.  **Continuation Prompt**: It sends a new prompt that includes the entire conversation history, instructing the model to continue from where it left off.
4.  **Finalization**: Once the target length is nearly reached, a specific prompt is sent to generate a natural conclusion to the appointment.
5.  **Saving**: The full, assembled conversation is saved to a text file.

## Ethical Disclaimer

-   **Synthetic Data**: The data generated by this tool is entirely **synthetic** and does not represent real people, events, or conversations.
-   **Not for Medical Advice**: These dialogues are created for NLP research purposes and **must not be used for medical advice or diagnosis**.
-   **Model Bias**: Generative language models may perpetuate biases present in their training data. It is recommended to analyze the generated corpus for potential biases before using it in sensitive applications.

## License

This project is released under the [MIT License](LICENSE).
