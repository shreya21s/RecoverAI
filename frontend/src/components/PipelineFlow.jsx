import React from 'react';

export function PipelineFlow({ status, strategy, policyDecision }) {
  const steps = [
    { id: 'failed', label: 'Failed Payment', state: 'completed' },
    { id: 'diagnosis', label: 'Diagnosis', state: status ? 'completed' : 'pending' },
    { id: 'customer', label: 'Customer Profiling', state: status ? 'completed' : 'pending' },
    { id: 'strategy', label: strategy ? 'completed' : 'pending', labelText: strategy || 'Strategy' },
    { id: 'policy', label: 'Policy Check', state: policyDecision ? (policyDecision === 'APPROVED' ? 'completed' : policyDecision === 'HITL_REQUIRED' ? 'warning' : 'failed') : 'pending' },
    { id: 'execution', label: 'Execution', state: status === 'RECOVERED' ? 'completed' : status === 'STOPPED' ? 'failed' : status === 'WAITING_FOR_APPROVAL' ? 'warning' : 'pending' }
  ];

  return (
    <div className="pipeline-flow">
      {steps.map((step, idx) => (
        <React.Fragment key={step.id}>
          <div className={`pipeline-step ${step.state === 'completed' ? 'completed' : step.state === 'warning' ? 'active' : step.state === 'failed' ? 'failed' : ''}`}>
            <div style={{ fontSize: '11px', textTransform: 'uppercase', opacity: 0.7, marginBottom: '2px' }}>
              Step {idx + 1}
            </div>
            <div style={{ fontWeight: '600' }}>
              {step.labelText || step.label}
            </div>
          </div>
          {idx < steps.length - 1 && (
            <span className="pipeline-arrow">➔</span>
          )}
        </React.Fragment>
      ))}
    </div>
  );
}
