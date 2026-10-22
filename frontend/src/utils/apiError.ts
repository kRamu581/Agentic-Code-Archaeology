import axios from "axios";

function validationMessage(issue: unknown): string | null {
  if (typeof issue === "string") return issue;
  if (issue && typeof issue === "object" && "msg" in issue && typeof issue.msg === "string") {
    return issue.msg.replace(/^Value error,\s*/i, "");
  }
  return null;
}

export function getApiError(error: unknown, fallback: string): string {
  if (!axios.isAxiosError(error)) return fallback;
  const detail: unknown = error.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const messages = detail.map(validationMessage).filter((message): message is string => Boolean(message));
    if (messages.length) return messages.join(" ");
  }
  return fallback;
}
