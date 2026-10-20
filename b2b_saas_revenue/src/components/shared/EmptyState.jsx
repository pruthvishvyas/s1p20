export function EmptyState({ message, action }) {
  return (
    <div className="empty-state">
      <span className="empty-icon" aria-hidden="true">&#128202;</span>
      <p className="empty-message">{message}</p>
      {action && <p className="empty-action">{action}</p>}
    </div>
  );
}
export const RUN_HINT = 'Run main.py, then python export_for_frontend.py, then regenerate/redeploy this dashboard.';
