import React from 'react';

export function StatusBadge({ status }) {
  if (!status) return null;
  const lowerStatus = status.toLowerCase();

  let className = 'badge';
  if (['recovered', 'success', 'completed'].includes(lowerStatus)) {
    className += ' badge-recovered';
  } else if (['waiting_for_approval', 'hitl_required', 'pending', 'running', 'waiting'].includes(lowerStatus)) {
    className += ' badge-hitl';
  } else if (['stopped', 'blocked', 'failed'].includes(lowerStatus)) {
    className += ' badge-stopped';
  } else {
    className += ' badge-processing';
  }

  // Format label: replace underscores with spaces
  const label = status.replace(/_/g, ' ');

  return <span className={className}>{label}</span>;
}
