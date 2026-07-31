"use client";

import { useState } from "react";
import { isAxiosError } from "axios";

import { useAsyncResource } from "./use-async-resource";
import * as certificatesService from "../services/certificates-service";
import type {
  IssueCertificateInput,
  UpdateCertificateInput,
} from "../types/certificate";

function extractErrorMessage(err: unknown, fallback: string): string {
  if (isAxiosError<{ message?: string }>(err)) {
    return err.response?.data?.message ?? fallback;
  }
  return fallback;
}

export function useAdminCertificates() {
  const resource = useAsyncResource(
    () => certificatesService.listCertificates(),
    [],
  );

  const [issuing, setIssuing] = useState(false);
  const [issueError, setIssueError] = useState<string | null>(null);

  async function issue(input: IssueCertificateInput) {
    setIssuing(true);
    setIssueError(null);

    try {
      const certificate = await certificatesService.issueCertificate(input);
      resource.refetch();
      return certificate;
    } catch (err) {
      setIssueError(extractErrorMessage(err, "Failed to issue certificate."));
      throw err;
    } finally {
      setIssuing(false);
    }
  }

  async function update(certificateId: string, data: UpdateCertificateInput) {
    await certificatesService.updateCertificate(certificateId, data);
    resource.refetch();
  }

  async function revoke(certificateId: string) {
    await certificatesService.revokeCertificate(certificateId);
    resource.refetch();
  }

  return {
    ...resource,
    issuing,
    issueError,
    issue,
    update,
    revoke,
  };
}
