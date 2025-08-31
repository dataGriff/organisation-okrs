import glob, os
import frontmatter
from markdown_it import MarkdownIt

def load_markdown_docs(okr_dir: str):
    """
    Walk okr_dir and yield (path, metadata, text) for each .md file.
    Text is a plain-text rendering of the Markdown body.
    """
    md = MarkdownIt()
    docs = []
    for path in glob.glob(os.path.join(okr_dir, "**/*.md"), recursive=True):
        if not path.lower().endswith(".md"):
            continue
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
        post = frontmatter.loads(raw)
        text = md.render(post.content)
        docs.append({
            "path": os.path.relpath(path, okr_dir).replace("\\", "/"),
            "abs_path": os.path.abspath(path),
            "meta": post.metadata or {},
            "text": text
        })
    return docs
