"use client";

import { useLayoutEffect, useRef } from "react";
import Link from "next/link";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

const QUESTION = "Why do payments go through a queue?";
const ANSWER =
  "Charging cards directly double charged customers when the provider timed out. Maya moved charges into a retry queue, and Priya owns it now.";

const SOURCES = [
  { kind: "Discussed in", title: "Slack thread", who: "Tomas Ruiz", when: "Nov 17, 2025", tone: "leaf" },
  { kind: "Written in", title: "Pull request #482", who: "Maya Okafor", when: "Nov 19, 2025", tone: "cobalt" },
  { kind: "Lives in", title: "retry_queue.ts", who: "Maya Okafor", when: "Nov 19, 2025", tone: "ink" },
  { kind: "Owned by", title: "Priya Raman", who: "Current owner", when: "Mar 2, 2026", tone: "coral" },
];

const CHAT = [
  { from: "new", text: "Why do payments go through a queue?" },
  { from: "boss", text: "No idea. I've only been here three months." },
  { from: "new", text: "Who would know?" },
  { from: "boss", text: "Tomas. He left in March." },
];

const FOUR = [
  { big: "Who wrote it", tone: "cobalt", line: "The person behind the code, pulled from every commit and pull request." },
  { big: "Why they did it", tone: "coral", line: "The actual reason, in the words of the people who made the call." },
  { big: "Where it was discussed", tone: "leaf", line: "A direct link to the thread where the decision happened." },
  { big: "Who owns it now", tone: "ink", line: "The right person to ask today, even after the author has left." },
];

function PanelProof({ index }: { index: number }) {
  if (index === 0) {
    return (
      <div className="proof">
        <img className="proof-logo" src="/logos/github.svg" alt="GitHub" width={26} height={26} />
        <strong className="proof-title">Move charges into a retry queue</strong>
        <span className="proof-meta">Maya Okafor merged pull request #482 on Nov 19, 2025</span>
      </div>
    );
  }
  if (index === 1) {
    return (
      <blockquote className="proof proof-quote">
        <p>&ldquo;Retrying inline is what double charged 212 orders last week.&rdquo;</p>
        <span className="proof-meta">Maya Okafor, in pull request #482</span>
      </blockquote>
    );
  }
  if (index === 2) {
    return (
      <div className="proof">
        <strong className="proof-head">Slack, #payments</strong>
        <p className="proof-msg">
          <b>Tomas Ruiz</b> If the provider times out and we retry, we charge them again.
        </p>
        <p className="proof-msg">
          <b>Maya Okafor</b> It has to be a queue. I&apos;ll take it.
        </p>
      </div>
    );
  }
  return (
    <div className="proof">
      <strong className="proof-owner">Priya Raman</strong>
      <span className="proof-meta">Owns the payments service since March 2026, after Tomas Ruiz left.</span>
    </div>
  );
}

