"""
Signal — AI Video Assistant
Streamlit front-end for the meeting/video intelligence pipeline defined
in main.py (process_input -> transcribe -> summarize -> extract -> RAG chat).
"""

import os
import random
import tempfile

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarize import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question


# ─────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Signal — AI Video Assistant",
    page_icon="▍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────────────────────────────────
_defaults = {
    "page": "landing",       # "landing" | "app"
    "results": None,         # dict returned by the pipeline
    "chat_history": [],      # list of {"role": ..., "content": ...}
    "source_kind": "Upload a file",
}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


def _go(page: str):
    st.session_state.page = page


def _reset_session():
    st.session_state.results = None
    st.session_state.chat_history = []


# ─────────────────────────────────────────────────────────────────────────
# Styling — "broadcast / editing suite" identity
#   bg: near-black, text: warm off-white, accent: signal green + amber,
#   display face: Space Grotesk, body: Inter, technical/mono: JetBrains Mono
# ─────────────────────────────────────────────────────────────────────────
def inject_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

        :root{
            --bg:#0B0D0F; --panel:#14171A; --panel-2:#191C1F; --border:#242830;
            --text:#EDEDE5; --muted:#8A93A0; --signal:#4ADE80; --amber:#F5A623; --slate:#5B6470;
        }

        html, body, [class*="css"], .stMarkdown, p, span, div { font-family:'Inter',sans-serif; }
        .stApp{ background:var(--bg); color:var(--text); }
        #MainMenu, header[data-testid="stHeader"], footer{ visibility:hidden; height:0; }
        .block-container{ padding-top:2rem; max-width:1180px; }

        h1,h2,h3,h4{ font-family:'Space Grotesk',sans-serif; letter-spacing:-0.01em; color:var(--text); }
        code, .mono{ font-family:'JetBrains Mono',monospace; }

        /* ---------- generic buttons ---------- */
        .stButton>button{
            background:var(--panel-2); color:var(--text); border:1px solid var(--border);
            border-radius:8px; padding:0.55rem 1.3rem; font-weight:600; font-family:'Space Grotesk',sans-serif;
            transition:all .15s ease;
        }
        .stButton>button:hover{ border-color:var(--signal); color:var(--signal); }
        .stButton>button:active{ transform:scale(0.98); }

        /* CTA (first button rendered on landing) */
        div[data-testid="stVerticalBlockBorderWrapper"] .stButton>button{ }

        /* ---------- inputs ---------- */
        .stTextInput input, .stSelectbox div[data-baseweb="select"]>div, .stTextArea textarea{
            background:var(--panel) !important; color:var(--text) !important; border:1px solid var(--border) !important;
            border-radius:8px !important; font-family:'JetBrains Mono',monospace !important;
        }
        .stRadio label{ color:var(--text); }
        [data-testid="stFileUploaderDropzone"]{
            background:var(--panel); border:1px dashed var(--border); border-radius:10px;
        }

        /* ---------- tabs ---------- */
        .stTabs [data-baseweb="tab-list"]{ gap:4px; border-bottom:1px solid var(--border); }
        .stTabs [data-baseweb="tab"]{
            background:transparent; color:var(--muted); font-family:'Space Grotesk',sans-serif;
            font-weight:600; padding:10px 18px; border-radius:8px 8px 0 0;
        }
        .stTabs [aria-selected="true"]{ color:var(--signal) !important; border-bottom:2px solid var(--signal); }

        /* ---------- status / spinner ---------- */
        [data-testid="stStatusWidget"], .stStatus{ background:var(--panel) !important; border:1px solid var(--border) !important; border-radius:10px !important; }

        /* ---------- landing hero ---------- */
        .hero-wrap{ text-align:center; padding:2.2rem 0 1rem 0; }
        .eyebrow{
            display:inline-flex; align-items:center; gap:8px; color:var(--signal); font-family:'JetBrains Mono',monospace;
            font-size:0.78rem; letter-spacing:0.12em; text-transform:uppercase; border:1px solid var(--border);
            padding:6px 14px; border-radius:999px; background:var(--panel);
        }
        .dot{ width:7px; height:7px; border-radius:50%; background:var(--signal); box-shadow:0 0 8px var(--signal); animation:blink 1.4s ease-in-out infinite; }
        @keyframes blink{ 0%,100%{opacity:1;} 50%{opacity:0.25;} }

        .hero-title{ font-size:3.4rem; line-height:1.08; margin:1.1rem auto 0.9rem auto; max-width:820px; }
        .hero-title .grad{ background:linear-gradient(90deg,var(--signal),#8CF0AE); -webkit-background-clip:text; background-clip:text; color:transparent; }
        .hero-sub{ color:var(--muted); font-size:1.08rem; max-width:600px; margin:0 auto 1.8rem auto; line-height:1.55; }

        /* waveform */
        .waveform{ display:flex; align-items:flex-end; justify-content:center; gap:4px; height:80px; margin:0 auto 2.2rem auto; max-width:640px; }
        .waveform span{
            display:block; width:4px; border-radius:3px; background:linear-gradient(180deg,var(--signal),rgba(74,222,128,0.15));
            height:var(--h); animation:pulse ease-in-out infinite alternate;
        }
        @keyframes pulse{ from{ transform:scaleY(0.35); opacity:0.55;} to{ transform:scaleY(1); opacity:1;} }

        /* feature cards */
        .feat-card{
            background:var(--panel); border:1px solid var(--border); border-radius:14px; padding:1.4rem 1.3rem;
            height:100%; transition:border-color .15s ease;
        }
        .feat-card:hover{ border-color:var(--signal); }
        .feat-num{ font-family:'JetBrains Mono',monospace; color:var(--signal); font-size:0.8rem; }
        .feat-title{ font-family:'Space Grotesk',sans-serif; font-weight:600; font-size:1.05rem; margin:0.5rem 0 0.4rem 0; }
        .feat-body{ color:var(--muted); font-size:0.92rem; line-height:1.5; }

        /* app header */
        .app-header{ display:flex; align-items:center; justify-content:space-between; padding-bottom:1rem; border-bottom:1px solid var(--border); margin-bottom:1.4rem; }
        .brand{ display:flex; align-items:center; gap:10px; font-family:'Space Grotesk',sans-serif; font-weight:700; font-size:1.15rem; }
        .rec{ width:8px; height:8px; border-radius:50%; background:#ff5c5c; box-shadow:0 0 8px #ff5c5c; animation:blink 1.2s infinite; }

        /* stat chips */
        .chip-row{ display:flex; gap:12px; flex-wrap:wrap; margin-bottom:1.2rem; }
        .chip{ background:var(--panel); border:1px solid var(--border); border-radius:10px; padding:0.8rem 1.1rem; min-width:140px; }
        .chip .label{ color:var(--muted); font-size:0.75rem; text-transform:uppercase; letter-spacing:0.08em; font-family:'JetBrains Mono',monospace; }
        .chip .value{ font-family:'Space Grotesk',sans-serif; font-weight:700; font-size:1.3rem; margin-top:2px; }

        .panel-block{ background:var(--panel); border:1px solid var(--border); border-radius:12px; padding:1.4rem 1.5rem; margin-bottom:1rem; }

        /* chat bubbles */
        [data-testid="stChatMessage"]{ background:var(--panel); border:1px solid var(--border); border-radius:12px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def waveform_html(n: int = 56) -> str:
    random.seed(11)
    bars = []
    for _ in range(n):
        h = random.randint(18, 100)
        delay = round(random.uniform(0, 1.2), 2)
        dur = round(random.uniform(0.7, 1.5), 2)
        bars.append(f'<span style="--h:{h}%; animation-delay:{delay}s; animation-duration:{dur}s;"></span>')
    return f'<div class="waveform">{"".join(bars)}</div>'


# ─────────────────────────────────────────────────────────────────────────
# Landing page
# ─────────────────────────────────────────────────────────────────────────
def render_landing():
    st.markdown('<div class="hero-wrap">', unsafe_allow_html=True)
    st.markdown(
        '<span class="eyebrow"><span class="dot"></span> AI Video Assistant</span>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<h1 class="hero-title">Turn any recording into a<br><span class="grad">meeting you can search.</span></h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="hero-sub">Drop in a video, audio file, or URL. Signal transcribes it, '
        'pulls out the summary, decisions, and action items, then lets you chat '
        'with the whole recording like it\'s a document.</p>',
        unsafe_allow_html=True,
    )
    st.markdown(waveform_html(), unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    col_l, col_c, col_r = st.columns([1, 0.7, 1])
    with col_c:
        if st.button("▸  Try now", use_container_width=True, key="cta_try_now"):
            _go("app")
            st.rerun()

    st.write("")
    st.write("")

    features = [
        ("01", "Transcribe", "Any source, any length. Audio and video are chunked and "
         "transcribed with language selection built in."),
        ("02", "Understand", "A title, summary, key decisions, action items, and open "
         "questions are pulled out automatically."),
        ("03", "Interrogate", "Ask the recording anything. A RAG chain built on the full "
         "transcript answers with grounded context."),
    ]
    cols = st.columns(3)
    for col, (num, title, body) in zip(cols, features):
        with col:
            st.markdown(
                f'<div class="feat-card"><div class="feat-num">{num}</div>'
                f'<div class="feat-title">{title}</div>'
                f'<div class="feat-body">{body}</div></div>',
                unsafe_allow_html=True,
            )


# ─────────────────────────────────────────────────────────────────────────
# Pipeline runner with staged progress in the UI
# ─────────────────────────────────────────────────────────────────────────
def run_pipeline_with_progress(source: str, language: str) -> dict:
    with st.status("Processing recording…", expanded=True) as status:
        st.write("Reading and chunking input…")
        chunks = process_input(source)

        st.write(f"Transcribing ({language})…")
        transcript = transcribe_all(chunks, language=language)

        st.write("Generating title…")
        title = generate_title(transcript)

        st.write("Summarizing…")
        summary = summarize(transcript)

        st.write("Extracting action items…")
        action_items = extract_action_items(transcript)

        st.write("Extracting key decisions…")
        decisions = extract_key_decisions(transcript)

        st.write("Extracting open questions…")
        questions = extract_questions(transcript)

        st.write("Building chat index…")
        rag_chain = build_rag_chain(transcript)

        status.update(label="Done — recording processed.", state="complete", expanded=False)

    return {
        "title": title,
        "transcript": transcript,
        "summary": summary,
        "action_items": action_items,
        "key_decisions": decisions,
        "open_questions": questions,
        "rag_chain": rag_chain,
    }


# ─────────────────────────────────────────────────────────────────────────
# App page
# ─────────────────────────────────────────────────────────────────────────
def render_intake_form():
    st.markdown('<div class="panel-block">', unsafe_allow_html=True)
    st.markdown("#### New session")
    st.session_state.source_kind = st.radio(
        "Source", ["Upload a file", "Paste a URL"],
        index=0 if st.session_state.source_kind == "Upload a file" else 1,
        horizontal=True, label_visibility="collapsed",
    )

    source_path = None
    if st.session_state.source_kind == "Upload a file":
        uploaded = st.file_uploader(
            "Drop an audio or video file", type=["mp3", "wav", "m4a", "mp4", "mov", "mkv"]
        )
        if uploaded is not None:
            tmp_dir = tempfile.mkdtemp()
            source_path = os.path.join(tmp_dir, uploaded.name)
            with open(source_path, "wb") as f:
                f.write(uploaded.getbuffer())
    else:
        source_path = st.text_input("Video/audio URL", placeholder="https://…")

    language = st.selectbox(
        "Language", ["english", "hindi", "spanish", "french", "german", "japanese"], index=0
    )

    start = st.button("Start analysis", type="primary")
    st.markdown("</div>", unsafe_allow_html=True)

    if start:
        if not source_path:
            st.error("Add a file or a URL first.")
            return
        try:
            st.session_state.results = run_pipeline_with_progress(source_path, language)
            st.session_state.chat_history = []
            st.rerun()
        except Exception as e:
            st.error(f"Something went wrong while processing: {e}")


def _count_items(value) -> int:
    if not value:
        return 0
    if isinstance(value, (list, tuple)):
        return len(value)
    if isinstance(value, str):
        val_lower = value.lower().strip()
        if any(neg in val_lower for neg in [
            "no action items found", 
            "no key decisions found", 
            "no open questions found"
        ]):
            return 0
        
        lines = [line.strip() for line in value.split("\n") if line.strip()]
        
        # Count lines starting with a number followed by a dot or parenthesis, e.g. "1.", "1)"
        import re
        numbered_items = [
            line for line in lines 
            if re.match(r'^\d+[\.\)]', line)
        ]
        
        if numbered_items:
            return len(numbered_items)
            
        # If no numbered list, count basic bullet points
        bullets = [
            line for line in lines 
            if line.startswith(("-", "*", "•"))
        ]
        if bullets:
            return len(bullets)
            
        return 1 if lines else 0
    return 1


def render_results():
    r = st.session_state.results

    st.markdown(f"### {r['title']}")

    wc = len(r["transcript"].split())
    ac = _count_items(r["action_items"])
    dc = _count_items(r["key_decisions"])
    qc = _count_items(r["open_questions"])

    st.markdown(
        f'<div class="chip-row">'
        f'<div class="chip"><div class="label">Transcript</div><div class="value">{wc} words</div></div>'
        f'<div class="chip"><div class="label">Action items</div><div class="value">{ac}</div></div>'
        f'<div class="chip"><div class="label">Decisions</div><div class="value">{dc}</div></div>'
        f'<div class="chip"><div class="label">Open questions</div><div class="value">{qc}</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    tabs = st.tabs(["Summary", "Action items", "Decisions", "Questions", "Transcript", "Chat"])

    with tabs[0]:
        st.markdown('<div class="panel-block">', unsafe_allow_html=True)
        st.write(r["summary"])
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[1]:
        st.markdown('<div class="panel-block">', unsafe_allow_html=True)
        _render_listish(r["action_items"])
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[2]:
        st.markdown('<div class="panel-block">', unsafe_allow_html=True)
        _render_listish(r["key_decisions"])
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[3]:
        st.markdown('<div class="panel-block">', unsafe_allow_html=True)
        _render_listish(r["open_questions"])
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[4]:
        st.markdown('<div class="panel-block mono">', unsafe_allow_html=True)
        st.text_area("Full transcript", r["transcript"], height=420, label_visibility="collapsed")
        st.markdown("</div>", unsafe_allow_html=True)

    with tabs[5]:
        render_chat(r["rag_chain"])

    st.write("")
    if st.button("↺  Analyze another recording"):
        _reset_session()
        st.rerun()


def _render_listish(value):
    if isinstance(value, (list, tuple)):
        for item in value:
            st.markdown(f"- {item}")
    else:
        st.write(value)


def render_chat(rag_chain):
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    question = st.chat_input("Ask this recording something…")
    if question:
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)
        with st.chat_message("assistant"):
            with st.spinner("Thinking…"):
                answer = ask_question(rag_chain, question)
            st.write(answer)
        st.session_state.chat_history.append({"role": "assistant", "content": answer})


def render_app():
    st.markdown(
        '<div class="app-header">'
        '<div class="brand"><span class="rec"></span> Signal</div>'
        "</div>",
        unsafe_allow_html=True,
    )
    top_l, top_r = st.columns([5, 1])
    with top_r:
        if st.button("← Home"):
            _go("landing")
            st.rerun()

    if st.session_state.results is None:
        render_intake_form()
    else:
        render_results()


# ─────────────────────────────────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────────────────────────────────
inject_css()

if st.session_state.page == "landing":
    render_landing()
else:
    render_app()