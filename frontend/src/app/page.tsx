import WelcomeCard from "@/features/auth/components/welcome-card";

export default function HomePage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-surface-bg px-4 py-12">
      <div className="w-full">
        <WelcomeCard />
      </div>
    </main>
  );
}