export function Landing() {
  const root = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    gsap.registerPlugin(ScrollTrigger);
    root.current?.classList.add("is-ready");
    ScrollTrigger.config({ ignoreMobileResize: true });
    gsap.ticker.lagSmoothing(0);

    const media = gsap.matchMedia();
    const context = gsap.context(() => {
      media.add(
        {
          wide: "(min-width: 761px) and (prefers-reduced-motion: no-preference)",
          phone: "(max-width: 760px) and (prefers-reduced-motion: no-preference)",
        },
        (self) => {
          const wide = Boolean(self.conditions?.wide);

          // Opening: the type rises and the brain floats up from behind the campus.
          gsap
            .timeline({ defaults: { ease: "expo.out" } })
            .from(".h-line > span", { yPercent: 112, duration: 1.15, stagger: 0.09 }, 0.1)
            .from(".h-sub, .h-cta", { y: 26, opacity: 0, duration: 0.9, stagger: 0.08 }, 0.5)
            .from(".w-brain-in", { y: "42vh", scale: 0.72, opacity: 0, duration: 1.8 }, 0)
            .from(".w-hq-in", { y: 150, duration: 1.5 }, 0.05)
            .from(".w-cloud-a", { x: "-46vw", duration: 2.1 }, 0)
            .from(".w-cloud-c", { x: "-30vw", duration: 2.1 }, 0);

          // Hero: the headline splits and flies off as you leave.
          gsap
            .timeline({
              defaults: { ease: "power2.in" },
              scrollTrigger: { trigger: ".s-hero", start: "top top", end: "bottom top", scrub: 0.6 },
            })
            .to(".h-line-a", { xPercent: -70, opacity: 0 }, 0)
            .to(".h-line-b", { xPercent: 70, opacity: 0 }, 0)
            .to(".h-rest", { y: -70, opacity: 0 }, 0);

          // The conversation: each message slams in from its own side, then the desk they left behind.
          const chat = gsap.timeline({
            defaults: { ease: "power3.out", duration: 1 },
            scrollTrigger: { trigger: ".s-chat", start: "top top", end: "+=340%", pin: true, scrub: 0.7, anticipatePin: 1 },
          });
          gsap.utils.toArray<HTMLElement>(".bubble").forEach((bubble, index) => {
            const fromRight = bubble.dataset.from === "new";
            chat.from(bubble, { x: fromRight ? "85vw" : "-85vw", rotate: fromRight ? 7 : -7, scale: 0.86 }, index * 0.9);
          });
          chat
            .to(".bubbles", { y: "-120vh", ease: "power2.in", duration: 1.4 }, "+=0.7")
            .from(".gone", { y: "110vh", rotate: 4, duration: 1.5 }, "<0.3")
            .from(".gone-line > span", { yPercent: 112, duration: 0.9, stagger: 0.14 }, "-=0.5")
            .to({}, { duration: 0.8 });

          // The answer: type the question, ask, then the sources fly in and lock under it.
          const typed = document.querySelector<HTMLElement>(".demo-typed");
          const timer = document.querySelector<HTMLElement>(".demo-time");
          const words = gsap.utils.toArray<HTMLElement>(".demo-answer span");
          const counter = { chars: 0, seconds: 0 };
          if (typed) typed.textContent = "";
          // Until Ask is pressed only the question bar shows, then the panel opens down to the answer.
          const demo = document.querySelector<HTMLElement>(".demo");
          const bar = document.querySelector<HTMLElement>(".demo-bar");
          const pad = demo ? parseFloat(getComputedStyle(demo).paddingTop) : 0;
          const closedBy = demo && bar ? Math.max(0, demo.offsetHeight - bar.offsetHeight - pad * 2) : 0;
          const closed = `inset(0px 0px ${closedBy}px 0px round 38px)`;
          const open = "inset(0px 0px 0px 0px round 38px)";
          const answer = gsap.timeline({
            defaults: { ease: "power3.out" },
            scrollTrigger: { trigger: ".s-answer", start: "top top", end: "+=420%", pin: true, scrub: 0.7, anticipatePin: 1 },
          });
          answer
            .fromTo(".demo", { clipPath: closed }, { clipPath: closed, duration: 0.01 }, 0)
            .from(".demo", { y: "100vh", scale: 0.8, rotate: -3, duration: 1.4 }, 0)
            .to(
              counter,
              {
                chars: QUESTION.length,
                duration: 1.5,
                ease: "none",
                onUpdate() {
                  if (typed) typed.textContent = QUESTION.slice(0, Math.round(counter.chars));
                },
              },
              "+=0.1",
            )
            .to(".demo-go", { scale: 0.9, duration: 0.14, ease: "power2.out" }, "+=0.1")
            .to(".demo-go", { scale: 1, duration: 0.2 })
            .to(".demo", { clipPath: open, duration: 0.9, ease: "power2.inOut" }, "<")
            .to(
              counter,
              {
                seconds: 4.2,
                duration: 1.1,
                ease: "none",
                onUpdate() {
                  if (timer) timer.textContent = `${counter.seconds.toFixed(1)} seconds`;
                },
              },
              "<",
            )
            .from(".demo-time-wrap", { opacity: 0, y: 10, duration: 0.3 }, "<")
            .from(words, { opacity: 0, y: 22, duration: 0.5, stagger: 0.025 }, "-=0.1")
            .set(".demo", { clipPath: "none" });

          gsap.utils.toArray<HTMLElement>(".src").forEach((card, index) => {
            const left = index < 2;
            answer.from(
              card,
              {
                x: wide ? (left ? "-70vw" : "70vw") : 0,
                y: wide ? (index % 2 ? "60vh" : "80vh") : "90vh",
                rotate: left ? -22 : 22,
                scale: 0.7,
                duration: 1,
              },
              index === 0 ? "+=0.2" : "-=0.72",
            );
          });
          answer.to({}, { duration: 1 });

          // What, then why: the word takes over the screen.
          gsap
            .timeline({
              defaults: { ease: "power3.inOut" },
              scrollTrigger: { trigger: ".s-why", start: "top top", end: "+=260%", pin: true, scrub: 0.7, anticipatePin: 1 },
            })
            .from(".word-what", { xPercent: -130, duration: 1.1, ease: "power3.out" })
            .from(".what-note", { opacity: 0, y: 24, duration: 0.5 }, "-=0.4")
            .fromTo(".strike", { scaleX: 0 }, { scaleX: 1, duration: 0.7 }, "+=0.4")
            .to(".word-what, .what-note, .strike", { yPercent: -180, opacity: 0, duration: 0.9, ease: "power2.in" }, "+=0.2")
            .from(".word-why", { yPercent: 130, scale: 0.6, duration: 1.2, ease: "power3.out" }, "-=0.35")
            .from(".why-note", { opacity: 0, y: 24, duration: 0.5 }, "-=0.4")
            .to({}, { duration: 0.6 });

          // Four questions: sideways across the sky on large screens, stacked on phones.
          if (wide) {
            const track = document.querySelector<HTMLElement>(".four-track");
            if (track) {
              gsap.to(track, {
                x: () => -(track.scrollWidth - window.innerWidth),
                ease: "none",
                scrollTrigger: {
                  trigger: ".s-four",
                  start: "top top",
                  end: () => `+=${track.scrollWidth}`,
                  pin: true,
                  scrub: 0.8,
                  invalidateOnRefresh: true,
                  anticipatePin: 1,
                },
              });
            }
          } else {
            gsap.utils.toArray<HTMLElement>(".panel").forEach((panel) => {
              gsap.from(panel, {
                y: 90,
                rotate: 3,
                duration: 0.9,
                ease: "power3.out",
                scrollTrigger: { trigger: panel, start: "top 88%", toggleActions: "play none none reverse" },
              });
            });
          }

          // The close: giant call to action rises at dusk.
          gsap.from(".end-line > span", {
            yPercent: 112,
            duration: 1.1,
            ease: "expo.out",
            stagger: 0.1,
            scrollTrigger: { trigger: ".s-end", start: "top 62%", toggleActions: "play none none reverse" },
          });

          // The world turns with the whole page. Made last so it measures the page after every pin exists.
          gsap
            .timeline({
              defaults: { ease: "none" },
              scrollTrigger: { start: 0, end: "max", scrub: 1.2 },
            })
            .to(".w-brain", { yPercent: -30, xPercent: wide ? -20 : -8, scale: 0.6, duration: 0.5 }, 0)
            .to(".w-brain", { yPercent: wide ? 6 : -40, xPercent: wide ? 12 : 6, scale: 0.62, duration: 0.2 }, 0.8)
            .to(".w-far", { yPercent: -14, duration: 1 }, 0)
            .to(".w-ground", { yPercent: 75, duration: 0.14 }, 0)
            .to(".w-ground", { yPercent: 0, duration: 0.14 }, 0.86)
            .to(".w-gold", { opacity: 1, duration: 0.16 }, 0.38)
            .to(".w-dusk", { opacity: 1, duration: 0.16 }, 0.72)
            .to(".w-hq-dusk", { opacity: 1, duration: 0.12 }, 0.8)
            .to(".w-trees", { filter: "brightness(0.42) saturate(0.8)", duration: 0.12 }, 0.8);
        },
      );
    }, root);

    // Fonts and photos can change heights after the first measure, so pins are re-measured once they're in.
    const refresh = () => ScrollTrigger.refresh();
    document.fonts?.ready.then(refresh);
    window.addEventListener("load", refresh);

    return () => {
      window.removeEventListener("load", refresh);
      media.revert();
      context.revert();
    };
  }, []);

  return (
    <div ref={root} className="lp">
      <noscript>
        <style>{`.lp .world, .lp .lp-flow { visibility: visible; }`}</style>
      </noscript>
      <div className="world" aria-hidden="true">
        <img className="w-sky" src="/world/sky-clear.webp" alt="" />
        <img className="w-sky w-gold" src="/world/sky-golden.jpg" alt="" />
        <img className="w-sky w-dusk" src="/world/sky-dusk.jpg" alt="" />
        <div className="w-far">
          <img className="w-cloud w-cloud-a" src="/world/cloud-a.webp" alt="" />
          <img className="w-cloud w-cloud-c" src="/world/cloud-c.webp" alt="" />
        </div>
        <div className="w-brain">
          <div className="w-brain-in">
            <img className="w-brain-img" src="/world/brain.webp" alt="" />
          </div>
        </div>
        <div className="w-ground">
          <div className="w-hq-in">
            <div className="w-trees" />
            <div className="w-hq-wrap">
              <img className="w-hq" src="/world/hq.webp" alt="" />
              <img className="w-hq w-hq-dusk" src="/world/hq-dusk.webp" alt="" />
            </div>
          </div>
        </div>
      </div>

      <header className="lp-top">
        <span className="lp-mark">Company Brain</span>
        <Link className="lp-pill" href="/app">
          Ask the brain
        </Link>
      </header>

      <main className="lp-flow">
        <section className="s-hero">
          <h1 className="h-title">
            <span className="h-line h-line-a">
              <span>Why is it</span>
            </span>{" "}
            <span className="h-line h-line-b">
              <span>built this way?</span>
            </span>
          </h1>
          <div className="h-rest">
            <p className="h-sub">
              Your company&apos;s memory in one place: who wrote it, why, where it was discussed and who owns it now.
            </p>
            <Link className="lp-pill lp-pill-big h-cta" href="/app">
              Ask the brain
            </Link>
          </div>
        </section>

        <section className="s-chat">
          <div className="bubbles">
            {CHAT.map((message) => (
              <p key={message.text} className="bubble" data-from={message.from}>
                {message.text}
              </p>
            ))}
          </div>
          <div className="gone">
            <img className="gone-photo" src="/world/desk.webp" alt="An empty desk with a cardboard box on it" />
            <h2 className="gone-title">
              <span className="gone-line">
                <span>The answer left</span>
              </span>{" "}
              <span className="gone-line">
                <span>with him.</span>
              </span>
            </h2>
          </div>
        </section>

        <section className="s-answer">
          <div className="demo">
            <div className="demo-bar">
              <span className="demo-typed">{QUESTION}</span>
              <span className="demo-go">Ask</span>
            </div>
            <p className="demo-answer">
              {ANSWER.split(" ").map((word, index) => (
                <span key={index}>{word} </span>
              ))}
            </p>
            <p className="demo-time-wrap">
              Answered in <span className="demo-time">4.2 seconds</span>
            </p>
            <ul className="srcs">
              {SOURCES.map((source) => (
                <li key={source.title} className={`src tone-${source.tone}`}>
                  <span className="src-kind">{source.kind}</span>
                  <strong className="src-title">{source.title}</strong>
                  <span className="src-who">{source.who}</span>
                  <span className="src-when">{source.when}</span>
                </li>
              ))}
            </ul>
          </div>
        </section>

        <section className="s-why">
          <div className="why-stage">
            <p className="word word-what">
              what
              <i className="strike" />
            </p>
            <p className="note what-note">Search tells you what the code does.</p>
            <p className="word word-why">why</p>
            <p className="note why-note">Company Brain tells you why it&apos;s there.</p>
          </div>
        </section>

        <section className="s-four">
          <div className="four-track">
            {FOUR.map((item, index) => (
              <article key={item.big} className={`panel tone-${item.tone}`}>
                <h3 className="panel-big">{item.big}</h3>
                <div className="panel-low">
                  <p className="panel-line">{item.line}</p>
                  <PanelProof index={index} />
                </div>
              </article>
            ))}
          </div>
        </section>

        <section className="s-end">
          <h2 className="end-title">
            <span className="end-line">
              <span>Stop asking</span>
            </span>{" "}
            <span className="end-line">
              <span>around.</span>
            </span>
          </h2>
          <Link className="lp-pill lp-pill-big" href="/app">
            Ask the brain
          </Link>
          <p className="lp-fine">This demo runs on a made-up company&apos;s code, pull requests and Slack.</p>
        </section>
      </main>
    </div>
  );
}
