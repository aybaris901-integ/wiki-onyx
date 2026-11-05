"""Team roster + the two generated reports: offboarding handoff and onboarding plan."""

from __future__ import annotations

import csv
import logging
from pathlib import Path

from . import llm
from .answer import best_line, source_from
from .config import Settings, settings as default_settings
from .data import Chunk, Corpus
from .models import Event, Person, Source, now_iso

log = logging.getLogger("brain.roster")

HANDOFF_SYSTEM = """You write offboarding handoff reports for a software company, from the sources given.
Markdown with exactly these sections: "## What they owned", "## Open risks", "## Who takes over",
"## Runbooks", "## Things only they knew". Short bullets, concrete, name people and files. Only use facts in
the sources; if a section has no evidence, write one bullet saying what to ask the person before they go.
End with a line "Sources: S1, S3, ..." listing the ids you relied on."""

ONBOARDING_SYSTEM = """You write a three-week onboarding plan for a new engineer, from the sources given.
Markdown with sections "## Week 1: read and ask", "## Week 2: pair and ship", "## Week 3: own something".
Each week has 3-5 bullets naming the decision records, owners and code paths to look at. Only use facts in
the sources. End with a line "Sources: S1, S3, ..." listing the ids you relied on."""


class Roster:
    def __init__(self, corpus: Corpus, settings: Settings | None = None):
        self.settings = settings or default_settings
        self.corpus = corpus
        self.path: Path = self.settings.demo_data_dir / "team-roster.csv"
        # the demo marks people as left and then resets; keep the original file so reset is exact
        self._original = self.path.read_text() if self.path.exists() else None

    @property
    def people(self) -> list[Person]:
        return self.corpus.people

    def reload(self) -> None:
        if self._original is not None:
            try:
                self.path.write_text(self._original)
            except OSError as exc:
                log.warning("could not restore roster: %s", exc)
        self.corpus.people = self.corpus._load_roster()

    def find(self, handle: str) -> Person | None:
        return self.corpus.person(handle)

    def set_status(self, person: Person, status: str) -> Person:
        person.status = status
        today = now_iso()[:10]
        if status == "left":
            person.left = person.left or today
        elif status == "active":
            person.left = ""
        elif status == "new":
            person.started = person.started or today
            person.left = ""
        self._write()
        return person

    def _write(self) -> None:
        if not self.path.parent.exists():
            return
        fields = list(Person.model_fields)
        try:
            with self.path.open("w", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fields)
                writer.writeheader()
                for person in self.people:
                    writer.writerow(person.model_dump())
        except OSError as exc:
            log.warning("could not write roster: %s", exc)

    # ---------- evidence ----------

    def evidence_for(self, person: Person) -> list[Chunk]:
        docs = self.corpus.docs_for_person(person)
        handoff = self.corpus.handoff_doc(person)
        if handoff and handoff not in docs:
            docs.insert(0, handoff)
        owned = self.corpus.owned_paths(person)
        for chunk in self.corpus.chunks:
            if chunk.type == "code" and any(chunk.path.split("demo-data/acme/")[-1].startswith(p) for p in owned):
                if chunk.doc_id not in {d.doc_id for d in docs} and chunk.id.endswith("#0"):
                    docs.append(chunk)
        order = {"handoff": 0, "pr": 1, "adr": 2, "slack": 3, "meeting": 4, "issue": 5, "code": 6, "owner": 7}
        docs.sort(key=lambda c: order.get(c.type, 9))
        return docs[:18]

    def successors(self, person: Person) -> list[str]:
        """Who the handoff doc names, else the other owners of the same CODEOWNERS paths, else the manager."""
        names: list[str] = []
        handoff = self.corpus.handoff_doc(person)
        if handoff:
            full = "\n".join(c.text for c in self.corpus.chunks if c.doc_id == handoff.doc_id)
            for other in self.people:
                if other.name != person.name and other.status != "left" and other.name in full:
                    names.append(other.name)
        if not names:
            for prefix, handles in self.corpus.codeowners:
                if person.handle in handles:
                    for h in handles:
                        p = self.corpus.person(h)
                        if p and p.name != person.name and p.status != "left":
                            names.append(p.name)
        if not names and person.manager:
            names.append(self.corpus.display_name(person.manager))
        return list(dict.fromkeys(names))

    # ---------- reports ----------

    async def handoff_report(self, person: Person) -> Event:
        evidence = self.evidence_for(person)
        body, sources = None, []
        if llm.available(self.settings) and evidence:
            try:
                body, sources = await self._llm_report(HANDOFF_SYSTEM, person, evidence, f"{person.name} ({person.role}, {person.team}) left the company today. Successor candidates: {', '.join(self.successors(person)) or 'unknown'}.")
            except Exception as exc:
                log.warning("handoff llm failed: %s", exc)
        if not body:
            body, sources = self._template_handoff(person, evidence)
        return Event(type="handoff_report", title=f"Handoff report for {person.name}", body=body, person=person.name, sources=sources, severity="good")

    async def onboarding_plan(self, person: Person) -> Event:
        evidence = [c for c in self.corpus.docs.values() if c.type in ("adr", "handoff", "meeting")][:14]
        body, sources = None, []
        if llm.available(self.settings) and evidence:
            try:
                body, sources = await self._llm_report(ONBOARDING_SYSTEM, person, evidence, f"{person.name} joins as {person.role or 'engineer'} on the {person.team or 'engineering'} team, reporting to {self.corpus.display_name(person.manager) if person.manager else 'their manager'}.")
            except Exception as exc:
                log.warning("onboarding llm failed: %s", exc)
        if not body:
            body, sources = self._template_onboarding(person, evidence)
        return Event(type="onboarding_plan", title=f"Onboarding plan for {person.name}", body=body, person=person.name, sources=sources, severity="good")

    async def _llm_report(self, system: str, person: Person, evidence: list[Chunk], intro: str) -> tuple[str, list[Source]]:
        labelled = [f"[S{i}] type={c.type} title=\"{c.title}\" author={c.author} date={c.date} url={c.url}\n{c.text[:1500]}" for i, c in enumerate(evidence, 1)]
        reply = await llm.complete(system, intro + "\n\nSources:\n\n" + "\n\n".join(labelled), self.settings, max_tokens=1500)
        if not reply or "##" not in reply:
            raise llm.LLMError("report had no sections")
        import re

        ids = {int(n) for n in re.findall(r"S(\d+)", reply.rsplit("Sources:", 1)[-1])} if "Sources:" in reply else set()
        body = reply.rsplit("Sources:", 1)[0].strip() if "Sources:" in reply else reply.strip()
        picked = [evidence[i - 1] for i in sorted(ids) if 1 <= i <= len(evidence)] or evidence[:4]
        return body, [source_from(c, best_line(c, person.name)) for c in picked[:6]]

    def _template_handoff(self, person: Person, evidence: list[Chunk]) -> tuple[str, list[Source]]:
        owned = self.corpus.owned_paths(person)
        prs = self.corpus.prs_by(person)
        handoff = self.corpus.handoff_doc(person)
        threads = [c for c in evidence if c.type == "slack"]
        issues = [c for c in evidence if c.type == "issue"]
        successors = self.successors(person)
        left = f"left on {person.left}" if person.left else "is leaving"
        lines = [f"**{person.name}** ({person.role or 'engineer'}, {person.team or 'engineering'}) {left}. Generated from CODEOWNERS, pull requests, Slack and their handoff notes."]
        lines += ["", "## What they owned"]
        lines += [f"- `{p}` (CODEOWNERS)" for p in owned] or ["- Nothing in CODEOWNERS. Check git history for files they touched most."]
        lines += [f"- {pr.title} ({pr.date})" for pr in prs[:5]]
        lines += ["", "## Open risks"]
        lines += [f"- {c.title}" + (f" ({c.date})" if c.date and c.date not in c.title else "") for c in issues[:4]] or [f"- {t.title}: {best_line(t, person.name) or 'see thread'}" for t in threads[:3]] or ["- No open incidents on record. Ask them what keeps them up at night."]
        lines += ["", "## Who takes over"]
        lines += [f"- {name}" for name in successors] or ["- Nobody named yet. The manager should assign an owner this week."]
        lines += ["", "## Runbooks"]
        lines += [f"- {handoff.title}: {handoff.url}" if handoff else "- No handoff document. Record one before access is revoked."]
        lines += [f"- {c.title}" for c in evidence if c.type == "code"][:4]
        lines += ["", "## Things only they knew"]
        secrets = self._only_they_knew(person)
        lines += [f"- {s}" for s in secrets] or [f"- {best_line(t, person.name)}" for t in threads[:2] if best_line(t, person.name)] or ["- Interview them: the 2 a.m. fixes never made it into a doc."]
        sources = [source_from(c, best_line(c, person.name)) for c in evidence[:5]]
        return "\n".join(lines), sources

    def _only_they_knew(self, person: Person) -> list[str]:
        """Bullets under the handoff doc's 'things nobody else knows' style heading."""
        import re

        handoff = self.corpus.handoff_doc(person)
        if not handoff:
            return []
        for chunk in self.corpus.chunks:
            if chunk.doc_id != handoff.doc_id:
                continue
            body = chunk.text.split("\n\n", 1)[-1]
            match = re.search(r"^#+\s*(?:\d+\.\s*)?.*?(nobody else|only (?:they|i|alex|[a-z]+) kn[eo]w|tribal).*$", body, re.I | re.M)
            if not match:
                continue
            section = body[match.end():]
            section = re.split(r"^#+\s", section, maxsplit=1, flags=re.M)[0]
            bullets = [re.sub(r"\*\*", "", re.sub(r"^[-*\d.)\s]+", "", l)).strip() for l in section.splitlines() if l.strip().startswith(("-", "*")) or re.match(r"^\d+[.)]", l.strip())]
            if bullets:
                return [b[:220] for b in bullets[:5]]
        return []

    def _template_onboarding(self, person: Person, evidence: list[Chunk]) -> tuple[str, list[Source]]:
        adrs = [c for c in evidence if c.type == "adr"]
        owners = sorted({p.name for _, hs in self.corpus.codeowners for h in hs if (p := self.corpus.person(h)) and p.status != "left"})
        lines = [f"**{person.name}** joins as {person.role or 'engineer'} on {person.started or 'today'}.", "", "## Week 1: read and ask"]
        lines += [f"- Read {c.title} ({c.date}) by {c.author}" for c in adrs[:4]] or ["- Read every ADR under demo-data/docs/adr."]
        lines += [f"- Meet the owners: {', '.join(owners)}" if owners else "- Meet each CODEOWNERS owner."]
        lines += ["", "## Week 2: pair and ship", "- Pair with the payments owner on one retry-queue change.", "- Ship a small PR with a real “## Why” section.", "- Ask the brain five questions and file what it gets wrong."]
        lines += ["", "## Week 3: own something", "- Take one CODEOWNERS path with a buddy.", "- Write the ADR for the next decision you are part of."]
        return "\n".join(lines), [source_from(c, None) for c in adrs[:4]]
