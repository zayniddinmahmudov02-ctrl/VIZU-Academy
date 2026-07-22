export default function AdminLoading() {
  return (
    <div className="flex h-[60vh] items-center justify-center">
      <div className="h-10 w-10 animate-spin rounded-full border-[3px] border-white/10 border-t-[var(--admin-primary)]" />
    </div>
  );
}
