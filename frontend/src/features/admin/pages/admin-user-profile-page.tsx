"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Copy } from "lucide-react";

import { useAdminUserProfile } from "../hooks/use-admin-user-profile";
import { startImpersonation } from "@/src/lib/token";

import ProfileHeader from "../components/profile-header";
import ProfileActions from "../components/profile-actions";
import SubscriptionCard from "../components/subscription-card";
import ProgressViewer from "../components/progress-viewer";
import ActivityTimeline from "../components/activity-timeline";
import LoginHistoryTable from "../components/login-history-table";
import DeviceHistoryList from "../components/device-history-list";
import PaymentHistoryTable from "../components/payment-history-table";
import AuditLogTable from "../components/audit-log-table";
import AdminModal from "../components/admin-modal";
import AdminLoading from "../components/admin-loading";

type ModalKind = "ban" | "suspend" | "grant-premium" | "extend-subscription" | "add-tag" | "reset-password-result" | "impersonate-confirm" | null;

export default function AdminUserProfilePage({ userId }: { userId: string }) {
  const router = useRouter();
  const profile = useAdminUserProfile(userId);

  const [modal, setModal] = useState<ModalKind>(null);
  const [reasonInput, setReasonInput] = useState("");
  const [daysInput, setDaysInput] = useState("30");
  const [tagInput, setTagInput] = useState("");
  const [tempPassword, setTempPassword] = useState("");

  function closeModal() {
    setModal(null);
    setReasonInput("");
    setDaysInput("30");
    setTagInput("");
  }

  async function handleBan() {
    if (!reasonInput.trim()) return;
    await profile.ban(reasonInput.trim());
    closeModal();
  }

  async function handleSuspend() {
    const days = Number(daysInput);
    if (!days || days <= 0 || !reasonInput.trim()) return;
    await profile.suspend(days, reasonInput.trim());
    closeModal();
  }

  async function handleGrantPremium() {
    const days = Number(daysInput);
    if (!days || days <= 0) return;
    await profile.grantPremium(days);
    closeModal();
  }

  async function handleExtendSubscription() {
    const days = Number(daysInput);
    if (!days || days <= 0) return;
    await profile.extendSubscription(days);
    closeModal();
  }

  async function handleAddTag() {
    if (!tagInput.trim()) return;
    await profile.addTag(tagInput.trim());
    closeModal();
  }

  async function handleResetPassword() {
    const password = await profile.resetPassword();
    if (password) {
      setTempPassword(password);
      setModal("reset-password-result");
    }
  }

  async function handleImpersonate() {
    const result = await profile.impersonate();
    if (result) {
      startImpersonation(result.accessToken, result.user.username);
      router.push("/dashboard");
    }
  }

  if (profile.detail.loading) {
    return <AdminLoading />;
  }

  if (profile.detail.error || !profile.detail.data) {
    return (
      <div className="admin-glass rounded-2xl p-8 text-center">
        <p className="text-sm font-semibold text-white">User not found</p>
        <button type="button" onClick={() => router.push("/admin/users")} className="mt-3 text-xs text-[var(--admin-primary)]">
          Back to Users
        </button>
      </div>
    );
  }

  const user = profile.detail.data;

  return (
    <div className="space-y-6">
      <button
        type="button"
        onClick={() => router.push("/admin/users")}
        className="flex items-center gap-1.5 text-xs font-semibold text-[var(--admin-text-muted)] transition-colors hover:text-white"
      >
        <ArrowLeft size={14} /> Back to Users
      </button>

      <ProfileHeader user={user} onAddTag={() => setModal("add-tag")} onRemoveTag={(tagId) => profile.removeTag(tagId)} />

      <ProfileActions
        user={user}
        disabled={profile.actionPending}
        onBan={() => setModal("ban")}
        onUnban={() => profile.unban()}
        onSuspend={() => setModal("suspend")}
        onUnsuspend={() => profile.unsuspend()}
        onGrantPremium={() => setModal("grant-premium")}
        onExtendSubscription={() => setModal("extend-subscription")}
        onResetPassword={handleResetPassword}
        onImpersonate={() => setModal("impersonate-confirm")}
      />

      {profile.actionError && (
        <div className="rounded-xl bg-[#ef4444]/10 px-4 py-3 text-xs text-[#ef4444]">{profile.actionError}</div>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        {profile.subscription.data && <SubscriptionCard subscription={profile.subscription.data} />}
        {profile.progress.data && <ProgressViewer progress={profile.progress.data} />}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {profile.activity.data && <ActivityTimeline items={profile.activity.data} />}
        {profile.deviceHistory.data && <DeviceHistoryList devices={profile.deviceHistory.data} />}
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {profile.loginHistory.data && (
          <LoginHistoryTable history={profile.loginHistory.data} page={profile.loginHistoryPage} onPageChange={profile.setLoginHistoryPage} />
        )}
        {profile.payments.data && <PaymentHistoryTable payments={profile.payments.data} />}
      </div>

      {profile.auditLog.data && (
        <AuditLogTable log={profile.auditLog.data} page={profile.auditLogPage} onPageChange={profile.setAuditLogPage} />
      )}

      {/* Ban modal */}
      <AdminModal open={modal === "ban"} onOpenChange={(open) => !open && closeModal()} title="Ban User">
        <p className="mb-2 text-xs text-[var(--admin-text-muted)]">This immediately blocks the user from signing in.</p>
        <textarea
          value={reasonInput}
          onChange={(e) => setReasonInput(e.target.value)}
          placeholder="Reason for ban…"
          className="h-24 w-full rounded-xl border border-[var(--admin-border)] bg-white/[0.03] p-3 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50"
        />
        <button
          type="button"
          onClick={handleBan}
          disabled={!reasonInput.trim() || profile.actionPending}
          className="mt-4 w-full rounded-xl bg-[#ef4444] py-2.5 text-sm font-semibold text-white disabled:opacity-40"
        >
          Confirm Ban
        </button>
      </AdminModal>

      {/* Suspend modal */}
      <AdminModal open={modal === "suspend"} onOpenChange={(open) => !open && closeModal()} title="Suspend User">
        <label className="mb-1 block text-xs text-[var(--admin-text-muted)]">Duration (days)</label>
        <input
          type="number"
          min={1}
          value={daysInput}
          onChange={(e) => setDaysInput(e.target.value)}
          className="mb-3 w-full rounded-xl border border-[var(--admin-border)] bg-white/[0.03] p-3 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50"
        />
        <label className="mb-1 block text-xs text-[var(--admin-text-muted)]">Reason</label>
        <textarea
          value={reasonInput}
          onChange={(e) => setReasonInput(e.target.value)}
          placeholder="Reason for suspension…"
          className="h-20 w-full rounded-xl border border-[var(--admin-border)] bg-white/[0.03] p-3 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50"
        />
        <button
          type="button"
          onClick={handleSuspend}
          disabled={!reasonInput.trim() || profile.actionPending}
          className="mt-4 w-full rounded-xl bg-[#f59e0b] py-2.5 text-sm font-semibold text-white disabled:opacity-40"
        >
          Confirm Suspension
        </button>
      </AdminModal>

      {/* Grant premium modal */}
      <AdminModal open={modal === "grant-premium"} onOpenChange={(open) => !open && closeModal()} title="Grant Premium">
        <label className="mb-1 block text-xs text-[var(--admin-text-muted)]">Days to grant</label>
        <input
          type="number"
          min={1}
          value={daysInput}
          onChange={(e) => setDaysInput(e.target.value)}
          className="w-full rounded-xl border border-[var(--admin-border)] bg-white/[0.03] p-3 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50"
        />
        <button
          type="button"
          onClick={handleGrantPremium}
          disabled={profile.actionPending}
          className="mt-4 w-full rounded-xl bg-[var(--admin-primary)] py-2.5 text-sm font-semibold text-white disabled:opacity-40"
        >
          Grant Premium
        </button>
      </AdminModal>

      {/* Extend subscription modal */}
      <AdminModal open={modal === "extend-subscription"} onOpenChange={(open) => !open && closeModal()} title="Extend Subscription">
        <label className="mb-1 block text-xs text-[var(--admin-text-muted)]">Additional days</label>
        <input
          type="number"
          min={1}
          value={daysInput}
          onChange={(e) => setDaysInput(e.target.value)}
          className="w-full rounded-xl border border-[var(--admin-border)] bg-white/[0.03] p-3 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50"
        />
        <button
          type="button"
          onClick={handleExtendSubscription}
          disabled={profile.actionPending}
          className="mt-4 w-full rounded-xl bg-[var(--admin-primary)] py-2.5 text-sm font-semibold text-white disabled:opacity-40"
        >
          Extend
        </button>
      </AdminModal>

      {/* Add tag modal */}
      <AdminModal open={modal === "add-tag"} onOpenChange={(open) => !open && closeModal()} title="Add Tag">
        <input
          value={tagInput}
          onChange={(e) => setTagInput(e.target.value)}
          placeholder="e.g. VIP, Beta Tester"
          className="w-full rounded-xl border border-[var(--admin-border)] bg-white/[0.03] p-3 text-sm text-white outline-none focus:border-[var(--admin-primary)]/50"
        />
        <button
          type="button"
          onClick={handleAddTag}
          disabled={!tagInput.trim() || profile.actionPending}
          className="mt-4 w-full rounded-xl bg-[var(--admin-primary)] py-2.5 text-sm font-semibold text-white disabled:opacity-40"
        >
          Add Tag
        </button>
      </AdminModal>

      {/* Reset password result modal */}
      <AdminModal open={modal === "reset-password-result"} onOpenChange={(open) => !open && closeModal()} title="Temporary Password">
        <p className="mb-2 text-xs text-[var(--admin-text-muted)]">
          Share this password with the user manually. It will not be shown again.
        </p>
        <div className="flex items-center justify-between rounded-xl border border-[var(--admin-border)] bg-white/[0.03] px-3 py-2.5">
          <code className="text-sm text-white">{tempPassword}</code>
          <button type="button" onClick={() => navigator.clipboard.writeText(tempPassword)} className="text-[var(--admin-text-muted)] hover:text-white">
            <Copy size={14} />
          </button>
        </div>
      </AdminModal>

      {/* Impersonate confirm modal */}
      <AdminModal open={modal === "impersonate-confirm"} onOpenChange={(open) => !open && closeModal()} title="Login As User">
        <p className="mb-4 text-xs text-[var(--admin-text-muted)]">
          You will be signed in as <span className="font-semibold text-white">{user.username}</span> for 30 minutes. This action is
          logged in the audit trail.
        </p>
        <button
          type="button"
          onClick={handleImpersonate}
          disabled={profile.actionPending}
          className="w-full rounded-xl bg-[#ef4444] py-2.5 text-sm font-semibold text-white disabled:opacity-40"
        >
          Continue
        </button>
      </AdminModal>
    </div>
  );
}
