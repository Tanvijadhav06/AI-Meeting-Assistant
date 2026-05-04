import streamlit as st
from transformers import pipeline
from fpdf import FPDF
import tempfile
import re

st.set_page_config(page_title="AI Meeting Assistant", layout="wide")

# ---------- UI ----------
st.markdown("""
<style>
html, body {
    background-color: #EAF3FF;
    font-family: 'Inter', sans-serif;
}
.card {
    background: white;
    padding: 20px;
    border-radius: 16px;
    border-left: 5px solid #3B82F6;
    margin-bottom: 20px;
}
.tag-high {background:#EF4444;color:white;padding:4px 10px;border-radius:8px;}
.tag-medium {background:#F59E0B;color:white;padding:4px 10px;border-radius:8px;}
.tag-low {background:#10B981;color:white;padding:4px 10px;border-radius:8px;}
.user {background:#2563EB;color:white;padding:10px;border-radius:10px;text-align:right;margin:5px;}
.ai {background:#DBEAFE;padding:10px;border-radius:10px;margin:5px;}
.highlight {background:#FEF3C7;padding:8px;border-radius:10px;margin-top:5px;}
</style>
""", unsafe_allow_html=True)

st.title("AI Meeting Assistant")

# ---------- MODELS ----------
@st.cache_resource
def load_models():
    model = pipeline("text2text-generation", model="google/flan-t5-base")
    sentiment = pipeline("sentiment-analysis")
    return model, sentiment

model, sentiment_model = load_models()

# ---------- SESSION ----------
if "chat" not in st.session_state:
    st.session_state.chat = []

# ---------- FUNCTIONS ----------
def clean_text(text):
    return text.replace("→", "-")

def summarize(text):
    prompt = f"Summarize the following meeting clearly with tasks:\n{text}"
    res = model(prompt, max_length=150, do_sample=False)
    return res[0]["generated_text"]

def extract_tasks(text):
    tasks = []
    for line in text.split("\n"):
        if ":" in line:
            name, task = line.split(":", 1)
            tasks.append(f"{name.strip()} - {task.strip()}")
    return tasks

def detect_priority(task):
    t = task.lower()
    if any(k in t for k in ["urgent","critical","blocker"]):
        return "high"
    elif any(k in t for k in ["pending","important","delay","priority"]):
        return "medium"
    return "low"

def highlight_line(text, question):
    words = re.findall(r"\w+", question.lower())
    for line in text.split("\n"):
        if any(w in line.lower() for w in words):
            return line
    return ""

def chat_answer(text, q):
    prompt = f"Answer based only on the meeting:\n{text}\nQuestion:{q}"
    res = model(prompt, max_length=120, do_sample=False)
    return res[0]["generated_text"]

def create_pdf(summary, tasks, sentiment, email):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.multi_cell(0, 10, f"Summary:\n{summary}\n")
    pdf.multi_cell(0, 10, "Tasks:")
    for t in tasks:
        pdf.multi_cell(0, 8, f"- {t}")

    pdf.multi_cell(0, 10, f"\nSentiment: {sentiment}")
    pdf.multi_cell(0, 10, "\nEmail:")
    pdf.multi_cell(0, 8, email)

    file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf.output(file.name)
    return file.name

# ---------- INPUT ----------
st.markdown('<div class="card">', unsafe_allow_html=True)
transcript = st.text_area("Paste Meeting Transcript", height=200)
st.markdown('</div>', unsafe_allow_html=True)

# ---------- MAIN ----------
if st.button("Generate Insights"):

    summary = clean_text(summarize(transcript))
    tasks = [clean_text(t) for t in extract_tasks(transcript)]
    sentiment = sentiment_model(summary[:512])[0]["label"]

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Summary")
        st.write(summary)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Action Items")

        for t in tasks:
            level = detect_priority(t)
            tag = f'<span class="tag-{level}">{level.upper()}</span>'
            st.markdown(f"{tag} {t}", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Sentiment")
    st.write(sentiment)
    st.markdown('</div>', unsafe_allow_html=True)

    # ---------- EMAIL ----------
    email = f"""
Subject: Meeting Summary

Hi Team,

{summary}

Action Items:
{chr(10).join(tasks)}

Thanks,
Team
"""

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("Follow-up Email")
    st.text_area("", email, height=200)

    pdf_path = create_pdf(summary, tasks, sentiment, email)

    with open(pdf_path, "rb") as f:
        st.download_button("Download PDF", f, "report.pdf")

    st.markdown('</div>', unsafe_allow_html=True)

# ---------- CHAT ----------
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("Chat with Meeting")

for msg in st.session_state.chat:
    if msg["role"] == "user":
        st.markdown(f'<div class="user">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="ai">{msg["content"]}</div>', unsafe_allow_html=True)
        if msg.get("highlight"):
            st.markdown(f'<div class="highlight">{msg["highlight"]}</div>', unsafe_allow_html=True)

q = st.text_input("Ask question")

col1, col2 = st.columns(2)

with col1:
    if st.button("Send"):
        if q.strip():
            ans = chat_answer(transcript, q)
            hl = highlight_line(transcript, q)

            st.session_state.chat.append({"role":"user","content":q})
            st.session_state.chat.append({"role":"ai","content":ans,"highlight":hl})

            st.rerun()

with col2:
    if st.button("Clear Chat"):
        st.session_state.chat = []
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)