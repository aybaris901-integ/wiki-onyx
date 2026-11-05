import type { CSSProperties } from "react";
import type { Source } from "@/lib/answer";

// Source cards: one per place the answer came from, color-coded by kind.
// Used full-size under an answer and compact inside event cards.

export type Kind = "pr" | "commit" | "thread" | "code" | "doc" | "owner" | "other";

export function kindOf(type: string): Kind {
  const name = type.toLowerCase();
  if (name.includes("commit")) return "commit";
  if (name === "pr" || name.includes("pull")) return "pr";
  if (/slack|thread|discussion|message|chat/.test(name)) return "thread";
  if (/owner|person/.test(name)) return "owner";
  if (/code|file|blob/.test(name)) return "code";
  if (/doc|wiki|notion|confluence|page|adr|meeting|handoff/.test(name)) return "doc";
  return "other";
}

export const LOOK: Record<Kind, { label: string; tone: string }> = {
  thread: { label: "Discussed in", tone: "leaf" },
  pr: { label: "Written in", tone: "cobalt" },
  commit: { label: "Changed in", tone: "cobalt" },
  code: { label: "Lives in", tone: "ink" },
  doc: { label: "Written down in", tone: "sky" },
  owner: { label: "Owned by", tone: "coral" },
  other: { label: "Source", tone: "sky" },
};

export function titleFor(kind: Kind, source: Source): string {
  if (kind === "owner") return source.author || "Owner not named";
  if (source.title) return source.title;
  const url = source.url;
  if (kind === "pr") {
    const number = url.match(/\/pulls?\/(\d+)/)?.[1];
    return number ? `Pull request #${number}` : "Pull request";
  }
  if (kind === "commit") {
    const sha = url.match(/\/commits?\/([0-9a-f]{7})/i)?.[1];
    return sha ? `Commit ${sha}` : "Commit";
  }
  if (kind === "thread") return /slack/i.test(`${source.type} ${url}`) ? "Slack thread" : "Discussion";
  const last = url.split("?")[0].split("/").filter(Boolean).at(-1) ?? "";
  if (kind === "code") return last ? decodeURIComponent(last) : "Code";
  if (kind === "doc" && last) {
    const words = decodeURIComponent(last).replace(/\.md$/i, "").replace(/[-_]+/g, " ");
    return words.charAt(0).toUpperCase() + words.slice(1);
  }
  return kind === "doc" ? "Document" : "Link";
}

export function readableDate(date: string): string {
  if (!date) return "";
  const parsed = new Date(date);
  if (Number.isNaN(parsed.getTime())) return date;
  return parsed.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    timeZone: "UTC",
  });
}

// Reads as a story: oldest first, with whoever owns it now at the end.
export function inStoryOrder(sources: Source[]): Source[] {
  const time = (source: Source) => {
    const value = new Date(source.date).getTime();
    return Number.isNaN(value) ? Infinity : value;
  };
  return [...sources].sort((a, b) => {
    const ownerGap = Number(kindOf(a.type) === "owner") - Number(kindOf(b.type) === "owner");
    return ownerGap || time(a) - time(b);
  });
}

export function SourceCard({
  source,
  index,
  compact = false,
}: {
  source: Source;
  index: number;
  compact?: boolean;
}) {
  const kind = kindOf(source.type);
  const { label, tone } = LOOK[kind];
  const date = readableDate(source.date);
  const who = kind === "owner" ? "Current owner" : source.author || "Author not named";
  const style = { "--i": index, "--r": `${index % 2 ? 7 : -7}deg` } as CSSProperties;
  const body = (
    <>
      <span className="ap-src-kind">{label}</span>
      <strong className="ap-src-title">{titleFor(kind, source)}</strong>
      {!compact && source.quote && <span className="ap-src-quote">&ldquo;{source.quote}&rdquo;</span>}
      <span className="ap-src-who">{who}</span>
      {date && <time className="ap-src-when">{date}</time>}
    </>
  );
  const className = `ap-src tone-${tone}${compact ? " ap-src-compact" : ""}`;

  return (
    <li className={compact ? "ap-src-item ap-src-item-compact" : "ap-src-item"} style={style}>
      {source.url ? (
        <a className={className} href={source.url} target="_blank" rel="noopener noreferrer">
          {body}
        </a>
      ) : (
        <div className={className}>{body}</div>
      )}
    </li>
  );
}
