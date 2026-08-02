export function getErrorMessage(error: unknown, fallback: string): string {
  const response = (error as { response?: { data?: { message?: string; detail?: string } } })
    ?.response;
  return response?.data?.message ?? response?.data?.detail ?? fallback;
}
