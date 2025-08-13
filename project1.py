from youtube_transcript_api import YouTubeTranscriptApi , TranscriptsDisabled
from langgraph.graph import StateGraph , END 
from typing import TypedDict
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from dotenv import load_dotenv  
load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0, max_tokens=1000)



class Content(BaseModel):
    table_of_contents: list[str]

class Full(TypedDict):
  text: str
  video_id: str
  summary: str
  table_of_contents: list[str]
  full_transcript: str
  blog: str
  disabled: bool

# transcription node
def transcription(state: Full):
  video_id=state["video_id"]
  try:
   transcript=YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
   new_transcript = [value["text"] for value in transcript]
   new_transcript = " ".join(new_transcript)
   return {
     'disabled': False,
     'full_transcript': new_transcript
   }
  except TranscriptsDisabled:
   print("Transcript is disabled")
   return {'disabled':True}
  
# create table of content
def create_content(state: Full):
  prompt = f"""
  You are a professional blog writer from the transcript of the youtube video. Create a table of contents to write the blog on for the following transcript:

  {state["full_transcript"]}

  Table of Contents:
  """

  response = llm.with_structured_output(Content).invoke(prompt)

  return {"table_of_contents": response.table_of_contents}

# def write blog 
def write_blog(state: Full):
  prompt = f"""
  Don't use any persona name from the video transcription it should reflect the person self learning experience about that.
  You are a blog writer. Write a blog on the following transcript of the youtube video. Use the table of contents to write the blog.

  {state["full_transcript"]}

  Table of Contents:
  {" ".join(state["table_of_contents"])}

  Blog:
  """

  response = llm.invoke(prompt)
  
  return {"blog": response.content}


def summarize(state: Full):
  prompt = f"""
  Don't use any persona name from the video transcription it should reflect the person self learning experience about that.
  You are a summarizer. Write summary of the blog Post and a perfect seo friendly title for it.
  Blog:
  {state["blog"]}

  Summary:
  """

  response = llm.invoke(prompt)

  return {"summary": response.content}

def check_transcript_disabled(state: Full):
  if state["disabled"]:
    print("Transcript is disabled")
    return "END"
  return "GO"


builder = StateGraph(Full)
builder.add_node("transcription", transcription)
builder.add_node("create_content", create_content)
builder.add_node("write_blog", write_blog)
builder.add_node("summarize", summarize)


builder.add_conditional_edges("transcription", check_transcript_disabled , {
    "END": END,
    "GO": "create_content"
})

builder.add_edge("create_content", "write_blog")
builder.add_edge("write_blog", "summarize")
builder.add_edge("summarize", END)

builder.set_entry_point("transcription")

graph=builder.compile()

