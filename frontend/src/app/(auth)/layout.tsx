import PageTransition from "@/components/motion/page-transition";

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-surface-bg px-4 py-12">
      <div className="pointer-events-none absolute -left-32 -top-32 h-[420px] w-[420px] rounded-full bg-accent-blue/10 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-32 -right-32 h-[420px] w-[420px] rounded-full bg-accent-purple/10 blur-3xl" />

      <div className="relative z-10 w-full">
        <PageTransition>{children}</PageTransition>
      </div>
    </main>
  );
}
