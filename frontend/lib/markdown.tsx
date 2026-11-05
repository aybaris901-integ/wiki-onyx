import { Fragment, type ReactNode } from "react";

// A tiny markdown renderer for the agent's reports: headings, bullets, numbered lists,
// paragraphs, **bold**, `code` and [links](https://...). Everything is text, never HTML,
// and only http(s) links are made clickable.

function safeHref(raw: string): string | null {
  try {
    const url = new URL(raw);
    return url.protocol === "http:" || url.protocol === "https:" ? url.href : null;
  } catch {
    return null;
  }
}

const INLINE = /(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)\s]+\))/g;

function inline(text: string): ReactNode[] {
  return text.split(INLINE).map((part, index) => {
    if (!part) return null;
    if (part.startsWith("**") && part.endsWith("**")) return <strong key={index}>{part.slice(2, -2)}</strong>;
    if (part.startsWith("`") && part.endsWith("`")) return <code key={index}>{part.slice(1, -1)}</code>;
    const link = part.match(/^\[([^\]]+)\]\(([^)\s]+)\)$/);
    if (link) {
      const href = safeHref(link[2]);
      return href ? (
        <a key={index} href={href} target="_blank" rel="noopener noreferrer">
          {link[1]}
        </a>
      ) : (
        <Fragment key={index}>{link[1]}</Fragment>
      );
    }
    return <Fragment key={index}>{part}</Fragment>;
  });
}

type Block =
  | { kind: "heading"; level: number; text: string }
  | { kind: "list"; ordered: boolean; items: string[] }
  | { kind: "paragraph"; text: string };

function blocks(markdown: string): Block[] {
  const out: Block[] = [];
  let paragraph: string[] = [];
  const flush = () => {
    if (paragraph.length) out.push({ kind: "paragraph", text: paragraph.join(" ") });
    paragraph = [];
  };

  for (const raw of markdown.split(/\r?\n/)) {
    const line = raw.trimEnd();
    const heading = line.match(/^(#{1,6})\s+(.*)$/);
    const bullet = line.match(/^\s*[-*]\s+(.*)$/);
    const number = line.match(/^\s*\d+[.)]\s+(.*)$/);
    if (!line.trim()) {
      flush();
    } else if (heading) {
      flush();
      out.push({ kind: "heading", level: heading[1].length, text: heading[2] });
    } else if (bullet || number) {
      flush();
      const ordered = Boolean(number);
      const item = (bullet ?? number)![1];
      const last = out[out.length - 1];
      if (last?.kind === "list" && last.ordered === ordered) last.items.push(item);
      else out.push({ kind: "list", ordered, items: [item] });
    } else {
      paragraph.push(line.trim());
    }
  }
  flush();
  return out;
}

export function Markdown({ text, className }: { text: string; className?: string }) {
  if (!text.trim()) return null;
  return (
    <div className={className}>
      {blocks(text).map((block, index) => {
        if (block.kind === "heading") {
          const Tag = (`h${Math.min(6, block.level + 2)}` as "h3" | "h4" | "h5" | "h6");
          return <Tag key={index}>{inline(block.text)}</Tag>;
        }
        if (block.kind === "list") {
          const Tag = block.ordered ? "ol" : "ul";
          return (
            <Tag key={index}>
              {block.items.map((item, i) => (
                <li key={i}>{inline(item)}</li>
              ))}
            </Tag>
          );
        }
        return <p key={index}>{inline(block.text)}</p>;
      })}
    </div>
  );
}
