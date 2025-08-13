# app.py
import streamlit as st
from urllib.parse import urlparse, parse_qs
from project1 import graph

st.set_page_config(page_title="YouTube → Blog", page_icon="📝", layout="wide")
st.title("📝 YouTube → SEO Blog (n8n/LangGraph Demo)")

def extract_video_id(value: str) -> str:
    """
    Accepts a full YouTube URL or a raw ID and returns the video id.
    Handles: youtube.com/watch?v=..., youtu.be/..., /shorts/..., /embed/...
    """
    if not value:
        return value
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()

    if "youtube" in host or "youtu.be" in host:
        # youtu.be/<id>
        if "youtu.be" in host:
            return parsed.path.lstrip("/")
        # youtube.com/watch?v=...
        qs = parse_qs(parsed.query)
        if "v" in qs:
            return qs["v"][0]
        # youtube.com/shorts/<id> or /embed/<id>
        parts = [p for p in parsed.path.split("/") if p]
        if "shorts" in parts:
            return parts[parts.index("shorts") + 1]
        if "embed" in parts:
            return parts[parts.index("embed") + 1]
        # fallback – if nothing matched, return as-is (maybe it was an ID)
        return value
    # looks like a raw id
    return value

url_or_id = st.text_input("Paste a YouTube URL (or raw video ID):", placeholder="https://www.youtube.com/watch?v=dQw4w9WgXcQ")

go = st.button("Generate Blog", type="primary")

# Output placeholders
status = st.empty()
col1, col2 = st.columns([1, 1])
with col1:
    toc_box = st.container()
    blog_box = st.container()
with col2:
    summary_box = st.container()
    # debug_box = st.expander("Debug stream", expanded=False)

if go and url_or_id:
    vid = extract_video_id(url_or_id)
    status.info("Fetching transcript…")

    # Stream LangGraph updates
    final_state = {}
    for update in graph.stream({"video_id": vid}):

        node_name, node_payload = next(iter(update.items()))

        # Handle early stop on transcript failure
        if node_name == "transcription" and node_payload.get("disabled"):
            status.error(node_payload.get("error", "Transcript unavailable."))
            break

        # Pretty live updates
        if "full_transcript" in node_payload:
            status.success("Transcript fetched ✅")

        if "table_of_contents" in node_payload:
            with toc_box:
                st.subheader("Table of Contents")
                st.markdown("\n".join([f"- {h}" for h in node_payload["table_of_contents"]]))

        if "blog" in node_payload:
            with blog_box:
                st.subheader("Draft Blog")
                st.markdown(node_payload["blog"])

        if "summary" in node_payload:
            with summary_box:
                st.subheader("SEO Title & Summary")
                st.markdown(node_payload["summary"])

        # keep merging to show final result if needed
        final_state.update(node_payload)
