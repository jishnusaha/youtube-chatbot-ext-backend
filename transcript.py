from youtube_transcript_api import YouTubeTranscriptApi


def get_transcript(video_id: str) -> str:
    transcript = YouTubeTranscriptApi().fetch(video_id)
    return " ".join([snippets.text for snippets in transcript])
