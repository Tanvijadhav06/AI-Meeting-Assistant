# AI Meeting Assistant

An AI-powered application that converts meeting transcripts into structured insights and actionable outputs.

Features

- Generates meeting summaries
- Extracts action items
- Detects task priority (High / Medium / Low)
- Performs sentiment analysis
- Generates follow-up emails
- Supports chat-based queries on meeting data
- Exports meeting reports as PDF

Tech Stack

- Python
- Streamlit
- Hugging Face Transformers (FLAN-T5)
- FPDF

Run the Application

```bash
pip install -r requirements.txt
python -m streamlit run app.py