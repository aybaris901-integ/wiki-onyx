"""Loads the demo-data folder (the fake company) into Chunks the retriever and answerer work from.

Layout and front matter are defined in the repo's AGENTS.md. Everything here is plain file parsing,
so it works with no model and no network.
"""

from __future__ import annotations

import csv
import json
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote_plus

import yaml

from .config import Settings, settings as default_settings
from .models import Person

FRONT_MATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.S)
PR_TEMPLATE = re.compile(r"\{\{\s*pr:([a-z0-9][a-z0-9-]*)\s*\}\}")
CODE_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".json", ".md", ".yaml", ".yml", ".toml", ".sql", ".sh"}
CODE_CHUNK_LINES = 60

DOC_TYPES = {"slack": "slack", "meeting": "doc", "adr": "doc", "handoff": "doc", "pr": "pr", "issue": "issue"}


@dataclass
class Chunk:
    id: str
    text: str
    type: str  # slack | meeting | adr | handoff | pr | issue | code | owner
    title: str
    author: str
    date: str
    url: str
    doc_id: str
    path: str = ""
    people: list[str] = field(default_factory=list)
    lines: list[str] = field(default_factory=list)
    channel: str = ""
    pr: str = ""
    files: list[str] = field(default_factory=list)

    @property
    def source_type(self) -> str:
        """The card type the frontend understands."""
        return DOC_TYPES.get(self.type, "code" if self.type == "code" else "doc")

    def metadata(self) -> dict:
        return {
            "type": self.type,
            "title": self.title,
            "author": self.author,
            "date": self.date,
            "url": self.url,
            "doc_id": self.doc_id,
            "path": self.path,
            "people": ", ".join(self.people),
            "channel": self.channel,
            "pr": self.pr,
        }


@dataclass
class PRInfo:
    slug: str
    title: str
    author: str = ""
    date: str = ""
    number: int | None = None
    url: str | None = None
    files: list[str] = field(default_factory=list)


def parse_front_matter(text: str) -> tuple[dict, str]:
    match = FRONT_MATTER.match(text)
    if not match:
        return {}, text
    try:
        meta = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        meta = {}
    if not isinstance(meta, dict):
        meta = {}
    return meta, text[match.end():]


def _str(value) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        return ", ".join(_str(v) for v in value)
    return str(value).strip()


def _list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [part.strip() for part in re.split(r"[,;]", value) if part.strip()]
    return [_str(v) for v in value if _str(v)]


def _quotable(line: str) -> str:
    """Strip Slack speaker prefixes / list markers so a line can be shown in quotes on a card."""
    line = line.strip()
    line = re.sub(r"^\*\*[^*]+\*\*\s*(\([^)]*\))?:\s*", "", line)
    line = re.sub(r"^[-*>#]+\s*", "", line)
    return line.strip()


