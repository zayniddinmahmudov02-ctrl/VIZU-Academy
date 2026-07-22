import { Quote } from "lucide-react";

const quotes = [
  { text: "Der Anfang ist die Hälfte des Ganzen.", author: "Aristoteles" },
];

export default function QuoteCard() {
  const quote = quotes[0];

  return (
    <section className="pattern-accent relative flex h-full flex-col items-center justify-center overflow-hidden rounded-card bg-gradient-to-br from-navy-900 to-navy-700 p-6 text-center text-white shadow-[var(--shadow-card)] ring-1 ring-accent-gold/20 sm:p-7">
      <Quote size={26} className="relative z-10 text-accent-gold" strokeWidth={1.75} />
      <p className="relative z-10 mt-4 max-w-xs text-sm font-medium italic leading-relaxed text-white/90">
        „{quote.text}“
      </p>
      <p className="relative z-10 mt-3 text-xs font-semibold uppercase tracking-wide text-accent-gold/80">
        — {quote.author}
      </p>
    </section>
  );
}
