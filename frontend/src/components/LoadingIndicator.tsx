export default function LoadingIndicator({ children }: { children: string }) {
  return (
    <p className="loading-message" role="status" aria-live="polite">
      <span className="loading-spinner" aria-hidden="true" />
      {children}
    </p>
  );
}