class Corpus:
    """Everything the agent knows about the company, loaded from disk."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or default_settings
        self.root = self.settings.demo_data_dir
        self.manifest: dict = {}
        self.prs: dict[str, PRInfo] = {}
        self.people: list[Person] = []
        self.codeowners: list[tuple[str, list[str]]] = []  # (path prefix, handles)
        self.chunks: list[Chunk] = []
        self.docs: dict[str, Chunk] = {}  # first chunk of each doc, by doc_id
        self.warnings: list[str] = []

    # ---------- loading ----------

    def load(self) -> "Corpus":
        self.manifest = self._load_manifest()
        self.prs = self._load_prs()
        self.people = self._load_roster()
        self.codeowners = self._load_codeowners()
        self.chunks = []
        self.docs = {}
        for folder in ("docs", "prs", "issues"):
            for path in sorted((self.root / folder).rglob("*.md")):
                self._add_markdown(path)
        for path in sorted((self.root / "acme").rglob("*")):
            if path.is_file() and path.suffix in CODE_SUFFIXES and path.name != "CODEOWNERS":
                self._add_code(path)
        self._add_owner_chunks()
        return self

    def mtime(self) -> float:
        latest = 0.0
        if self.root.exists():
            for path in self.root.rglob("*"):
                if path.is_file():
                    latest = max(latest, path.stat().st_mtime)
        return latest

    def _load_manifest(self) -> dict:
        path = self.root / "manifest.json"
        if not path.exists():
            self.warnings.append("manifest.json missing")
            return {}
        try:
            return json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            self.warnings.append(f"manifest.json unreadable: {exc}")
            return {}

    def _load_prs(self) -> dict[str, PRInfo]:
        prs: dict[str, PRInfo] = {}
        for slug, info in (self.manifest.get("prs") or {}).items():
            if not isinstance(info, dict):
                continue
            prs[slug] = PRInfo(
                slug=slug,
                title=_str(info.get("title")) or slug.replace("-", " "),
                author=_str(info.get("author")),
                date=_str(info.get("date")),
                number=info.get("number") if isinstance(info.get("number"), int) else None,
                url=_str(info.get("url")) or None,
                files=_list(info.get("files")),
            )
        # PR markdown files can add anything the manifest lacks.
        for path in sorted((self.root / "prs").glob("*.md")):
            meta, _ = parse_front_matter(path.read_text(errors="replace"))
            slug = _str(meta.get("pr")) or path.stem
            info = prs.setdefault(slug, PRInfo(slug=slug, title=_str(meta.get("title")) or slug))
            info.title = info.title or _str(meta.get("title"))
            info.author = info.author or _str(meta.get("author"))
            info.date = info.date or _str(meta.get("date"))
            if not info.files:
                info.files = _list(meta.get("files"))
            if info.number is None and isinstance(meta.get("number"), int):
                info.number = meta["number"]
            if not info.url:
                info.url = _str(meta.get("pr_url")) or None
        return prs

    def _load_roster(self) -> list[Person]:
        path = self.root / "team-roster.csv"
        people: list[Person] = []
        if not path.exists():
            self.warnings.append("team-roster.csv missing")
            return people
        with path.open(newline="") as handle:
            for row in csv.DictReader(handle):
                row = {k.strip().lower(): (v or "").strip() for k, v in row.items() if k}
                if not row.get("name"):
                    continue
                people.append(Person(**{k: row.get(k, "") for k in Person.model_fields}))
        return people

    def _load_codeowners(self) -> list[tuple[str, list[str]]]:
        path = self.root / "acme" / "CODEOWNERS"
        rules: list[tuple[str, list[str]]] = []
        if not path.exists():
            return rules
        for line in path.read_text().splitlines():
            line = line.split("#", 1)[0].strip()
            if not line:
                continue
            parts = line.split()
            rules.append((parts[0].lstrip("/"), [p.lstrip("@") for p in parts[1:]]))
        return rules

    # ---------- people helpers ----------

    def person(self, name_or_handle: str) -> Person | None:
        key = name_or_handle.strip().lower().lstrip("@")
        for person in self.people:
            if key in (person.name.lower(), person.handle.lower(), person.email.lower()):
                return person
        for person in self.people:  # first-name match as a last resort
            if key == person.name.split()[0].lower():
                return person
        return None

    def display_name(self, handle_or_name: str) -> str:
        person = self.person(handle_or_name)
        return person.name if person else handle_or_name.lstrip("@")

    def owners_for_path(self, repo_path: str) -> list[Person]:
        """CODEOWNERS semantics: the last matching rule wins. Paths are relative to acme/."""
        rel = repo_path.replace("\\", "/")
        rel = re.sub(r"^.*?demo-data/acme/", "", rel).strip("/")
        winner: list[str] = []
        for prefix, handles in self.codeowners:
            clean = prefix.rstrip("/")
            if prefix in ("*", "") or rel == clean or rel.startswith(clean + "/"):
                winner = handles
        people = [self.person(h) for h in winner]
        return [p for p in people if p]

    def owned_paths(self, person: Person) -> list[str]:
        return [prefix for prefix, handles in self.codeowners if person.handle in handles or person.name in handles]

    # ---------- urls ----------

    def repo_path_of(self, path: Path) -> str:
        try:
            return str(path.resolve().relative_to(self.settings.demo_data_dir.resolve().parent))
        except ValueError:
            return f"demo-data/{path.relative_to(self.root)}" if self.root in path.parents else path.name

    def pr_url(self, pr: PRInfo) -> str:
        if pr.url:
            return pr.url
        if pr.number:
            return f"https://github.com/{self.settings.repo_slug}/pull/{pr.number}"
        return f"https://github.com/{self.settings.repo_slug}/pulls?q={quote_plus(pr.title)}"

    def pr_label(self, pr: PRInfo) -> str:
        return f"PR #{pr.number}" if pr.number else f"PR “{pr.title}”"

    def render(self, text: str) -> str:
        def swap(match: re.Match) -> str:
            pr = self.prs.get(match.group(1))
            if not pr:
                self.warnings.append(f"unknown pr slug {match.group(1)}")
                return match.group(0)
            return f"{self.pr_label(pr)} ({self.pr_url(pr)})"

        return PR_TEMPLATE.sub(swap, text)

    # ---------- chunking ----------

    def _add_markdown(self, path: Path) -> None:
        raw = path.read_text(errors="replace")
        meta, body = parse_front_matter(raw)
        body = self.render(body).strip()
        doc_type = _str(meta.get("type")) or path.parent.name.rstrip("s")
        if doc_type == "meetings":
            doc_type = "meeting"
        repo_path = self.repo_path_of(path)
        doc_id = repo_path
        title = _str(meta.get("title")) or path.stem.replace("-", " ")
        author = self.display_name(_str(meta.get("author")))
        date = _str(meta.get("date"))
        url = _str(meta.get("url")) or self.settings.blob_url(repo_path)
        pr_slug = _str(meta.get("pr"))
        if doc_type == "pr":
            pr = self.prs.get(pr_slug or path.stem)
            if pr:
                pr_slug = pr.slug
                author = author or pr.author
                date = date or pr.date
                url = self.pr_url(pr) if (pr.number or pr.url) else url
        people = _list(meta.get("participants")) or ([author] if author else [])
        people = [self.display_name(p) for p in people]
        channel = _str(meta.get("channel"))
        files = _list(meta.get("files"))

        header = f"{title}\n{doc_type} by {author} on {date}" + (f" in {channel}" if channel else "")
        sections = self._split_markdown(body)
        for index, section in enumerate(sections):
            lines = [q for q in (_quotable(l) for l in section.splitlines()) if len(q) > 24]
            chunk = Chunk(
                id=f"{doc_id}#{index}",
                text=f"{header}\n\n{section}",
                type=doc_type,
                title=title,
                author=author,
                date=date,
                url=url,
                doc_id=doc_id,
                path=repo_path,
                people=people,
                lines=lines,
                channel=channel,
                pr=pr_slug,
                files=files,
            )
            self.chunks.append(chunk)
            self.docs.setdefault(doc_id, chunk)

    @staticmethod
    def _split_markdown(body: str, target: int = 1400) -> list[str]:
        """Split on headings, then pack paragraphs up to ~target characters."""
        if not body:
            return [""]
        parts = re.split(r"\n(?=##? )", body)
        sections: list[str] = []
        for part in parts:
            if len(part) <= target:
                sections.append(part.strip())
                continue
            buf = ""
            for para in re.split(r"\n\s*\n", part):
                if buf and len(buf) + len(para) > target:
                    sections.append(buf.strip())
                    buf = ""
                buf += para + "\n\n"
            if buf.strip():
                sections.append(buf.strip())
        return [s for s in sections if s] or [body]

    def _code_author(self, path: Path, repo_path: str) -> tuple[str, str, str]:
        """(author, date, pr slug) for a code file: PR files from the manifest, then CODEOWNERS, then git."""
        for pr in self.prs.values():
            for f in pr.files:
                if repo_path.endswith(f.strip("/")) or f.strip("/").endswith(str(path.relative_to(self.root))):
                    return self.display_name(pr.author), pr.date, pr.slug
        owners = self.owners_for_path(repo_path)
        if owners:
            return owners[0].name, "", ""
        try:
            out = subprocess.run(
                ["git", "log", "-1", "--format=%an|%as", "--", str(path)],
                capture_output=True, text=True, timeout=5, cwd=path.parent,
            ).stdout.strip()
            if out:
                name, _, date = out.partition("|")
                return self.display_name(name), date, ""
        except (OSError, subprocess.SubprocessError):
            pass
        return "", "", ""

    def _add_code(self, path: Path) -> None:
        repo_path = self.repo_path_of(path)
        text = path.read_text(errors="replace")
        lines = text.splitlines()
        author, date, pr_slug = self._code_author(path, repo_path)
        owners = [p.name for p in self.owners_for_path(repo_path)]
        rel = str(path.relative_to(self.root / "acme"))
        header = f"{rel}\ncode file, written by {author or 'unknown'}" + (f", owned by {', '.join(owners)}" if owners else "")
        url = self.settings.blob_url(repo_path)
        for start in range(0, max(len(lines), 1), CODE_CHUNK_LINES):
            piece = "\n".join(lines[start:start + CODE_CHUNK_LINES])
            index = start // CODE_CHUNK_LINES
            self.chunks.append(Chunk(
                id=f"{repo_path}#{index}",
                text=f"{header}\n\n{piece}",
                type="code",
                title=rel,
                author=author,
                date=date,
                url=f"{url}#L{start + 1}" if index else url,
                doc_id=repo_path,
                path=repo_path,
                people=[author] if author else [],
                lines=[],
                pr=pr_slug,
            ))
            if index == 0:
                self.docs.setdefault(repo_path, self.chunks[-1])

    def _add_owner_chunks(self) -> None:
        """One chunk per CODEOWNERS rule so 'who owns X' retrieves well even with no docs."""
        codeowners_url = self.settings.blob_url("demo-data/acme/CODEOWNERS")
        for prefix, handles in self.codeowners:
            owners = [self.person(h) for h in handles]
            owners = [p for p in owners if p]
            names = ", ".join(p.name for p in owners) or ", ".join(handles)
            status = "; ".join(f"{p.name} is {p.status}" + (f" (left {p.left})" if p.left else "") for p in owners)
            text = f"CODEOWNERS: {prefix} is owned by {names}. {status}"
            self.chunks.append(Chunk(
                id=f"codeowners#{prefix}",
                text=text,
                type="owner",
                title=f"Owner of {prefix}",
                author=owners[0].name if owners else names,
                date="",
                url=codeowners_url,
                doc_id="demo-data/acme/CODEOWNERS",
                path="demo-data/acme/CODEOWNERS",
                people=[p.name for p in owners],
                lines=[text],
            ))

    # ---------- queries used by the answerer and roster ----------

    def chunks_for_person(self, person: Person) -> list[Chunk]:
        name = person.name.lower()
        first = name.split()[0]
        found = []
        for chunk in self.chunks:
            people = [p.lower() for p in chunk.people]
            if name in people or chunk.author.lower() == name or (
                chunk.type in ("slack", "meeting") and re.search(rf"\b{re.escape(first)}\b", chunk.text, re.I)
            ):
                found.append(chunk)
        return found

    def docs_for_person(self, person: Person) -> list[Chunk]:
        seen: set[str] = set()
        out = []
        for chunk in self.chunks_for_person(person):
            if chunk.doc_id not in seen:
                seen.add(chunk.doc_id)
                out.append(self.docs.get(chunk.doc_id, chunk))
        return out

    def handoff_doc(self, person: Person) -> Chunk | None:
        first = person.name.split()[0].lower()
        for doc_id, chunk in self.docs.items():
            if chunk.type == "handoff" and (first in doc_id.lower() or chunk.author == person.name):
                return chunk
        return None

    def prs_by(self, person: Person) -> list[PRInfo]:
        return [pr for pr in self.prs.values() if self.display_name(pr.author) == person.name]
