import React, { useState, useEffect } from 'react';
import {
  LayoutDashboard,
  Receipt,
  History,
  UserCheck,
  Database,
  AlertTriangle,
  TrendingUp,
  Coins,
  Eye,
  RefreshCw,
  Play,
  CheckCircle,
  XCircle,
  Plus,
  Search,
  ArrowRight,
  Lock,
  ShieldAlert,
  ChevronDown,
  ChevronUp,
  Sparkles,
  X,
  Zap,
  UserPlus,
  DollarSign,
  Sliders,
  Filter,
  CheckSquare,
  Square,
  ChevronLeft,
  ChevronRight,
  RotateCcw,
  Save,
  Layers,
  ListFilter
} from 'lucide-react';
import { api } from './api';
import { StatusBadge } from './components/StatusBadge';
import { PipelineFlow } from './components/PipelineFlow';

function App() {
  const [currentPage, setCurrentPage] = useState('Overview');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [processingText, setProcessingText] = useState('');

  const formatDate = (isoString) => {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
  };

  // App State
  const [cases, setCases] = useState([]);
  const [batches, setBatches] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [overallMetrics, setOverallMetrics] = useState({
    recoveredRevenue: 0,
    recoveryRate: 0,
    processedCases: 0,
    pendingReviews: 0,
    baselineRevenue: 0,
    incrementalRevenue: 0
  });

  // Details Drawer State
  const [activeCase, setActiveCase] = useState(null);
  const [activeCaseAudit, setActiveCaseAudit] = useState([]);

  // Modals State
  const [activeReview, setActiveReview] = useState(null);
  const [decisionType, setDecisionType] = useState(''); // 'approve' | 'reject'
  const [decisionReason, setDecisionReason] = useState('');
  const [revalidationOutcome, setRevalidationOutcome] = useState(null);

  // Audit Trails State
  const [auditEvents, setAuditEvents] = useState([]);
  const [expandedEventId, setExpandedEventId] = useState(null);
  const [auditSearch, setAuditSearch] = useState('');
  const [auditActorFilter, setAuditActorFilter] = useState('ALL');
  const [auditPage, setAuditPage] = useState(1);
  const [auditPageSize, setAuditPageSize] = useState(15);
  
  // Batch Impact Modal State
  const [selectedBatchImpact, setSelectedBatchImpact] = useState(null);

  // Search, Filters & Pagination State for Recovery Cases
  const [caseSearch, setCaseSearch] = useState('');
  const [caseStatusFilter, setCaseStatusFilter] = useState('ALL');
  const [caseFailureFilter, setCaseFailureFilter] = useState('ALL');
  const [casePage, setCasePage] = useState(1);
  const [casePageSize, setCasePageSize] = useState(10);
  const [selectedCaseIds, setSelectedCaseIds] = useState(new Set());
  const [isBatchBuilderOpen, setIsBatchBuilderOpen] = useState(false);
  const [customBatchName, setCustomBatchName] = useState('Custom Recovery Portfolio');

  // Policy Rules Studio State
  const [policyConfig, setPolicyConfig] = useState({
    MAX_RETRIES: 3,
    MAX_REMINDERS: 3,
    MIN_RECOVERY_PROBABILITY: 0.15,
    HITL_AMOUNT_THRESHOLD: 50000,
    HITL_CONFIDENCE_THRESHOLD: 0.70,
    HITL_FAILED_ATTEMPTS_THRESHOLD: 2,
    SIMULATION_MODE: true
  });
  const [policyFeedback, setPolicyFeedback] = useState(null);
  const [testPolicyAmount, setTestPolicyAmount] = useState(65000);
  const [testPolicyRetries, setTestPolicyRetries] = useState(0);

  // Custom Case / Personalized Revenue Intake Modal State
  const [isCustomCaseModalOpen, setIsCustomCaseModalOpen] = useState(false);
  const [customCaseForm, setCustomCaseForm] = useState({
    amount: 15000,
    currency: 'INR',
    payment_method: 'UPI',
    failure_code: 'TEMPORARY_BANK_FAILURE',
    retry_count: 0,
    reminder_count: 0,
    is_disputed: false,
    customer_name: 'Aditi Rao',
    customer_segment: 'HIGH_VALUE_RELIABLE',
    customer_ltv: 120000,
    successful_payments: 15,
    failed_payments: 1,
    engagement_score: 9.0,
    auto_run: true
  });

  const PRESETS = [
    {
      name: '💎 High-Value VIP',
      badge: 'HITL Review (>₹50k)',
      data: {
        amount: 85000,
        customer_name: 'Vikramaditya Singhania',
        customer_segment: 'HIGH_VALUE_RELIABLE',
        customer_ltv: 350000,
        successful_payments: 28,
        failed_payments: 1,
        engagement_score: 9.6,
        payment_method: 'NETBANKING',
        failure_code: 'TEMPORARY_BANK_FAILURE',
        retry_count: 0,
        reminder_count: 0,
        is_disputed: false
      }
    },
    {
      name: '⚡ Quick Recovery',
      badge: 'Auto Retry (₹4.5k)',
      data: {
        amount: 4500,
        customer_name: 'Ananya Deshmukh',
        customer_segment: 'RELIABLE',
        customer_ltv: 60000,
        successful_payments: 12,
        failed_payments: 1,
        engagement_score: 8.5,
        payment_method: 'UPI',
        failure_code: 'TEMPORARY_BANK_FAILURE',
        retry_count: 0,
        reminder_count: 0,
        is_disputed: false
      }
    },
    {
      name: '🛒 Cart Abandonment',
      badge: 'Payment Link (₹2.8k)',
      data: {
        amount: 2800,
        customer_name: 'Rahul Sen',
        customer_segment: 'AVERAGE',
        customer_ltv: 30000,
        successful_payments: 6,
        failed_payments: 2,
        engagement_score: 6.0,
        payment_method: 'CARD',
        failure_code: 'PAYMENT_ABANDONED',
        retry_count: 0,
        reminder_count: 0,
        is_disputed: false
      }
    },
    {
      name: '⚠️ High-Risk Multi-Retry',
      badge: 'Policy Hard Stop',
      data: {
        amount: 9500,
        customer_name: 'Karan Mehra',
        customer_segment: 'AT_RISK',
        customer_ltv: 18000,
        successful_payments: 2,
        failed_payments: 4,
        engagement_score: 3.0,
        payment_method: 'CARD',
        failure_code: 'REPEATED_FAILURE',
        retry_count: 3,
        reminder_count: 3,
        is_disputed: false
      }
    },
    {
      name: '🛡️ Disputed Charge',
      badge: 'Dispute Intercept',
      data: {
        amount: 14000,
        customer_name: 'Pooja Hegde',
        customer_segment: 'AVERAGE',
        customer_ltv: 45000,
        successful_payments: 5,
        failed_payments: 1,
        engagement_score: 5.5,
        payment_method: 'CARD',
        failure_code: 'AUTHENTICATION_FAILED',
        retry_count: 1,
        reminder_count: 0,
        is_disputed: true
      }
    }
  ];

  const handleApplyPreset = (presetData) => {
    setCustomCaseForm(prev => ({
      ...prev,
      ...presetData
    }));
  };

  const handleCreateCustomCase = async (e) => {
    if (e) e.preventDefault();
    if (!customCaseForm.amount || Number(customCaseForm.amount) <= 0) {
      alert('Please enter a valid revenue amount (> ₹0)');
      return;
    }
    setLoading(true);
    setProcessingText(customCaseForm.auto_run ? 'Creating case & running AI agent graph...' : 'Creating custom recovery case...');
    try {
      const payload = {
        ...customCaseForm,
        amount: parseFloat(customCaseForm.amount),
        customer_ltv: parseFloat(customCaseForm.customer_ltv || 0),
        successful_payments: parseInt(customCaseForm.successful_payments || 0, 10),
        failed_payments: parseInt(customCaseForm.failed_payments || 0, 10),
        retry_count: parseInt(customCaseForm.retry_count || 0, 10),
        reminder_count: parseInt(customCaseForm.reminder_count || 0, 10),
        engagement_score: parseFloat(customCaseForm.engagement_score || 5.0)
      };
      const res = await api.createCase(payload);
      setIsCustomCaseModalOpen(false);
      await fetchData(true);
      if (res.case_id) {
        await handleOpenCaseDetails(res.case_id);
      }
      alert(`Recovery Case ${res.case_id} created with revenue ₹${Number(res.amount).toLocaleString('en-IN')}!`);
    } catch (err) {
      alert(`Failed to create custom case: ${err.message}`);
    } finally {
      setProcessingText('');
      setLoading(false);
    }
  };

  const handleOpenBatchImpact = async (batchId) => {
    try {
      const impact = await api.getBatchImpact(batchId);
      setSelectedBatchImpact(impact);
    } catch (err) {
      alert(`Failed to load batch impact report: ${err.message}`);
    }
  };

  // Fetch initial data
  const fetchData = async (quiet = false) => {
    if (!quiet) setLoading(true);
    setError(null);
    try {
      const casesData = await api.getCases();
      setCases(casesData);

      const batchesData = await api.getBatches();
      setBatches(batchesData);

      const reviewsData = await api.getPendingApprovals();
      setReviews(reviewsData);

      // Compute aggregated overview metrics
      let totalRecovered = 0;
      let totalOutstanding = 0;
      let processed = 0;
      let pendingReviewsCount = reviewsData.length;

      casesData.forEach(c => {
        const amt = c.payment?.amount || 0;
        totalOutstanding += amt;
        if (c.status === 'RECOVERED') {
          totalRecovered += amt;
        }
        if (c.status !== 'PENDING') {
          processed += 1;
        }
      });

      // Fetch batch-level metrics if a completed batch exists
      let baselineRev = 0;
      let actualRecoveredRev = 0;
      
      const completedBatch = batchesData.find(b => b.status === 'COMPLETED' || b.status === 'COMPLETED_WITH_ERRORS');
      if (completedBatch) {
        try {
          const impact = await api.getBatchImpact(completedBatch.batch_id);
          actualRecoveredRev = impact.financial_impact.recovered_revenue;
          baselineRev = impact.baseline_comparison.baseline_recovered_revenue;
        } catch (e) {
          console.error("Failed to load batch impact metrics", e);
        }
      } else {
        // Fallback calculation from individual actions if no batch run
        casesData.forEach(c => {
          if (c.status === 'RECOVERED') {
            actualRecoveredRev += c.payment?.amount || 0;
          }
        });
      }

      setOverallMetrics({
        recoveredRevenue: actualRecoveredRev,
        recoveryRate: totalOutstanding > 0 ? ((actualRecoveredRev / totalOutstanding) * 100).toFixed(1) : 0,
        processedCases: processed,
        pendingReviews: pendingReviewsCount,
        baselineRevenue: baselineRev,
        incrementalRevenue: Math.max(0, actualRecoveredRev - baselineRev)
      });
    } catch (err) {
      setError(err.message || 'Failed to fetch dashboard data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // API Actions
  const handleResetDatabase = async () => {
    setLoading(true);
    setProcessingText('Resetting and seeding deterministic simulation data...');
    try {
      await api.resetDatabase();
      await fetchData(true);
      alert('Simulation database successfully reset and seeded with 100 cases!');
    } catch (err) {
      alert(`Simulation database reset failed: ${err.message}`);
    } finally {
      setProcessingText('');
      setLoading(false);
    }
  };

  const handleOpenCaseDetails = async (caseId) => {
    try {
      const caseDetail = await api.getCase(caseId);
      setActiveCase(caseDetail);
      const audit = await api.getCaseAuditTrail(caseId);
      setActiveCaseAudit(audit);
    } catch (err) {
      alert(`Failed to load case details: ${err.message}`);
    }
  };

  const handleTriggerScheduled = async (caseId) => {
    setLoading(true);
    setProcessingText(`Manually executing scheduled retry action for ${caseId}...`);
    try {
      const result = await api.triggerScheduled(caseId);
      alert(`Scheduled action triggered successfully! Final status: ${result.final_status}`);
      await handleOpenCaseDetails(caseId);
      await fetchData(true);
    } catch (err) {
      alert(`Failed to trigger scheduled retry: ${err.message}`);
    } finally {
      setProcessingText('');
      setLoading(false);
    }
  };

  const handleRunCase = async (caseId) => {
    setLoading(true);
    setProcessingText(`Running AI recovery orchestration for case ${caseId}...`);
    try {
      const result = await api.runCase(caseId);
      alert(`Recovery workflow completed! Final status: ${result.final_status}`);
      await handleOpenCaseDetails(caseId);
      await fetchData(true);
    } catch (err) {
      alert(`Failed to run recovery workflow: ${err.message}`);
    } finally {
      setProcessingText('');
      setLoading(false);
    }
  };

  const handleCreateDemoBatch = async () => {
    setLoading(true);
    setProcessingText('Creating showcase batch BATCH-DEMO-001...');
    try {
      // Seed BATCH-DEMO-001 with showcase cases
      await api.createBatch("August Recovery Portfolio", [
        "REC-DEMO-001",
        "REC-DEMO-002",
        "REC-DEMO-003",
        "REC-DEMO-004",
        "REC-DEMO-005"
      ]);
      await fetchData(true);
      alert('Demo batch BATCH-DEMO-001 created successfully!');
    } catch (err) {
      alert(`Failed to create batch: ${err.message}`);
    } finally {
      setProcessingText('');
      setLoading(false);
    }
  };

  const handleRunBatch = async (batchId) => {
    setLoading(true);
    setProcessingText(`Executing recovery portfolio ${batchId}...`);
    try {
      await api.runBatch(batchId);
      await fetchData(true);
      alert('Batch processing completed successfully!');
    } catch (err) {
      alert(`Batch processing failed: ${err.message}`);
    } finally {
      setProcessingText('');
      setLoading(false);
    }
  };

  const handleOpenReview = async (caseId, type) => {
    try {
      const context = await api.getApprovalContext(caseId);
      setActiveReview(context);
      setDecisionType(type);
      setDecisionReason('');
      setRevalidationOutcome(null);
    } catch (err) {
      alert(`Failed to load approval context: ${err.message}`);
    }
  };

  const handleConfirmDecision = async () => {
    if (!activeReview) return;
    setLoading(true);
    setProcessingText(decisionType === 'approve' ? 'Processing approval revalidation...' : 'Stopping recovery action...');
    try {
      // Stale data check: refresh list to verify if it is still pending
      const latestPending = await api.getPendingApprovals();
      const stillPending = latestPending.some(p => p.case_id === activeReview.case_id);
      if (!stillPending) {
        alert('This case state has already changed. Refreshing review queue...');
        setActiveReview(null);
        await fetchData(true);
        return;
      }

      let outcome;
      if (decisionType === 'approve') {
        outcome = await api.approveCase(activeReview.case_id, 'admin_reviewer', decisionReason);
        setRevalidationOutcome(outcome);
      } else {
        outcome = await api.rejectCase(activeReview.case_id, 'admin_reviewer', decisionReason);
        setRevalidationOutcome(outcome);
      }
      await fetchData(true);
    } catch (err) {
      alert(`Action failed: ${err.message}`);
    } finally {
      setProcessingText('');
      setLoading(false);
    }
  };

  const fetchAuditEvents = async () => {
    setLoading(true);
    try {
      // Load audit trail from the first batch or retrieve general logs
      const completedBatch = batches.find(b => b.status === 'COMPLETED' || b.status === 'COMPLETED_WITH_ERRORS');
      if (completedBatch) {
        const events = await api.getBatchAuditTrail(completedBatch.batch_id);
        setAuditEvents(events);
      } else {
        // Fallback: list case-level events for REC-DEMO-001
        const events = await api.getCaseAuditTrail('REC-DEMO-001');
        setAuditEvents(events);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchPolicyConfig = async () => {
    try {
      const cfg = await api.getPolicyConfig();
      setPolicyConfig(cfg);
    } catch (e) {
      console.error("Failed to load policy config", e);
    }
  };

  const handleSavePolicy = async () => {
    setLoading(true);
    setProcessingText('Saving policy thresholds...');
    try {
      const updated = await api.updatePolicyConfig(policyConfig);
      setPolicyConfig(updated);
      setPolicyFeedback({ type: 'success', message: 'Policy rules and safety thresholds updated successfully!' });
      setTimeout(() => setPolicyFeedback(null), 4000);
    } catch (err) {
      setPolicyFeedback({ type: 'error', message: `Failed to save policy: ${err.message}` });
    } finally {
      setProcessingText('');
      setLoading(false);
    }
  };

  const handleResetPolicy = async () => {
    setLoading(true);
    setProcessingText('Resetting policy thresholds to defaults...');
    try {
      const reset = await api.resetPolicyConfig();
      setPolicyConfig(reset);
      setPolicyFeedback({ type: 'success', message: 'Policy thresholds reset to system defaults.' });
      setTimeout(() => setPolicyFeedback(null), 4000);
    } catch (err) {
      setPolicyFeedback({ type: 'error', message: `Failed to reset policy: ${err.message}` });
    } finally {
      setProcessingText('');
      setLoading(false);
    }
  };

  const handleToggleSelectCase = (caseId) => {
    setSelectedCaseIds(prev => {
      const next = new Set(prev);
      if (next.has(caseId)) next.delete(caseId);
      else next.add(caseId);
      return next;
    });
  };

  const handleSelectAllVisibleCases = () => {
    const eligibleVisible = paginatedCases.filter(c => c.status !== 'RECOVERED' && c.status !== 'STOPPED').map(c => c.case_id);
    const allSelected = eligibleVisible.length > 0 && eligibleVisible.every(id => selectedCaseIds.has(id));
    setSelectedCaseIds(prev => {
      const next = new Set(prev);
      if (allSelected) {
        eligibleVisible.forEach(id => next.delete(id));
      } else {
        eligibleVisible.forEach(id => next.add(id));
      }
      return next;
    });
  };

  const handleSelectCategoryPreset = (category) => {
    let matched = [];
    if (category === 'ALL_ELIGIBLE') {
      matched = cases.filter(c => c.status !== 'RECOVERED' && c.status !== 'STOPPED').map(c => c.case_id);
    } else if (category === 'HIGH_VALUE') {
      matched = cases.filter(c => (c.payment?.amount || 0) >= policyConfig.HITL_AMOUNT_THRESHOLD && c.status !== 'RECOVERED' && c.status !== 'STOPPED').map(c => c.case_id);
    } else if (category === 'UPI') {
      matched = cases.filter(c => c.payment?.payment_method === 'UPI' && c.status !== 'RECOVERED' && c.status !== 'STOPPED').map(c => c.case_id);
    } else if (category === 'ABANDONMENT') {
      matched = cases.filter(c => c.payment?.failure_code === 'PAYMENT_ABANDONED' && c.status !== 'RECOVERED' && c.status !== 'STOPPED').map(c => c.case_id);
    }
    setSelectedCaseIds(new Set(matched));
  };

  const handleCreateCustomBatchFromSelected = async () => {
    if (selectedCaseIds.size === 0) {
      alert('Please select at least one eligible case to create a batch.');
      return;
    }
    setLoading(true);
    setProcessingText(`Creating batch "${customBatchName}" with ${selectedCaseIds.size} cases...`);
    try {
      await api.createBatch(customBatchName, Array.from(selectedCaseIds));
      setIsBatchBuilderOpen(false);
      setSelectedCaseIds(new Set());
      await fetchData(true);
      setCurrentPage('Batches');
      alert(`Batch "${customBatchName}" created successfully!`);
    } catch (err) {
      alert(`Failed to create custom batch: ${err.message}`);
    } finally {
      setProcessingText('');
      setLoading(false);
    }
  };

  useEffect(() => {
    if (currentPage === 'Audit') {
      fetchAuditEvents();
    }
    if (currentPage === 'PolicyStudio') {
      fetchPolicyConfig();
    }
  }, [currentPage, batches]);

  return (
    <div className="app-container">
      {/* Sidebar */}
      <div className="sidebar">
        <div className="sidebar-logo">
          <Database size={24} className="text-indigo-400" />
          <h1>RecoverAI</h1>
        </div>
        <div className="sidebar-menu">
          <div
            className={`menu-item ${currentPage === 'Overview' ? 'active' : ''}`}
            onClick={() => setCurrentPage('Overview')}
          >
            <LayoutDashboard size={18} />
            Overview
          </div>
          <div
            className={`menu-item ${currentPage === 'Cases' ? 'active' : ''}`}
            onClick={() => setCurrentPage('Cases')}
          >
            <Receipt size={18} />
            Recovery Cases
          </div>
          <div
            className={`menu-item ${currentPage === 'Batches' ? 'active' : ''}`}
            onClick={() => setCurrentPage('Batches')}
          >
            <Coins size={18} />
            Batches
          </div>
          <div
            className={`menu-item ${currentPage === 'HumanReview' ? 'active' : ''}`}
            onClick={() => setCurrentPage('HumanReview')}
          >
            <UserCheck size={18} />
            Human Review
            {reviews.length > 0 && (
              <span style={{
                marginLeft: 'auto',
                backgroundColor: 'var(--accent-amber)',
                color: 'black',
                fontSize: '11px',
                fontWeight: 'bold',
                padding: '2px 6px',
                borderRadius: '10px'
              }}>{reviews.length}</span>
            )}
          </div>
          <div
            className={`menu-item ${currentPage === 'PolicyStudio' ? 'active' : ''}`}
            onClick={() => setCurrentPage('PolicyStudio')}
          >
            <Sliders size={18} />
            Policy Studio
          </div>
          <div
            className={`menu-item ${currentPage === 'Audit' ? 'active' : ''}`}
            onClick={() => setCurrentPage('Audit')}
          >
            <History size={18} />
            Audit Trail
          </div>
        </div>
        <div style={{ padding: '24px', borderTop: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: '600' }}>DEMO CONTROLS</div>
          <button 
            className="btn btn-primary" 
            style={{ width: '100%', justifyContent: 'center', backgroundColor: 'var(--accent-rose)', borderColor: 'var(--accent-rose)', color: 'white' }} 
            onClick={handleResetDatabase} 
            disabled={loading}
          >
            <RefreshCw size={14} className={loading && processingText.includes('Resetting') ? 'animate-spin' : ''} />
            {loading && processingText.includes('Resetting') ? 'Resetting...' : 'Reset Demo Data'}
          </button>
        </div>
      </div>

      {/* Main Layout */}
      <div className="main-layout">
        <div className="top-header">
          <div className="header-title">
            <h2>{currentPage}</h2>
            <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
              AI-powered recovery orchestration with policy-controlled execution
            </p>
          </div>
          <div className="header-actions" style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <button 
              className="btn btn-primary" 
              style={{ 
                background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
                boxShadow: '0 4px 12px rgba(99, 102, 241, 0.25)',
                fontWeight: '600',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }} 
              onClick={() => setIsCustomCaseModalOpen(true)}
            >
              <Plus size={16} />
              Feed Custom Revenue
            </button>
            <span style={{
              fontSize: '11px',
              fontWeight: '700',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              backgroundColor: 'rgba(244, 63, 94, 0.12)',
              color: '#fb7185',
              padding: '6px 12px',
              borderRadius: '6px',
              border: '1px solid rgba(244, 63, 94, 0.2)'
            }}>
              Demo / Simulation
            </span>
            <button className="btn btn-secondary" onClick={() => fetchData()} disabled={loading}>
              <RefreshCw size={16} />
              Sync
            </button>
          </div>
        </div>

        {/* Page Content */}
        <div className="page-container">
          {error && (
            <div style={{
              backgroundColor: 'var(--accent-rose-opaque)',
              color: 'var(--accent-rose)',
              padding: '16px',
              borderRadius: '8px',
              border: '1px solid var(--accent-rose)',
              marginBottom: '24px',
              display: 'flex',
              alignItems: 'center',
              gap: '12px'
            }}>
              <AlertTriangle size={20} />
              <span>{error}</span>
            </div>
          )}

          {loading ? (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '300px', flexDirection: 'column', gap: '16px' }}>
              <RefreshCw className="animate-spin" size={32} style={{ color: 'var(--accent-indigo)', animation: 'spin 1.5s linear infinite' }} />
              <span style={{ color: 'var(--text-secondary)' }}>
                {processingText || 'Loading RecoverAI metrics...'}
              </span>
            </div>
          ) : (
            <>
              {/* OVERVIEW DASHBOARD */}
              {currentPage === 'Overview' && (
                <div>
                  {/* Judge Mode & Guided Walkthrough */}
                  <div className="panel" style={{ border: '2px dashed var(--accent-indigo)', background: 'rgba(99, 102, 241, 0.04)', padding: '20px', marginBottom: '24px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <ShieldAlert size={20} style={{ color: 'var(--accent-indigo)' }} />
                        <span style={{ fontWeight: '800', fontSize: '15px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--accent-indigo)' }}>
                          Judge Mode & Guided Walkthrough
                        </span>
                      </div>
                      <span style={{ fontSize: '11px', fontWeight: 'bold', backgroundColor: 'var(--accent-indigo)', color: 'white', padding: '2px 8px', borderRadius: '4px' }}>
                        5-MIN DEMO PATH
                      </span>
                    </div>
                    
                    <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.5', marginBottom: '16px' }}>
                      RecoverAI aligns AI strategy recommendation with deterministic policy boundaries. Below are the key showcase scenarios prepared for your assessment. Trigger and inspect each recovery execution path deterministically.
                    </p>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '16px', marginBottom: '20px' }}>
                      {/* Scenario A Card */}
                      <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                        <div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                            <span style={{ fontSize: '10px', fontWeight: 'bold', color: 'var(--accent-emerald)', textTransform: 'uppercase' }}>SCENARIO A</span>
                            <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Auto Recovery</span>
                          </div>
                          <div style={{ fontWeight: 'bold', fontSize: '14px', color: 'var(--text-primary)', marginBottom: '6px' }}>Successful Recovery</div>
                          <p style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: '1.4', marginBottom: '12px' }}>
                            `REC-DEMO-001` represents a high-value customer checkout abandonment. AI recommends SMART_RETRY, policy approves, execution succeeds, and revenue increases.
                          </p>
                        </div>
                        <div style={{ display: 'flex', gap: '8px' }}>
                          <button className="btn btn-secondary" style={{ fontSize: '11px', padding: '4px 8px', width: '100%', justifyContent: 'center' }} onClick={() => handleOpenCaseDetails('REC-DEMO-001')}>
                            <Eye size={12} /> Inspect Scenario
                          </button>
                        </div>
                      </div>

                      {/* Scenario B Card */}
                      <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                        <div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                            <span style={{ fontSize: '10px', fontWeight: 'bold', color: 'var(--accent-amber)', textTransform: 'uppercase' }}>SCENARIO B</span>
                            <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>HITL Pipeline</span>
                          </div>
                          <div style={{ fontWeight: 'bold', fontSize: '14px', color: 'var(--text-primary)', marginBottom: '6px' }}>Human Override Queue</div>
                          <p style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: '1.4', marginBottom: '12px' }}>
                            `REC-DEMO-003` is a high-value transaction. Policy halts automatic execution due to amount limits, routing to review queue. Human revalidates and approves.
                          </p>
                        </div>
                        <div style={{ display: 'flex', gap: '8px' }}>
                          <button className="btn btn-secondary" style={{ fontSize: '11px', padding: '4px 8px', width: '100%', justifyContent: 'center' }} onClick={() => setCurrentPage('HumanReview')}>
                            <UserCheck size={12} /> Review Queue
                          </button>
                        </div>
                      </div>

                      {/* Scenario C Card */}
                      <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                        <div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                            <span style={{ fontSize: '10px', fontWeight: 'bold', color: 'var(--accent-rose)', textTransform: 'uppercase' }}>SCENARIO C</span>
                            <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>STOP Safeguard</span>
                          </div>
                          <div style={{ fontWeight: 'bold', fontSize: '14px', color: 'var(--text-primary)', marginBottom: '6px' }}>Deterministic Policy Stop</div>
                          <p style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: '1.4', marginBottom: '12px' }}>
                            `REC-DEMO-004` represents repeated payment abandonment. Policy stops further attempts immediately (MAX_RETRIES_EXCEEDED), preventing customer spam.
                          </p>
                        </div>
                        <div style={{ display: 'flex', gap: '8px' }}>
                          <button className="btn btn-secondary" style={{ fontSize: '11px', padding: '4px 8px', width: '100%', justifyContent: 'center' }} onClick={() => handleOpenCaseDetails('REC-DEMO-004')}>
                            <Eye size={12} /> Inspect Scenario
                          </button>
                        </div>
                      </div>

                      {/* Scenario D Card */}
                      <div style={{ backgroundColor: 'var(--bg-secondary)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-color)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                        <div>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                            <span style={{ fontSize: '10px', fontWeight: 'bold', color: 'var(--accent-indigo)', textTransform: 'uppercase' }}>SCENARIO D</span>
                            <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Scheduled Delay</span>
                          </div>
                          <div style={{ fontWeight: 'bold', fontSize: '14px', color: 'var(--text-primary)', marginBottom: '6px' }}>Wait & Retry Trigger</div>
                          <p style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: '1.4', marginBottom: '12px' }}>
                            `REC-DEMO-001` configured to WAIT_AND_RETRY. When processed, it transitions to `SCHEDULED`, enabling manual retry triggering and revalidation.
                          </p>
                        </div>
                        <div style={{ display: 'flex', gap: '8px' }}>
                          <button className="btn btn-secondary" style={{ fontSize: '11px', padding: '4px 8px', width: '100%', justifyContent: 'center' }} onClick={() => handleOpenCaseDetails('REC-DEMO-001')}>
                            <Eye size={12} /> Inspect Scenario
                          </button>
                        </div>
                      </div>
                    </div>

                    {/* Compact Architecture Block */}
                    <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '16px', display: 'flex', flexWrap: 'wrap', gap: '12px', alignItems: 'center' }}>
                      <span style={{ fontSize: '11px', fontWeight: 'bold', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                        System Flow Architecture:
                      </span>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', fontSize: '11px' }}>
                        <span style={{ padding: '2px 6px', backgroundColor: 'var(--bg-tertiary)', borderRadius: '4px', border: '1px solid var(--border-color)' }}>
                          Failed Payment ➔ AI Recommends Strategy ➔ Policy revalidates limits ➔ Execute / HITL / STOP
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Aggregated metrics */}
                  <div className="metrics-grid">
                    <div className="metric-card">
                      <div className="metric-card-header">
                        <span>₹ Recovered Revenue</span>
                        <Coins size={18} className="text-emerald-400" />
                      </div>
                      <div className="metric-card-value" style={{ color: 'var(--accent-emerald)' }}>
                        ₹{overallMetrics.recoveredRevenue.toLocaleString('en-IN')}
                      </div>
                      <div className="metric-card-footer">
                        Actual simulated funds recovered
                      </div>
                    </div>
                    <div className="metric-card">
                      <div className="metric-card-header">
                        <span>Recovery Rate</span>
                        <TrendingUp size={18} className="text-indigo-400" />
                      </div>
                      <div className="metric-card-value">
                        {overallMetrics.recoveryRate}%
                      </div>
                      <div className="metric-card-footer">
                        Percentage of outstanding recovered
                      </div>
                    </div>
                    <div className="metric-card">
                      <div className="metric-card-header">
                        <span>Cases Processed</span>
                        <Receipt size={18} className="text-blue-400" />
                      </div>
                      <div className="metric-card-value">
                        {overallMetrics.processedCases}
                      </div>
                      <div className="metric-card-footer">
                        Excludes terminal case initial counts
                      </div>
                    </div>
                    <div className="metric-card">
                      <div className="metric-card-header">
                        <span>Awaiting Human Review</span>
                        <AlertTriangle size={18} className="text-amber-400" />
                      </div>
                      <div className="metric-card-value" style={{ color: 'var(--accent-amber)' }}>
                        {overallMetrics.pendingReviews}
                      </div>
                      <div className="metric-card-footer">
                        Escalated to human reviewer queue
                      </div>
                    </div>
                  </div>

                  {/* Revenue comparison and Pipeline explanation */}
                  <div className="grid-2">
                    <div className="panel">
                      <div className="panel-header">
                        <span className="panel-title">Revenue Impact Comparison</span>
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '16px', backgroundColor: 'var(--bg-tertiary)', borderRadius: '8px' }}>
                          <div>
                            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>RecoverAI Revenue</div>
                            <div style={{ fontSize: '24px', fontWeight: 'bold', color: 'var(--accent-emerald)', marginTop: '4px' }}>
                              ₹{overallMetrics.recoveredRevenue.toLocaleString('en-IN')}
                            </div>
                          </div>
                          <div>
                            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>Naive Baseline</div>
                            <div style={{ fontSize: '24px', fontWeight: 'bold', color: 'var(--text-muted)', marginTop: '4px' }}>
                              ₹{overallMetrics.baselineRevenue.toLocaleString('en-IN')}
                            </div>
                          </div>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--accent-emerald)' }}>
                          <TrendingUp size={24} />
                          <div>
                            <div style={{ fontWeight: 'bold', fontSize: '16px' }}>
                              +₹{overallMetrics.incrementalRevenue.toLocaleString('en-IN')} Incremental Revenue
                            </div>
                            <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                              Improvement vs simple one-size-fits-all retry baseline
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    <div className="panel">
                      <div className="panel-header">
                        <span className="panel-title">Recovery Pipeline Flow</span>
                      </div>
                      <p style={{ fontSize: '13px', color: 'var(--text-secondary)', lineHeight: '1.5', marginBottom: '16px' }}>
                        Failed payments undergo full failure diagnostics and customer engagement analysis before evaluating policy-controlled execution options.
                      </p>
                      <PipelineFlow status="RECOVERED" strategy="SMART_RETRY" policyDecision="APPROVED" />
                    </div>
                  </div>
                </div>
              )}

              {/* RECOVERY CASES PAGE */}
              {currentPage === 'Cases' && (() => {
                // Filter cases
                const filteredCases = cases.filter(c => {
                  if (caseSearch) {
                    const q = caseSearch.toLowerCase();
                    const matchId = c.case_id?.toLowerCase().includes(q);
                    const matchCust = c.payment?.customer?.name?.toLowerCase().includes(q) || c.metadata_json?.customer_name?.toLowerCase().includes(q);
                    const matchStrategy = c.current_strategy?.toLowerCase().includes(q);
                    const matchAmt = c.payment?.amount?.toString().includes(q);
                    if (!matchId && !matchCust && !matchStrategy && !matchAmt) return false;
                  }
                  if (caseStatusFilter === 'PENDING' && c.status !== 'PENDING') return false;
                  if (caseStatusFilter === 'RECOVERED' && c.status !== 'RECOVERED') return false;
                  if (caseStatusFilter === 'HITL' && c.status !== 'WAITING_FOR_APPROVAL' && c.status !== 'ESCALATED' && !c.requires_human_approval) return false;
                  if (caseStatusFilter === 'STOPPED' && c.status !== 'STOPPED' && c.status !== 'BLOCKED') return false;
                  if (caseStatusFilter === 'CUSTOM' && !c.case_id?.startsWith('REC-USER-')) return false;
                  
                  if (caseFailureFilter !== 'ALL') {
                    if (c.payment?.failure_code !== caseFailureFilter) return false;
                  }
                  return true;
                });

                const totalCasePages = Math.max(1, Math.ceil(filteredCases.length / casePageSize));
                const paginatedCases = filteredCases.slice((casePage - 1) * casePageSize, casePage * casePageSize);

                // Counts for filters
                const pendingCount = cases.filter(c => c.status === 'PENDING').length;
                const hitlCount = cases.filter(c => c.status === 'WAITING_FOR_APPROVAL' || c.status === 'ESCALATED' || c.requires_human_approval).length;
                const recoveredCount = cases.filter(c => c.status === 'RECOVERED').length;
                const stoppedCount = cases.filter(c => c.status === 'STOPPED' || c.status === 'BLOCKED').length;
                const customCount = cases.filter(c => c.case_id?.startsWith('REC-USER-')).length;

                // Selected totals
                const selectedCasesList = cases.filter(c => selectedCaseIds.has(c.case_id));
                const selectedTotalAmount = selectedCasesList.reduce((acc, c) => acc + (c.payment?.amount || 0), 0);

                return (
                  <div className="panel" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    
                    {/* Header with Title & Action Buttons */}
                    <div className="panel-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
                      <div>
                        <span className="panel-title">Recovery Portfolio Cases ({filteredCases.length} / {cases.length})</span>
                      </div>
                      <div style={{ display: 'flex', gap: '10px' }}>
                        {selectedCaseIds.size > 0 && (
                          <button 
                            className="btn btn-primary" 
                            style={{ backgroundColor: 'var(--accent-amber)', borderColor: 'var(--accent-amber)', color: 'black', fontWeight: 'bold' }}
                            onClick={() => setIsBatchBuilderOpen(true)}
                          >
                            <Layers size={16} />
                            Create Custom Batch ({selectedCaseIds.size})
                          </button>
                        )}
                        <button 
                          className="btn btn-primary" 
                          style={{ display: 'flex', alignItems: 'center', gap: '8px' }}
                          onClick={() => setIsCustomCaseModalOpen(true)}
                        >
                          <Plus size={16} />
                          Feed Custom Revenue
                        </button>
                      </div>
                    </div>

                    {/* Search & Filter Toolbar */}
                    <div style={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: '12px',
                      alignItems: 'center',
                      backgroundColor: 'var(--bg-tertiary)',
                      padding: '12px 16px',
                      borderRadius: '8px',
                      border: '1px solid var(--border-color)'
                    }}>
                      {/* Search Bar */}
                      <div style={{ position: 'relative', flexGrow: 1, minWidth: '220px' }}>
                        <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                        <input
                          type="text"
                          placeholder="Search Case ID, Customer, Strategy, or Amount..."
                          value={caseSearch}
                          onChange={(e) => { setCaseSearch(e.target.value); setCasePage(1); }}
                          style={{ paddingLeft: '36px', height: '38px', fontSize: '13px' }}
                        />
                        {caseSearch && (
                          <button 
                            onClick={() => setCaseSearch('')} 
                            style={{ position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)', background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
                          >
                            <X size={14} />
                          </button>
                        )}
                      </div>

                      {/* Failure Category Filter */}
                      <div style={{ minWidth: '180px' }}>
                        <select
                          value={caseFailureFilter}
                          onChange={(e) => { setCaseFailureFilter(e.target.value); setCasePage(1); }}
                          style={{ height: '38px', fontSize: '13px' }}
                        >
                          <option value="ALL">All Failure Categories</option>
                          <option value="TEMPORARY_BANK_FAILURE">Bank Network Failures</option>
                          <option value="INSUFFICIENT_FUNDS">Insufficient Funds</option>
                          <option value="PAYMENT_ABANDONED">Payment Abandonment</option>
                          <option value="AUTHENTICATION_FAILED">Authentication / 3DS</option>
                          <option value="EXPIRED_PAYMENT_METHOD">Expired Payment Method</option>
                          <option value="REPEATED_FAILURE">Repeated Declines</option>
                          <option value="UNKNOWN_FAILURE">Unknown Failures</option>
                        </select>
                      </div>

                      {/* Page Size Selector */}
                      <div style={{ width: '120px' }}>
                        <select
                          value={casePageSize}
                          onChange={(e) => { setCasePageSize(parseInt(e.target.value, 10)); setCasePage(1); }}
                          style={{ height: '38px', fontSize: '13px' }}
                        >
                          <option value={10}>10 per page</option>
                          <option value={25}>25 per page</option>
                          <option value={50}>50 per page</option>
                        </select>
                      </div>
                    </div>

                    {/* Filter Pills */}
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', alignItems: 'center' }}>
                      <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: '600', marginRight: '4px' }}>Status:</span>
                      {[
                        { id: 'ALL', label: `All (${cases.length})` },
                        { id: 'PENDING', label: `Pending (${pendingCount})` },
                        { id: 'HITL', label: `Requires Review (${hitlCount})` },
                        { id: 'RECOVERED', label: `Recovered (${recoveredCount})` },
                        { id: 'STOPPED', label: `Stopped / Blocked (${stoppedCount})` },
                        { id: 'CUSTOM', label: `Custom Feed (${customCount})` },
                      ].map(tab => (
                        <button
                          key={tab.id}
                          onClick={() => { setCaseStatusFilter(tab.id); setCasePage(1); }}
                          style={{
                            padding: '6px 12px',
                            borderRadius: '20px',
                            fontSize: '12px',
                            fontWeight: '600',
                            border: '1px solid',
                            cursor: 'pointer',
                            transition: 'all 0.2s',
                            backgroundColor: caseStatusFilter === tab.id ? 'var(--accent-indigo)' : 'var(--bg-tertiary)',
                            borderColor: caseStatusFilter === tab.id ? 'var(--accent-indigo)' : 'var(--border-color)',
                            color: caseStatusFilter === tab.id ? '#ffffff' : 'var(--text-secondary)'
                          }}
                        >
                          {tab.label}
                        </button>
                      ))}
                    </div>

                    {/* Floating Selection Bar */}
                    {selectedCaseIds.size > 0 && (
                      <div style={{
                        backgroundColor: 'rgba(99, 102, 241, 0.15)',
                        border: '1px solid var(--accent-indigo)',
                        borderRadius: '8px',
                        padding: '10px 16px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        gap: '12px'
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px' }}>
                          <CheckSquare size={16} className="text-indigo-400" />
                          <span>Selected <strong>{selectedCaseIds.size} cases</strong> totaling <strong>₹{selectedTotalAmount.toLocaleString('en-IN')}</strong></span>
                        </div>
                        <div style={{ display: 'flex', gap: '8px' }}>
                          <button 
                            className="btn btn-primary" 
                            style={{ padding: '6px 12px', fontSize: '12px' }}
                            onClick={() => setIsBatchBuilderOpen(true)}
                          >
                            <Layers size={14} />
                            Build Custom Batch
                          </button>
                          <button 
                            className="btn btn-secondary" 
                            style={{ padding: '6px 12px', fontSize: '12px' }}
                            onClick={() => setSelectedCaseIds(new Set())}
                          >
                            Clear Selection
                          </button>
                        </div>
                      </div>
                    )}

                    {/* Table View */}
                    <div className="table-wrapper">
                      <table>
                        <thead>
                          <tr>
                            <th style={{ width: '40px', textAlign: 'center' }}>
                              <input
                                type="checkbox"
                                onChange={handleSelectAllVisibleCases}
                                checked={paginatedCases.length > 0 && paginatedCases.filter(c => c.status !== 'RECOVERED' && c.status !== 'STOPPED').every(c => selectedCaseIds.has(c.case_id))}
                                style={{ width: 'auto', cursor: 'pointer' }}
                              />
                            </th>
                            <th>Case ID</th>
                            <th>Payment Amount</th>
                            <th>Strategy</th>
                            <th>Policy Decision</th>
                            <th>Final Status</th>
                            <th>Recovered Amount</th>
                            <th>Actions</th>
                          </tr>
                        </thead>
                        <tbody>
                          {paginatedCases.length === 0 ? (
                            <tr>
                              <td colSpan={8} style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                                No recovery cases found matching your search and filter criteria.
                              </td>
                            </tr>
                          ) : (
                            paginatedCases.map((c) => {
                              const isSelected = selectedCaseIds.has(c.case_id);
                              const isEligible = c.status !== 'RECOVERED' && c.status !== 'STOPPED';
                              return (
                                <tr key={c.case_id} style={{ backgroundColor: isSelected ? 'rgba(99, 102, 241, 0.08)' : 'inherit' }}>
                                  <td style={{ textAlign: 'center' }}>
                                    <input
                                      type="checkbox"
                                      disabled={!isEligible}
                                      checked={isSelected}
                                      onChange={() => handleToggleSelectCase(c.case_id)}
                                      style={{ width: 'auto', cursor: isEligible ? 'pointer' : 'not-allowed' }}
                                    />
                                  </td>
                                  <td style={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    {c.case_id}
                                    {['REC-DEMO-001', 'REC-DEMO-002', 'REC-DEMO-003', 'REC-DEMO-004', 'REC-DEMO-005'].includes(c.case_id) && (
                                      <span style={{
                                        fontSize: '10px',
                                        fontWeight: 'bold',
                                        backgroundColor: 'rgba(99, 102, 241, 0.12)',
                                        color: 'var(--accent-indigo)',
                                        padding: '2px 6px',
                                        borderRadius: '4px',
                                        textTransform: 'uppercase',
                                        border: '1px solid rgba(99, 102, 241, 0.2)'
                                      }}>
                                        Showcase Scenario
                                      </span>
                                    )}
                                    {c.case_id.startsWith('REC-USER-') && (
                                      <span style={{
                                        fontSize: '10px',
                                        fontWeight: 'bold',
                                        backgroundColor: 'rgba(16, 185, 129, 0.12)',
                                        color: 'var(--accent-emerald)',
                                        padding: '2px 6px',
                                        borderRadius: '4px',
                                        textTransform: 'uppercase',
                                        border: '1px solid rgba(16, 185, 129, 0.2)'
                                      }}>
                                        Custom Feed
                                      </span>
                                    )}
                                  </td>
                                  <td>₹{c.payment?.amount?.toLocaleString('en-IN') || '0'}</td>
                                  <td>{c.current_strategy || 'PENDING'}</td>
                                  <td>
                                    <StatusBadge status={c.metadata_json?.policy_decision || (c.requires_human_approval ? 'HITL_REQUIRED' : 'APPROVED')} />
                                  </td>
                                  <td>
                                    <StatusBadge status={c.status} />
                                  </td>
                                  <td style={{ color: c.status === 'RECOVERED' ? 'var(--accent-emerald)' : 'inherit' }}>
                                    ₹{c.actions?.find(a => a.status === 'SUCCESS')?.recovered_amount?.toLocaleString('en-IN') || '0'}
                                  </td>
                                  <td>
                                    <button className="btn btn-secondary" onClick={() => handleOpenCaseDetails(c.case_id)}>
                                      <Eye size={14} />
                                      View Details
                                    </button>
                                  </td>
                                </tr>
                              );
                            })
                          )}
                        </tbody>
                      </table>
                    </div>

                    {/* Pagination Bar */}
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '12px 16px',
                      borderTop: '1px solid var(--border-color)',
                      flexWrap: 'wrap',
                      gap: '12px'
                    }}>
                      <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                        Showing {filteredCases.length === 0 ? 0 : (casePage - 1) * casePageSize + 1} to {Math.min(casePage * casePageSize, filteredCases.length)} of {filteredCases.length} cases
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <button
                          className="btn btn-secondary"
                          style={{ padding: '6px 10px' }}
                          disabled={casePage <= 1}
                          onClick={() => setCasePage(prev => Math.max(1, prev - 1))}
                        >
                          <ChevronLeft size={16} />
                          Previous
                        </button>
                        <span style={{ fontSize: '13px', padding: '0 8px', fontWeight: 'bold' }}>
                          Page {casePage} of {totalCasePages}
                        </span>
                        <button
                          className="btn btn-secondary"
                          style={{ padding: '6px 10px' }}
                          disabled={casePage >= totalCasePages}
                          onClick={() => setCasePage(prev => Math.min(totalCasePages, prev + 1))}
                        >
                          Next
                          <ChevronRight size={16} />
                        </button>
                      </div>
                    </div>

                  </div>
                );
              })()}

              {/* HUMAN REVIEW PAGE */}
              {currentPage === 'HumanReview' && (
                <div className="panel">
                  <div className="panel-header">
                    <span className="panel-title">Manual Action Review Queue ({reviews.length})</span>
                  </div>
                  {reviews.length === 0 ? (
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '48px', color: 'var(--text-secondary)', gap: '12px' }}>
                      <CheckCircle size={36} className="text-emerald-400" />
                      <span style={{ fontWeight: '600' }}>Review queue is empty!</span>
                      <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>No recovery cases currently require human approval overrides.</span>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                      {reviews.map((r) => (
                        <div key={r.case_id} style={{
                          backgroundColor: 'var(--bg-tertiary)',
                          border: '1px solid var(--border-color)',
                          borderRadius: '12px',
                          padding: '20px',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          gap: '24px'
                        }}>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', flexGrow: 1 }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                              <span style={{ fontWeight: 'bold', fontSize: '16px' }}>{r.case_id}</span>
                              <span className="badge badge-hitl">Requires Approval</span>
                            </div>
                            <div className="grid-2" style={{ gap: '16px', marginTop: '4px' }}>
                              <div>
                                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Payment Value:</span>
                                <div style={{ fontSize: '14px', fontWeight: 'bold' }}>₹{r.payment_amount.toLocaleString('en-IN')}</div>
                              </div>
                              <div>
                                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Strategy:</span>
                                <div style={{ fontSize: '14px', fontWeight: 'bold' }}>{r.recommended_action}</div>
                              </div>
                              <div>
                                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Triggered Rules:</span>
                                <div style={{ fontSize: '13px', color: 'var(--accent-amber)', fontWeight: '500' }}>
                                  {r.triggered_rules.join(', ')}
                                </div>
                              </div>
                            </div>
                          </div>
                          <div style={{ display: 'flex', gap: '12px', flexShrink: 0 }}>
                            <button className="btn" style={{ borderColor: 'var(--accent-rose)', color: 'var(--accent-rose)' }} onClick={() => handleOpenReview(r.case_id, 'reject')}>
                              <XCircle size={14} />
                              Reject
                            </button>
                            <button className="btn btn-primary" style={{ backgroundColor: 'var(--accent-emerald)', borderColor: 'var(--accent-emerald)' }} onClick={() => handleOpenReview(r.case_id, 'approve')}>
                              <CheckCircle size={14} />
                              Approve
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* BATCHES PAGE */}
              {currentPage === 'Batches' && (
                <div>
                  <div className="panel">
                    <div className="panel-header">
                      <span className="panel-title">Batch Recovery Portfolios ({batches.length})</span>
                      <button className="btn btn-primary" onClick={handleCreateDemoBatch}>
                        <Plus size={16} />
                        Create BATCH-DEMO-001
                      </button>
                    </div>
                    {batches.length === 0 ? (
                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '48px', color: 'var(--text-secondary)', gap: '12px' }}>
                        <Database size={36} className="text-muted" />
                        <span style={{ fontWeight: '600' }}>No recovery batches found</span>
                        <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Click the button above to generate a new portfolio batch.</span>
                      </div>
                    ) : (
                      <div className="table-wrapper">
                        <table>
                          <thead>
                            <tr>
                              <th>Batch ID</th>
                              <th>Batch Name</th>
                              <th>Status</th>
                              <th>Cases</th>
                              <th>Recovered Revenue</th>
                              <th>Expected Value</th>
                              <th>Recovery Rate</th>
                              <th>Actions</th>
                            </tr>
                          </thead>
                          <tbody>
                            {batches.map((b) => (
                              <tr key={b.batch_id}>
                                <td style={{ fontWeight: 'bold' }}>{b.batch_id}</td>
                                <td>{b.batch_name}</td>
                                <td>
                                  <StatusBadge status={b.status} />
                                </td>
                                <td>{b.total_cases}</td>
                                <td style={{ color: 'var(--accent-emerald)', fontWeight: '600' }}>
                                  ₹{b.total_recovered_amount.toLocaleString('en-IN')}
                                </td>
                                <td>₹{b.total_expected_recovery_value.toLocaleString('en-IN')}</td>
                                <td>{b.recovery_rate.toFixed(1)}%</td>
                                <td>
                                  <div style={{ display: 'flex', gap: '8px' }}>
                                    {b.status === 'PENDING' && (
                                      <button className="btn btn-primary" style={{ padding: '6px 12px' }} onClick={() => handleRunBatch(b.batch_id)} disabled={loading}>
                                        <Play size={14} />
                                        {loading && processingText.includes(b.batch_id) ? 'Running...' : 'Run Batch'}
                                      </button>
                                    )}
                                    {(b.status === 'COMPLETED' || b.status === 'COMPLETED_WITH_ERRORS') && (
                                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Executed</span>
                                        <button className="btn btn-secondary" style={{ padding: '4px 8px', fontSize: '11px', display: 'flex', alignItems: 'center', gap: '4px' }} onClick={() => handleOpenBatchImpact(b.batch_id)}>
                                          <Eye size={12} />
                                          View Impact
                                        </button>
                                      </div>
                                    )}
                                  </div>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* POLICY STUDIO PAGE */}
              {currentPage === 'PolicyStudio' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                  
                  {/* Header */}
                  <div className="panel" style={{ padding: '20px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <Sliders size={22} className="text-indigo-400" />
                          <h3 style={{ fontSize: '20px', fontWeight: 'bold' }}>Interactive Policy Rules Studio</h3>
                        </div>
                        <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                          Configure deterministic risk thresholds, retry barriers, and HITL safety triggers in real-time.
                        </p>
                      </div>
                      <div style={{ display: 'flex', gap: '10px' }}>
                        <button className="btn btn-secondary" onClick={handleResetPolicy} disabled={loading}>
                          <RotateCcw size={16} />
                          Reset to Defaults
                        </button>
                        <button 
                          className="btn btn-primary" 
                          style={{ background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)', fontWeight: 'bold' }} 
                          onClick={handleSavePolicy} 
                          disabled={loading}
                        >
                          <Save size={16} />
                          Save Policy Configuration
                        </button>
                      </div>
                    </div>

                    {policyFeedback && (
                      <div style={{
                        marginTop: '16px',
                        padding: '12px 16px',
                        borderRadius: '8px',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px',
                        backgroundColor: policyFeedback.type === 'success' ? 'var(--accent-emerald-opaque)' : 'var(--accent-rose-opaque)',
                        border: `1px solid ${policyFeedback.type === 'success' ? 'var(--accent-emerald)' : 'var(--accent-rose)'}`,
                        color: policyFeedback.type === 'success' ? 'var(--accent-emerald)' : 'var(--accent-rose)',
                        fontSize: '13px',
                        fontWeight: '600'
                      }}>
                        {policyFeedback.type === 'success' ? <CheckCircle size={18} /> : <AlertTriangle size={18} />}
                        <span>{policyFeedback.message}</span>
                      </div>
                    )}
                  </div>

                  {/* Policy Cards Grid */}
                  <div className="grid-2" style={{ gap: '20px' }}>
                    
                    {/* Card 1: High-Value HITL Threshold */}
                    <div className="panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 'bold', fontSize: '15px' }}>
                          <ShieldAlert size={18} style={{ color: 'var(--accent-amber)' }} />
                          High-Value HITL Escalation Threshold
                        </div>
                        <span style={{ fontSize: '18px', fontWeight: 'bold', color: 'var(--accent-amber)' }}>
                          ₹{policyConfig.HITL_AMOUNT_THRESHOLD?.toLocaleString('en-IN')}
                        </span>
                      </div>
                      <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                        Transactions equal to or exceeding this value are automatically blocked from automated execution and routed to the Human Review queue.
                      </p>
                      <input
                        type="range"
                        min="5000"
                        max="200000"
                        step="5000"
                        value={policyConfig.HITL_AMOUNT_THRESHOLD}
                        onChange={(e) => setPolicyConfig({ ...policyConfig, HITL_AMOUNT_THRESHOLD: parseFloat(e.target.value) })}
                        style={{ cursor: 'pointer' }}
                      />
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)' }}>
                        <span>₹5,000 (Conservative)</span>
                        <span>₹1,00,000</span>
                        <span>₹2,00,000 (Aggressive)</span>
                      </div>
                    </div>

                    {/* Card 2: Max Retries Allowed */}
                    <div className="panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 'bold', fontSize: '15px' }}>
                          <RotateCcw size={18} style={{ color: 'var(--accent-rose)' }} />
                          Maximum Automated Retries
                        </div>
                        <span style={{ fontSize: '18px', fontWeight: 'bold', color: 'var(--accent-rose)' }}>
                          {policyConfig.MAX_RETRIES} Retries
                        </span>
                      </div>
                      <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                        Hard stop threshold enforcing `MAX_RETRIES_REACHED`. Once reached, all automated retries are permanently blocked to prevent card network penalties.
                      </p>
                      <input
                        type="range"
                        min="1"
                        max="5"
                        step="1"
                        value={policyConfig.MAX_RETRIES}
                        onChange={(e) => setPolicyConfig({ ...policyConfig, MAX_RETRIES: parseInt(e.target.value, 10) })}
                        style={{ cursor: 'pointer' }}
                      />
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)' }}>
                        <span>1 Attempt (Strict)</span>
                        <span>3 Attempts (Standard)</span>
                        <span>5 Attempts (Max)</span>
                      </div>
                    </div>

                    {/* Card 3: Maximum Customer Reminders */}
                    <div className="panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 'bold', fontSize: '15px' }}>
                          <Coins size={18} style={{ color: 'var(--accent-indigo)' }} />
                          Maximum Customer Reminders
                        </div>
                        <span style={{ fontSize: '18px', fontWeight: 'bold', color: 'var(--accent-indigo)' }}>
                          {policyConfig.MAX_REMINDERS} Reminders
                        </span>
                      </div>
                      <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                        Caps WhatsApp, Email, and SMS payment link notifications to avoid spamming the customer.
                      </p>
                      <input
                        type="range"
                        min="1"
                        max="5"
                        step="1"
                        value={policyConfig.MAX_REMINDERS}
                        onChange={(e) => setPolicyConfig({ ...policyConfig, MAX_REMINDERS: parseInt(e.target.value, 10) })}
                        style={{ cursor: 'pointer' }}
                      />
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)' }}>
                        <span>1 Reminder</span>
                        <span>3 Reminders</span>
                        <span>5 Reminders</span>
                      </div>
                    </div>

                    {/* Card 4: Minimum Diagnosis Confidence */}
                    <div className="panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 'bold', fontSize: '15px' }}>
                          <AlertTriangle size={18} style={{ color: 'var(--accent-emerald)' }} />
                          Diagnosis Confidence Barrier
                        </div>
                        <span style={{ fontSize: '18px', fontWeight: 'bold', color: 'var(--accent-emerald)' }}>
                          {(policyConfig.HITL_CONFIDENCE_THRESHOLD * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p style={{ fontSize: '12px', color: 'var(--text-secondary)', lineHeight: '1.4' }}>
                        If the Diagnosis Agent cannot identify the failure root cause with confidence above this barrier, the case escalates to HITL.
                      </p>
                      <input
                        type="range"
                        min="0.50"
                        max="0.95"
                        step="0.05"
                        value={policyConfig.HITL_CONFIDENCE_THRESHOLD}
                        onChange={(e) => setPolicyConfig({ ...policyConfig, HITL_CONFIDENCE_THRESHOLD: parseFloat(e.target.value) })}
                        style={{ cursor: 'pointer' }}
                      />
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)' }}>
                        <span>50% (Permissive)</span>
                        <span>70% (Default)</span>
                        <span>95% (High Certainty)</span>
                      </div>
                    </div>

                  </div>

                  {/* Live Policy Simulation Sandbox */}
                  <div className="panel" style={{ padding: '20px' }}>
                    <div style={{ fontWeight: 'bold', fontSize: '16px', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <Zap size={18} style={{ color: 'var(--accent-amber)' }} />
                      Live Policy Sandbox Tester
                    </div>
                    <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '16px' }}>
                      Test how current configured thresholds will evaluate a sample transaction amount without saving.
                    </p>

                    <div className="grid-3" style={{ gap: '16px', alignItems: 'flex-end' }}>
                      <div className="form-group">
                        <label>Simulated Amount (₹)</label>
                        <input
                          type="number"
                          value={testPolicyAmount}
                          onChange={(e) => setTestPolicyAmount(parseFloat(e.target.value) || 0)}
                        />
                      </div>
                      <div className="form-group">
                        <label>Simulated Retries</label>
                        <input
                          type="number"
                          value={testPolicyRetries}
                          onChange={(e) => setTestPolicyRetries(parseInt(e.target.value, 10) || 0)}
                        />
                      </div>
                      <div>
                        {(() => {
                          const isHighValue = testPolicyAmount >= policyConfig.HITL_AMOUNT_THRESHOLD;
                          const isMaxRetries = testPolicyRetries >= policyConfig.MAX_RETRIES;
                          
                          let decision = 'APPROVED';
                          let badgeClass = 'badge-approved';
                          let note = 'Transaction within automated execution safety boundaries.';

                          if (isMaxRetries) {
                            decision = 'BLOCKED (STOPPED)';
                            badgeClass = 'badge-stopped';
                            note = `Violates MAX_RETRIES limit (${policyConfig.MAX_RETRIES}). Automated execution halted.`;
                          } else if (isHighValue) {
                            decision = 'HITL_REQUIRED';
                            badgeClass = 'badge-hitl';
                            note = `Exceeds High-Value threshold (₹${policyConfig.HITL_AMOUNT_THRESHOLD.toLocaleString('en-IN')}). Routed to human review.`;
                          }

                          return (
                            <div style={{ backgroundColor: 'var(--bg-tertiary)', padding: '12px', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Outcome with Active Rules:</div>
                              <div style={{ fontSize: '15px', fontWeight: 'bold', marginTop: '2px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                                <span className={`badge ${badgeClass}`}>{decision}</span>
                              </div>
                              <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                                {note}
                              </div>
                            </div>
                          );
                        })()}
                      </div>
                    </div>
                  </div>

                </div>
              )}

              {/* AUDIT PAGE */}
              {currentPage === 'Audit' && (() => {
                const filteredAudit = auditEvents.filter(event => {
                  if (auditSearch) {
                    const q = auditSearch.toLowerCase();
                    const matchCase = event.case_id?.toLowerCase().includes(q);
                    const matchEvent = event.event_type?.toLowerCase().includes(q);
                    const matchActor = event.actor_name?.toLowerCase().includes(q);
                    const matchSumm = event.decision_summary?.toLowerCase().includes(q);
                    if (!matchCase && !matchEvent && !matchActor && !matchSumm) return false;
                  }
                  if (auditActorFilter !== 'ALL' && event.actor_type !== auditActorFilter) return false;
                  return true;
                });

                const totalAuditPages = Math.max(1, Math.ceil(filteredAudit.length / auditPageSize));
                const paginatedAudit = filteredAudit.slice((auditPage - 1) * auditPageSize, auditPage * auditPageSize);

                return (
                  <div className="panel" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                    <div className="panel-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
                      <span className="panel-title">System Audit Log Trail ({filteredAudit.length} / {auditEvents.length})</span>
                      <button className="btn btn-secondary" onClick={() => fetchAuditEvents()} disabled={loading}>
                        <RefreshCw size={14} />
                        Refresh Logs
                      </button>
                    </div>

                    {/* Audit Search Toolbar */}
                    <div style={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: '12px',
                      alignItems: 'center',
                      backgroundColor: 'var(--bg-tertiary)',
                      padding: '12px 16px',
                      borderRadius: '8px',
                      border: '1px solid var(--border-color)'
                    }}>
                      <div style={{ position: 'relative', flexGrow: 1, minWidth: '220px' }}>
                        <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
                        <input
                          type="text"
                          placeholder="Search Audit Trail by Case ID, Event, Actor, or Summary..."
                          value={auditSearch}
                          onChange={(e) => { setAuditSearch(e.target.value); setAuditPage(1); }}
                          style={{ paddingLeft: '36px', height: '38px', fontSize: '13px' }}
                        />
                      </div>

                      <div style={{ minWidth: '160px' }}>
                        <select
                          value={auditActorFilter}
                          onChange={(e) => { setAuditActorFilter(e.target.value); setAuditPage(1); }}
                          style={{ height: '38px', fontSize: '13px' }}
                        >
                          <option value="ALL">All Actors</option>
                          <option value="AGENT">Agents</option>
                          <option value="POLICY_ENGINE">Policy Engine</option>
                          <option value="HUMAN">Human Reviewers</option>
                          <option value="SYSTEM">System</option>
                          <option value="USER">User Intake</option>
                        </select>
                      </div>
                    </div>

                    <div className="table-wrapper">
                      <table>
                        <thead>
                          <tr>
                            <th>Timestamp</th>
                            <th>Case ID</th>
                            <th>Event Type</th>
                            <th>Actor</th>
                            <th>Summary</th>
                            <th>Metadata</th>
                          </tr>
                        </thead>
                        <tbody>
                          {paginatedAudit.length === 0 ? (
                            <tr>
                              <td colSpan={6} style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                                No audit records found matching your search.
                              </td>
                            </tr>
                          ) : (
                            paginatedAudit.map((event) => (
                              <React.Fragment key={event.audit_id}>
                                <tr>
                                  <td style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                                    {formatDate(event.timestamp)}
                                  </td>
                                  <td style={{ fontWeight: 'bold' }}>{event.case_id}</td>
                                  <td>
                                    <StatusBadge status={event.event_type} />
                                  </td>
                                  <td>
                                    <span className={`badge ${event.actor_type === 'HUMAN' ? 'badge-hitl' : 'badge-system'}`}>
                                      {event.actor_name}
                                    </span>
                                  </td>
                                  <td>{event.decision_summary}</td>
                                  <td>
                                    {event.metadata_json && Object.keys(event.metadata_json).length > 0 && (
                                      <button className="btn btn-secondary" style={{ padding: '4px 8px', fontSize: '12px' }} onClick={() => setExpandedEventId(expandedEventId === event.audit_id ? null : event.audit_id)}>
                                        {expandedEventId === event.audit_id ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                                      </button>
                                    )}
                                  </td>
                                </tr>
                                {expandedEventId === event.audit_id && (
                                  <tr>
                                    <td colSpan={6} style={{ backgroundColor: 'rgba(0,0,0,0.2)', padding: '16px' }}>
                                      <pre style={{ fontSize: '11px', margin: 0, overflowX: 'auto' }}>
                                        {JSON.stringify(event.metadata_json, null, 2)}
                                      </pre>
                                    </td>
                                  </tr>
                                )}
                              </React.Fragment>
                            ))
                          )}
                        </tbody>
                      </table>
                    </div>

                    {/* Audit Pagination */}
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '12px 16px',
                      borderTop: '1px solid var(--border-color)',
                      flexWrap: 'wrap',
                      gap: '12px'
                    }}>
                      <div style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                        Showing {filteredAudit.length === 0 ? 0 : (auditPage - 1) * auditPageSize + 1} to {Math.min(auditPage * auditPageSize, filteredAudit.length)} of {filteredAudit.length} events
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <button
                          className="btn btn-secondary"
                          style={{ padding: '6px 10px' }}
                          disabled={auditPage <= 1}
                          onClick={() => setAuditPage(prev => Math.max(1, prev - 1))}
                        >
                          <ChevronLeft size={16} />
                          Previous
                        </button>
                        <span style={{ fontSize: '13px', padding: '0 8px', fontWeight: 'bold' }}>
                          Page {auditPage} of {totalAuditPages}
                        </span>
                        <button
                          className="btn btn-secondary"
                          style={{ padding: '6px 10px' }}
                          disabled={auditPage >= totalAuditPages}
                          onClick={() => setAuditPage(prev => Math.min(totalAuditPages, prev + 1))}
                        >
                          Next
                          <ChevronRight size={16} />
                        </button>
                      </div>
                    </div>

                  </div>
                );
              })()}
            </>
          )}
        </div>
      </div>

      {/* Case Details Drawer */}
      {activeCase && (
        <div className="drawer-overlay" onClick={() => setActiveCase(null)}>
          <div className="drawer-content" onClick={(e) => e.stopPropagation()}>
            <div className="drawer-header">
              <div>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Case ID</span>
                <h3 style={{ fontSize: '20px', fontWeight: 'bold' }}>{activeCase.case_id}</h3>
              </div>
              <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                {activeCase.status === 'PENDING' && (
                  <button 
                    className="btn btn-primary" 
                    onClick={() => handleRunCase(activeCase.case_id)}
                    disabled={loading}
                    style={{ backgroundColor: 'var(--accent-emerald)', borderColor: 'var(--accent-emerald)' }}
                  >
                    <Play size={14} />
                    Run Recovery Workflow
                  </button>
                )}
                {activeCase.status === 'SCHEDULED' && (
                  <button 
                    className="btn btn-primary" 
                    onClick={() => handleTriggerScheduled(activeCase.case_id)}
                    disabled={loading}
                    style={{ backgroundColor: 'var(--accent-indigo)', borderColor: 'var(--accent-indigo)' }}
                  >
                    <Play size={14} />
                    Trigger Scheduled Retry
                  </button>
                )}
                <button className="btn btn-secondary" onClick={() => setActiveCase(null)}>Close</button>
              </div>
            </div>
            <div className="drawer-body">
              {/* Failed Payment Profile - What Happened */}
              <div className="panel" style={{ padding: '16px', borderLeft: '4px solid var(--accent-rose)', backgroundColor: 'var(--bg-secondary)' }}>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '8px', fontWeight: 'bold' }}>
                  What Happened? — Failed Payment Profile
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '13px' }}>
                  <div><strong>Case ID:</strong> {activeCase.case_id}</div>
                  <div><strong>Current Status:</strong> <span style={{ fontWeight: 'bold', color: 'var(--text-primary)' }}>{activeCase.status}</span></div>
                  <div><strong>Payment Amount:</strong> ₹{activeCase.payment?.amount?.toLocaleString('en-IN') || '0'}</div>
                  <div><strong>Dispute Status:</strong> {activeCase.payment?.is_disputed ? 'Active Dispute (Safeguarded)' : 'No Dispute'}</div>
                  <div><strong>Failed Reason:</strong> {activeCase.metadata_json?.diagnosis?.failure_category?.replace(/_/g, ' ') || 'Abandoned Checkout'}</div>
                  <div><strong>Retry Count:</strong> {activeCase.payment?.retry_count || 0} / 3 limit</div>
                </div>
              </div>

              {/* Pipeline Step */}
              <div className="panel" style={{ padding: '16px' }}>
                <div style={{ fontSize: '13px', fontWeight: '600', marginBottom: '8px' }}>Execution Path Highlight</div>
                <PipelineFlow
                  status={activeCase.status}
                  strategy={activeCase.current_strategy}
                  policyDecision={activeCase.metadata_json?.policy_decision || (activeCase.requires_human_approval ? 'HITL_REQUIRED' : 'APPROVED')}
                />
              </div>

              {/* AI Agents Analysis Trace */}
              <div className="panel" style={{ padding: '16px' }}>
                <div style={{ fontWeight: 'bold', fontSize: '14px', marginBottom: '12px' }}>AI Agents Analysis Trace</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {/* Diagnosis Agent */}
                  {activeCase.metadata_json?.diagnosis && (
                    <div style={{ borderLeft: '3px solid var(--accent-indigo)', paddingLeft: '12px' }}>
                      <div style={{ fontWeight: 'bold', fontSize: '13px', color: 'var(--text-primary)' }}>Diagnosis Agent</div>
                      <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                        <strong>Conclusion:</strong> {activeCase.metadata_json.diagnosis.failure_category?.replace(/_/g, ' ')}
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                        <strong>Confidence:</strong> {((activeCase.metadata_json.diagnosis.confidence || 0) * 100).toFixed(0)}%
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                        <strong>Evidence:</strong> {activeCase.metadata_json.diagnosis.evidence?.join(', ') || 'None'}
                      </div>
                    </div>
                  )}
                  
                  {/* Customer Profiling Agent */}
                  {activeCase.metadata_json?.customer_analysis && (
                    <div style={{ borderLeft: '3px solid var(--accent-indigo)', paddingLeft: '12px' }}>
                      <div style={{ fontWeight: 'bold', fontSize: '13px', color: 'var(--text-primary)' }}>Customer Profiling Agent</div>
                      <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                        <strong>Segment:</strong> {activeCase.metadata_json.customer_analysis.customer_segment?.replace(/_/g, ' ')}
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                        <strong>Reliability:</strong> {((activeCase.metadata_json.customer_analysis.payment_reliability_score || 0) * 100).toFixed(0)}%
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                        <strong>Quality Score:</strong> {(activeCase.metadata_json.customer_analysis.customer_quality_score || 0).toFixed(1)}/10
                      </div>
                    </div>
                  )}

                  {/* Strategy Agent */}
                  {activeCase.metadata_json?.strategy && (
                    <div style={{ borderLeft: '3px solid var(--accent-indigo)', paddingLeft: '12px' }}>
                      <div style={{ fontWeight: 'bold', fontSize: '13px', color: 'var(--text-primary)' }}>Strategy Agent</div>
                      <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px' }}>
                        <strong>Recommendation:</strong> {activeCase.metadata_json.strategy.recommended_action}
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                        <strong>Expected Recovery Value:</strong> ₹{(activeCase.metadata_json.strategy.expected_recovery_value || 0).toLocaleString('en-IN')}
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                        <strong>Estimated Cost:</strong> ₹{(activeCase.metadata_json.strategy.estimated_action_cost || 0).toLocaleString('en-IN')}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Decision Intelligence Section */}
              {activeCase.explanation_json ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginTop: '16px' }}>
                  <div style={{ fontWeight: 'bold', fontSize: '15px', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px' }}>
                    Decision Intelligence
                  </div>
                  
                  {/* AI vs Policy Visual Flow */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {/* AI Recommendation */}
                    <div className="panel" style={{ padding: '16px', borderLeft: '4px solid var(--accent-indigo)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>AI Intelligence</span>
                        <span style={{ fontSize: '11px', fontWeight: 'bold', color: 'var(--accent-indigo)' }}>RECOMMENDED</span>
                      </div>
                      <div style={{ fontSize: '18px', fontWeight: 'bold', color: 'var(--text-primary)' }}>
                        {activeCase.explanation_json.selected_strategy}
                      </div>
                      <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '6px', marginBottom: 0 }}>
                        {activeCase.metadata_json?.strategy?.reason || "Recommendation derived from failure type diagnostics."}
                      </p>
                    </div>

                    {/* Arrow down connector */}
                    <div style={{ display: 'flex', justifyContent: 'center', color: 'var(--text-muted)', margin: '-4px 0' }}>
                      <ArrowRight size={18} style={{ transform: 'rotate(90deg)' }} />
                    </div>

                    {/* Overridden alert if AI and Policy mismatch */}
                    {activeCase.explanation_json.override_details?.is_overridden && (
                      <div style={{
                        backgroundColor: 'rgba(244, 63, 94, 0.08)',
                        border: '1px solid var(--accent-rose)',
                        borderRadius: '8px',
                        padding: '12px',
                        fontSize: '12px',
                        color: 'var(--accent-rose)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px'
                      }}>
                        <ShieldAlert size={16} />
                        <span>{activeCase.explanation_json.override_details.override_reason}</span>
                      </div>
                    )}

                    {/* Policy Verification */}
                    <div className="panel" style={{
                      padding: '16px',
                      borderLeft: `4px solid ${activeCase.status === 'STOPPED' ? 'var(--accent-rose)' : activeCase.requires_human_approval ? 'var(--accent-amber)' : 'var(--accent-emerald)'}`
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                        <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Deterministic Policy Verification</span>
                        <StatusBadge status={activeCase.explanation_json.policy_explanation.decision} />
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                        {activeCase.explanation_json.policy_explanation.decision === 'APPROVED' ? (
                          <span className="text-emerald-400">✓ Checked dispute status, retry limits, and expected values. Execution authorized.</span>
                        ) : activeCase.explanation_json.policy_explanation.decision === 'HITL_REQUIRED' ? (
                          <span className="text-amber-400">⚠ Automated retry paused. Rules require human override verification.</span>
                        ) : (
                          <span className="text-rose-400">🛑 Automatic retry blocked. Policy engine enforced safety stop rules.</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Primary Signals and Impacts */}
                  <div className="panel" style={{ padding: '16px' }}>
                    <div style={{ fontWeight: 'bold', fontSize: '14px', marginBottom: '12px' }}>Decision Signals & Impacts</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      {activeCase.explanation_json.primary_factors.map((f, idx) => (
                        <div key={idx} style={{ display: 'flex', flexDirection: 'column', gap: '4px', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '8px' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontWeight: '600', fontSize: '13px' }}>{f.factor}</span>
                            <span className={`badge ${f.impact === 'positive' ? 'badge-success' : f.impact === 'negative' ? 'badge-error' : 'badge-system'}`} style={{ fontSize: '9px', padding: '2px 6px' }}>
                              {f.impact.toUpperCase()}
                            </span>
                          </div>
                          <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{f.explanation}</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Counterfactual Panel */}
                  <div className="panel" style={{ padding: '16px', border: '1px dashed var(--border-color)', backgroundColor: 'var(--bg-secondary)' }}>
                    <div style={{ fontWeight: 'bold', fontSize: '13px', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--text-primary)' }}>
                      <RefreshCw size={13} className="text-indigo-400" />
                      What Could Change This Decision? (Counterfactuals)
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      {activeCase.explanation_json.counterfactuals.map((cf, idx) => (
                        <div key={idx} style={{ fontSize: '12px', lineHeight: '1.4' }}>
                          <span style={{ color: 'var(--text-muted)', fontWeight: 'bold' }}>→ {cf.condition}:</span>{' '}
                          <span style={{ color: 'var(--text-secondary)' }}>{cf.alternative_outcome}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Alternatives Considered */}
                  {activeCase.explanation_json.alternatives && activeCase.explanation_json.alternatives.length > 0 && (
                    <div className="panel" style={{ padding: '16px' }}>
                      <div style={{ fontWeight: 'bold', fontSize: '14px', marginBottom: '12px' }}>Alternative Strategies Considered</div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                        {activeCase.explanation_json.alternatives.map((alt, idx) => (
                          <div key={idx} style={{ fontSize: '12px', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '8px' }}>
                            <div style={{ fontWeight: 'bold', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '2px' }}>{alt.strategy}</div>
                            <div style={{ color: 'var(--text-secondary)' }}>{alt.reason_not_selected}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div style={{ color: 'var(--text-secondary)', fontSize: '13px', padding: '16px', textAlign: 'center' }}>
                  Decision explanation will be available after this case is processed.
                </div>
              )}

              {/* Recovery Attempt History */}
              {activeCase.actions && activeCase.actions.length > 0 && (
                <div style={{ marginBottom: '24px' }}>
                  <div style={{ fontWeight: 'bold', fontSize: '15px', marginBottom: '16px' }}>Recovery Attempt History</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {activeCase.actions.sort((a, b) => a.attempt_number - b.attempt_number).map((attempt) => (
                      <div key={attempt.action_id} style={{
                        backgroundColor: 'var(--bg-tertiary)',
                        padding: '16px',
                        borderRadius: '8px',
                        borderLeft: `4px solid ${
                          attempt.status === 'SUCCEEDED' ? 'var(--accent-emerald)' : 
                          attempt.status === 'BLOCKED' ? 'var(--accent-rose)' : 
                          attempt.status === 'FAILED' ? 'var(--accent-rose)' : 
                          'var(--accent-indigo)'
                        }`,
                        fontSize: '13px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '6px'
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontWeight: 'bold', color: 'var(--text-primary)' }}>
                            Attempt #{attempt.attempt_number} — {attempt.action_type ? attempt.action_type.replace(/_/g, ' ') : 'N/A'}
                          </span>
                          <StatusBadge status={attempt.status} />
                        </div>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', color: 'var(--text-secondary)', fontSize: '12px', marginTop: '4px' }}>
                          <div><strong>Policy:</strong> {attempt.policy_decision || 'APPROVED'}</div>
                          <div><strong>Mode:</strong> {attempt.simulation_mode ? 'Simulation' : 'Live'}</div>
                          <div><strong>Requested At:</strong> {formatDate(attempt.requested_at)}</div>
                          <div><strong>Executed At:</strong> {attempt.executed_at ? formatDate(attempt.executed_at) : 'N/A'}</div>
                        </div>
                        {attempt.result && (
                          <div style={{ 
                            marginTop: '6px', 
                            padding: '8px', 
                            backgroundColor: 'rgba(255, 255, 255, 0.02)', 
                            borderRadius: '4px',
                            color: attempt.status === 'SUCCEEDED' ? 'var(--accent-emerald)' : 'var(--text-secondary)',
                            fontSize: '12px',
                            border: '1px solid rgba(255, 255, 255, 0.05)'
                          }}>
                            <strong>Outcome:</strong> {attempt.result}
                            {attempt.status === 'SUCCEEDED' && attempt.recovered_amount > 0 && ` (Recovered: ₹${attempt.recovered_amount.toLocaleString('en-IN')})`}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Case audit timeline */}
              <div>
                <div style={{ fontWeight: 'bold', fontSize: '15px', marginBottom: '16px' }}>Trace Audit Trail Timeline</div>
                <div className="timeline">
                  {activeCaseAudit.map((event) => (
                    <div key={event.audit_id} className="timeline-item">
                      <div className={`timeline-node ${event.event_type.includes('SUCCEEDED') ? 'success' : event.event_type.includes('FAILED') || event.event_type.includes('REJECT') ? 'error' : event.event_type.includes('HITL') ? 'warning' : ''}`} />
                      <div className="timeline-time">{formatDate(event.timestamp)}</div>
                      <div className="timeline-title">{event.event_type.replace(/_/g, ' ')}</div>
                      <div className="timeline-desc">{event.decision_summary}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Human Review Decision Modal */}
      {activeReview && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h3 style={{ fontSize: '16px', fontWeight: 'bold' }}>
                {decisionType === 'approve' ? 'Approve Recovery Action' : 'Reject Recovery Action'}
              </h3>
              <button className="btn btn-secondary" style={{ padding: '4px' }} onClick={() => setActiveReview(null)}>X</button>
            </div>
            
            {revalidationOutcome ? (
              <div className="modal-body">
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px', padding: '16px', textAlign: 'center' }}>
                  {revalidationOutcome.policy_revalidation?.action_allowed ? (
                    <CheckCircle size={48} className="text-emerald-400" />
                  ) : (
                    <ShieldAlert size={48} className="text-rose-400" />
                  )}
                  <h4 style={{ fontWeight: 'bold' }}>
                    {revalidationOutcome.policy_revalidation?.action_allowed 
                      ? 'Decision Processed Successfully' 
                      : 'Execution Halted by Policy Revalidation'}
                  </h4>
                  <p style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                    {revalidationOutcome.policy_revalidation?.action_allowed 
                      ? `Manual override verified and recovery action executed. Final case status: ${revalidationOutcome.final_status}`
                      : 'The Policy Engine detected violations during manual revalidation. Automated retry remains halted.'}
                  </p>
                </div>
              </div>
            ) : (
              <div className="modal-body">
                {activeReview.explanation_json && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '16px' }}>
                    <div style={{ borderLeft: '4px solid var(--accent-indigo)', backgroundColor: 'var(--bg-tertiary)', padding: '12px', borderRadius: '8px' }}>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 'bold' }}>AI Recommendation</div>
                      <div style={{ fontSize: '15px', fontWeight: 'bold', color: 'var(--text-primary)', marginTop: '4px' }}>
                        {activeReview.explanation_json.selected_strategy}
                      </div>
                      <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '4px', margin: 0 }}>
                        {activeReview.strategy?.reason || "Recommendation based on payment diagnostics."}
                      </p>
                    </div>

                    <div style={{ borderLeft: '4px solid var(--accent-rose)', backgroundColor: 'var(--bg-tertiary)', padding: '12px', borderRadius: '8px' }}>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 'bold' }}>Why Automatic Execution Is Blocked</div>
                      <ul style={{ listStyleType: 'disc', paddingLeft: '20px', fontSize: '12px', color: 'var(--accent-amber)', marginTop: '6px', margin: 0, display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        {activeReview.explanation_json.policy_explanation.triggered_rules.map((rule, idx) => (
                          <li key={idx}>
                            {rule === 'HIGH_VALUE_TRANSACTION' ? 'Transaction amount exceeds the automatic execution threshold (Rs. 50,000).' :
                             rule === 'LOW_DIAGNOSIS_CONFIDENCE' ? 'Diagnosis confidence is below the automatic safety threshold (70%).' :
                             rule === 'MULTIPLE_FAILED_ATTEMPTS' ? 'Previous failed attempts exceed the automatic limit.' :
                             rule === 'CUSTOMER_DISPUTE' ? 'Customer dispute detected. Recovery requires manual review overrides.' :
                             rule}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}

                <div style={{
                  backgroundColor: 'var(--bg-tertiary)',
                  padding: '12px',
                  borderRadius: '8px',
                  fontSize: '13px',
                  color: 'var(--text-secondary)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px'
                }}>
                  <ShieldAlert size={18} className="text-amber-400" />
                  <span>
                    <strong>Important Safeguard Reminder</strong>: {decisionType === 'approve' 
                      ? 'Approval does not bypass policy. RecoverAI will revalidate the case before execution.' 
                      : 'Rejection immediately flags the case status as STOPPED and halts execution.'}
                  </span>
                </div>
                
                <div className="form-group">
                  <label>Reason for Decision</label>
                  <textarea
                    rows="3"
                    placeholder="Enter manual reviewer comments..."
                    value={decisionReason}
                    onChange={(e) => setDecisionReason(e.target.value)}
                  />
                </div>
              </div>
            )}

            <div className="modal-footer">
              {revalidationOutcome ? (
                <button className="btn btn-primary" onClick={() => setActiveReview(null)}>
                  Close Queue
                </button>
              ) : (
                <>
                  <button className="btn btn-secondary" onClick={() => setActiveReview(null)} disabled={loading}>Cancel</button>
                  <button
                    className="btn btn-primary"
                    style={{
                      backgroundColor: decisionType === 'approve' ? 'var(--accent-emerald)' : 'var(--accent-rose)',
                      borderColor: decisionType === 'approve' ? 'var(--accent-emerald)' : 'var(--accent-rose)'
                    }}
                    onClick={handleConfirmDecision}
                    disabled={loading}
                  >
                    {loading ? 'Processing...' : (decisionType === 'approve' ? 'Approve Recovery' : 'Stop Case')}
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Custom Case / Personalized Revenue Intake Modal */}
      {isCustomCaseModalOpen && (
        <div className="modal-overlay" onClick={() => setIsCustomCaseModalOpen(false)}>
          <div 
            className="modal-content" 
            style={{ maxWidth: '720px', maxHeight: '90vh', overflowY: 'auto' }} 
            onClick={(e) => e.stopPropagation()}
          >
            <div className="modal-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <div style={{
                  width: '36px',
                  height: '36px',
                  borderRadius: '8px',
                  backgroundColor: 'rgba(99, 102, 241, 0.15)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: 'var(--accent-indigo)'
                }}>
                  <Plus size={20} />
                </div>
                <div>
                  <h3 style={{ fontSize: '18px', fontWeight: 'bold' }}>Feed Custom Failed Payment & Revenue</h3>
                  <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                    Inject personalized transaction amounts, customer profiles, and test AI recovery intelligence.
                  </p>
                </div>
              </div>
              <button 
                className="btn btn-secondary" 
                style={{ padding: '6px' }}
                onClick={() => setIsCustomCaseModalOpen(false)}
              >
                <X size={16} />
              </button>
            </div>

            <form onSubmit={handleCreateCustomCase}>
              <div className="modal-body" style={{ gap: '20px' }}>
                
                {/* 1-Click Quick Presets */}
                <div>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
                    <Sparkles size={14} className="text-indigo-400" />
                    Quick Preset Scenarios
                  </label>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                    {PRESETS.map((preset, i) => (
                      <button
                        key={i}
                        type="button"
                        onClick={() => handleApplyPreset(preset.data)}
                        style={{
                          backgroundColor: 'var(--bg-tertiary)',
                          border: '1px solid var(--border-color)',
                          borderRadius: '8px',
                          padding: '8px 12px',
                          cursor: 'pointer',
                          display: 'flex',
                          flexDirection: 'column',
                          alignItems: 'flex-start',
                          gap: '2px',
                          transition: 'all 0.2s',
                          color: 'var(--text-primary)'
                        }}
                        onMouseEnter={(e) => e.currentTarget.style.borderColor = 'var(--accent-indigo)'}
                        onMouseLeave={(e) => e.currentTarget.style.borderColor = 'var(--border-color)'}
                      >
                        <span style={{ fontSize: '12px', fontWeight: '600' }}>{preset.name}</span>
                        <span style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{preset.badge}</span>
                      </button>
                    ))}
                  </div>
                </div>

                <div className="grid-2" style={{ gap: '20px' }}>
                  
                  {/* Left Column: Payment & Revenue Details */}
                  <div style={{
                    backgroundColor: 'rgba(255, 255, 255, 0.02)',
                    padding: '16px',
                    borderRadius: '12px',
                    border: '1px solid var(--border-color)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '14px'
                  }}>
                    <div style={{ fontSize: '13px', fontWeight: 'bold', color: 'var(--accent-indigo)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Coins size={15} />
                      Payment & Revenue Details
                    </div>

                    <div className="form-group">
                      <label>Personalized Revenue Amount (₹) *</label>
                      <input
                        type="number"
                        min="1"
                        step="any"
                        required
                        value={customCaseForm.amount}
                        onChange={(e) => setCustomCaseForm({ ...customCaseForm, amount: e.target.value })}
                        placeholder="e.g. 15000"
                        style={{ fontSize: '16px', fontWeight: 'bold', color: 'var(--accent-emerald)' }}
                      />
                    </div>

                    <div className="grid-2" style={{ gap: '10px' }}>
                      <div className="form-group">
                        <label>Currency</label>
                        <select
                          value={customCaseForm.currency}
                          onChange={(e) => setCustomCaseForm({ ...customCaseForm, currency: e.target.value })}
                        >
                          <option value="INR">INR (₹)</option>
                          <option value="USD">USD ($)</option>
                          <option value="EUR">EUR (€)</option>
                        </select>
                      </div>
                      <div className="form-group">
                        <label>Payment Method</label>
                        <select
                          value={customCaseForm.payment_method}
                          onChange={(e) => setCustomCaseForm({ ...customCaseForm, payment_method: e.target.value })}
                        >
                          <option value="UPI">UPI</option>
                          <option value="CARD">Card</option>
                          <option value="NETBANKING">Netbanking</option>
                          <option value="WALLET">Wallet</option>
                        </select>
                      </div>
                    </div>

                    <div className="form-group">
                      <label>Failure Reason / Code</label>
                      <select
                        value={customCaseForm.failure_code}
                        onChange={(e) => setCustomCaseForm({ ...customCaseForm, failure_code: e.target.value })}
                      >
                        <option value="TEMPORARY_BANK_FAILURE">TEMPORARY_BANK_FAILURE (Bank network down)</option>
                        <option value="INSUFFICIENT_FUNDS">INSUFFICIENT_FUNDS (Account balance low)</option>
                        <option value="PAYMENT_ABANDONED">PAYMENT_ABANDONED (User dropped off)</option>
                        <option value="AUTHENTICATION_FAILED">AUTHENTICATION_FAILED (OTP / 3DS failure)</option>
                        <option value="EXPIRED_PAYMENT_METHOD">EXPIRED_PAYMENT_METHOD (Card expired)</option>
                        <option value="REPEATED_FAILURE">REPEATED_FAILURE (Persistent decline)</option>
                        <option value="UNKNOWN_FAILURE">UNKNOWN_FAILURE (Gateway anomaly)</option>
                      </select>
                    </div>

                    <div className="grid-2" style={{ gap: '10px' }}>
                      <div className="form-group">
                        <label>Prior Retries</label>
                        <input
                          type="number"
                          min="0"
                          max="10"
                          value={customCaseForm.retry_count}
                          onChange={(e) => setCustomCaseForm({ ...customCaseForm, retry_count: e.target.value })}
                        />
                      </div>
                      <div className="form-group">
                        <label>Prior Reminders</label>
                        <input
                          type="number"
                          min="0"
                          max="10"
                          value={customCaseForm.reminder_count}
                          onChange={(e) => setCustomCaseForm({ ...customCaseForm, reminder_count: e.target.value })}
                        />
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
                      <input
                        type="checkbox"
                        id="is_disputed"
                        checked={customCaseForm.is_disputed}
                        onChange={(e) => setCustomCaseForm({ ...customCaseForm, is_disputed: e.target.checked })}
                        style={{ width: 'auto', cursor: 'pointer' }}
                      />
                      <label htmlFor="is_disputed" style={{ cursor: 'pointer', color: customCaseForm.is_disputed ? 'var(--accent-rose)' : 'var(--text-secondary)' }}>
                        Active Customer Dispute / Chargeback
                      </label>
                    </div>
                  </div>

                  {/* Right Column: Customer Profile & Lifetime Value */}
                  <div style={{
                    backgroundColor: 'rgba(255, 255, 255, 0.02)',
                    padding: '16px',
                    borderRadius: '12px',
                    border: '1px solid var(--border-color)',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '14px'
                  }}>
                    <div style={{ fontSize: '13px', fontWeight: 'bold', color: 'var(--accent-indigo)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <UserPlus size={15} />
                      Customer Revenue Profile
                    </div>

                    <div className="form-group">
                      <label>Customer Name</label>
                      <input
                        type="text"
                        value={customCaseForm.customer_name}
                        onChange={(e) => setCustomCaseForm({ ...customCaseForm, customer_name: e.target.value })}
                        placeholder="e.g. Vikram Malhotra"
                      />
                    </div>

                    <div className="form-group">
                      <label>Customer Segment</label>
                      <select
                        value={customCaseForm.customer_segment}
                        onChange={(e) => setCustomCaseForm({ ...customCaseForm, customer_segment: e.target.value })}
                      >
                        <option value="HIGH_VALUE_RELIABLE">HIGH_VALUE_RELIABLE (VIP / Top 5%)</option>
                        <option value="RELIABLE">RELIABLE (Consistent history)</option>
                        <option value="AVERAGE">AVERAGE (Occasional buyer)</option>
                        <option value="AT_RISK">AT_RISK (Frequent declines)</option>
                        <option value="LOW_ENGAGEMENT">LOW_ENGAGEMENT (Dormant user)</option>
                      </select>
                    </div>

                    <div className="form-group">
                      <label>Customer Lifetime Value (LTV ₹)</label>
                      <input
                        type="number"
                        min="0"
                        step="any"
                        value={customCaseForm.customer_ltv}
                        onChange={(e) => setCustomCaseForm({ ...customCaseForm, customer_ltv: e.target.value })}
                        placeholder="e.g. 150000"
                      />
                    </div>

                    <div className="grid-2" style={{ gap: '10px' }}>
                      <div className="form-group">
                        <label>Successful Payments</label>
                        <input
                          type="number"
                          min="0"
                          value={customCaseForm.successful_payments}
                          onChange={(e) => setCustomCaseForm({ ...customCaseForm, successful_payments: e.target.value })}
                        />
                      </div>
                      <div className="form-group">
                        <label>Failed Payments</label>
                        <input
                          type="number"
                          min="0"
                          value={customCaseForm.failed_payments}
                          onChange={(e) => setCustomCaseForm({ ...customCaseForm, failed_payments: e.target.value })}
                        />
                      </div>
                    </div>

                    <div className="form-group">
                      <label>Engagement Score ({customCaseForm.engagement_score}/10)</label>
                      <input
                        type="range"
                        min="0"
                        max="10"
                        step="0.5"
                        value={customCaseForm.engagement_score}
                        onChange={(e) => setCustomCaseForm({ ...customCaseForm, engagement_score: parseFloat(e.target.value) })}
                        style={{ cursor: 'pointer' }}
                      />
                    </div>
                  </div>
                </div>

                {/* Auto-run Toggle */}
                <div style={{
                  backgroundColor: 'rgba(99, 102, 241, 0.08)',
                  border: '1px solid rgba(99, 102, 241, 0.2)',
                  borderRadius: '8px',
                  padding: '12px 16px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px'
                }}>
                  <input
                    type="checkbox"
                    id="auto_run"
                    checked={customCaseForm.auto_run}
                    onChange={(e) => setCustomCaseForm({ ...customCaseForm, auto_run: e.target.checked })}
                    style={{ width: 'auto', cursor: 'pointer' }}
                  />
                  <label htmlFor="auto_run" style={{ cursor: 'pointer', color: 'var(--text-primary)', fontWeight: '500', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Zap size={15} style={{ color: 'var(--accent-amber)' }} />
                    Immediately run AI Agent Diagnosis, Customer Profiling, Strategy & Policy Pipeline upon creation
                  </label>
                </div>

              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setIsCustomCaseModalOpen(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  style={{
                    background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
                    fontWeight: '600',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}
                  disabled={loading}
                >
                  <Play size={15} />
                  {customCaseForm.auto_run ? 'Create & Orchestrate Recovery' : 'Create Recovery Case'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Custom Batch Builder Modal */}
      {isBatchBuilderOpen && (() => {
        const selectedList = cases.filter(c => selectedCaseIds.has(c.case_id));
        const totalAmount = selectedList.reduce((acc, c) => acc + (c.payment?.amount || 0), 0);

        return (
          <div className="modal-overlay" onClick={() => setIsBatchBuilderOpen(false)}>
            <div 
              className="modal-content" 
              style={{ maxWidth: '640px', maxHeight: '90vh', overflowY: 'auto' }} 
              onClick={(e) => e.stopPropagation()}
            >
              <div className="modal-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{
                    width: '36px',
                    height: '36px',
                    borderRadius: '8px',
                    backgroundColor: 'rgba(245, 158, 11, 0.15)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'var(--accent-amber)'
                  }}>
                    <Layers size={20} />
                  </div>
                  <div>
                    <h3 style={{ fontSize: '18px', fontWeight: 'bold' }}>Custom Batch Portfolio Builder</h3>
                    <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                      Group chosen recovery cases into a custom portfolio for automated batch orchestration.
                    </p>
                  </div>
                </div>
                <button className="btn btn-secondary" style={{ padding: '6px' }} onClick={() => setIsBatchBuilderOpen(false)}>
                  <X size={16} />
                </button>
              </div>

              <div className="modal-body" style={{ gap: '18px' }}>
                <div className="form-group">
                  <label>Portfolio Batch Name *</label>
                  <input
                    type="text"
                    value={customBatchName}
                    onChange={(e) => setCustomBatchName(e.target.value)}
                    placeholder="e.g. Q3 High-Priority Recovery Portfolio"
                    style={{ fontWeight: '600' }}
                  />
                </div>

                {/* Quick Selection Presets */}
                <div>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
                    <Sparkles size={14} className="text-amber-400" />
                    Quick Selection Shortcuts
                  </label>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      style={{ fontSize: '12px', padding: '6px 10px' }}
                      onClick={() => handleSelectCategoryPreset('ALL_ELIGIBLE')}
                    >
                      All Eligible Cases ({cases.filter(c => c.status !== 'RECOVERED' && c.status !== 'STOPPED').length})
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      style={{ fontSize: '12px', padding: '6px 10px' }}
                      onClick={() => handleSelectCategoryPreset('HIGH_VALUE')}
                    >
                      💎 High Value (&gt; ₹{policyConfig.HITL_AMOUNT_THRESHOLD / 1000}k)
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      style={{ fontSize: '12px', padding: '6px 10px' }}
                      onClick={() => handleSelectCategoryPreset('UPI')}
                    >
                      ⚡ All UPI Cases
                    </button>
                    <button
                      type="button"
                      className="btn btn-secondary"
                      style={{ fontSize: '12px', padding: '6px 10px' }}
                      onClick={() => handleSelectCategoryPreset('ABANDONMENT')}
                    >
                      🛒 Abandoned Carts
                    </button>
                  </div>
                </div>

                {/* Selected Summary Card */}
                <div style={{
                  backgroundColor: 'var(--bg-tertiary)',
                  borderRadius: '10px',
                  padding: '16px',
                  border: '1px solid var(--border-color)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Selected Cases</div>
                    <div style={{ fontSize: '20px', fontWeight: 'bold', color: 'var(--accent-amber)', marginTop: '2px' }}>
                      {selectedCaseIds.size} Cases
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Total Revenue at Risk</div>
                    <div style={{ fontSize: '20px', fontWeight: 'bold', color: 'var(--accent-emerald)', marginTop: '2px' }}>
                      ₹{totalAmount.toLocaleString('en-IN')}
                    </div>
                  </div>
                </div>

                {/* Selected Cases List */}
                <div className="form-group">
                  <label>Selected Case IDs ({selectedCaseIds.size})</label>
                  {selectedList.length === 0 ? (
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', padding: '12px', backgroundColor: 'var(--bg-tertiary)', borderRadius: '8px' }}>
                      No cases selected yet. Click the preset buttons above or checkboxes on the Cases table.
                    </div>
                  ) : (
                    <div style={{
                      maxHeight: '160px',
                      overflowY: 'auto',
                      backgroundColor: 'var(--bg-tertiary)',
                      borderRadius: '8px',
                      padding: '8px',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '6px'
                    }}>
                      {selectedList.map(c => (
                        <div key={c.case_id} style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          padding: '6px 10px',
                          backgroundColor: 'rgba(255, 255, 255, 0.03)',
                          borderRadius: '6px',
                          fontSize: '12px'
                        }}>
                          <span style={{ fontWeight: '600' }}>{c.case_id}</span>
                          <span style={{ color: 'var(--text-secondary)' }}>₹{c.payment?.amount?.toLocaleString('en-IN')}</span>
                          <button
                            type="button"
                            onClick={() => handleToggleSelectCase(c.case_id)}
                            style={{ background: 'transparent', border: 'none', color: 'var(--accent-rose)', cursor: 'pointer', padding: '2px' }}
                          >
                            <X size={14} />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>

              </div>

              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setIsBatchBuilderOpen(false)}>
                  Cancel
                </button>
                <button
                  type="button"
                  className="btn btn-primary"
                  style={{ backgroundColor: 'var(--accent-amber)', borderColor: 'var(--accent-amber)', color: 'black', fontWeight: 'bold' }}
                  disabled={selectedCaseIds.size === 0 || loading}
                  onClick={handleCreateCustomBatchFromSelected}
                >
                  <Layers size={16} />
                  Create Batch Portfolio ({selectedCaseIds.size})
                </button>
              </div>

            </div>
          </div>
        );
      })()}

      {/* Batch Impact Modal */}
      {selectedBatchImpact && (
        <div className="drawer-overlay" onClick={() => setSelectedBatchImpact(null)}>
          <div className="drawer-content" style={{ width: '600px' }} onClick={(e) => e.stopPropagation()}>
            <div className="drawer-header">
              <div>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Batch Impact Report</span>
                <h3 style={{ fontSize: '20px', fontWeight: 'bold' }}>{selectedBatchImpact.batch_id}</h3>
              </div>
              <button className="btn btn-secondary" onClick={() => setSelectedBatchImpact(null)}>Close</button>
            </div>
            <div className="drawer-body" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {/* Financial Impact Comparison */}
              <div className="panel" style={{ padding: '20px' }}>
                <div style={{ fontWeight: 'bold', fontSize: '15px', marginBottom: '12px' }}>Revenue Impact Comparison</div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px', backgroundColor: 'var(--bg-tertiary)', borderRadius: '8px' }}>
                    <div>
                      <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>RecoverAI Revenue</div>
                      <div style={{ fontSize: '20px', fontWeight: 'bold', color: 'var(--accent-emerald)', marginTop: '2px' }}>
                        ₹{selectedBatchImpact.financial_impact.recovered_revenue.toLocaleString('en-IN')}
                      </div>
                    </div>
                    <div>
                      <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>Baseline (Naive Retry)</div>
                      <div style={{ fontSize: '20px', fontWeight: 'bold', color: 'var(--text-muted)', marginTop: '2px' }}>
                        ₹{selectedBatchImpact.baseline_comparison.baseline_recovered_revenue.toLocaleString('en-IN')}
                      </div>
                    </div>
                  </div>
                  
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: 'var(--accent-emerald)' }}>
                    <TrendingUp size={20} />
                    <div>
                      <div style={{ fontWeight: 'bold', fontSize: '14px' }}>
                        +₹{selectedBatchImpact.baseline_comparison.incremental_revenue.toLocaleString('en-IN')} Incremental Revenue
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
                        ({selectedBatchImpact.baseline_comparison.improvement_percentage.toFixed(1)}% improvement vs naive retry baseline)
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Safety Metrics */}
              <div className="grid-2" style={{ gap: '16px' }}>
                <div className="metric-card" style={{ padding: '16px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Policy Block Rate</span>
                  <div style={{ fontSize: '18px', fontWeight: 'bold', marginTop: '4px' }}>
                    {selectedBatchImpact.safety_metrics.policy_block_rate.toFixed(1)}%
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                    Percentage of cases stopped/blocked
                  </div>
                </div>
                <div className="metric-card" style={{ padding: '16px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>HITL Escalation Rate</span>
                  <div style={{ fontSize: '18px', fontWeight: 'bold', marginTop: '4px' }}>
                    {selectedBatchImpact.safety_metrics.hitl_escalation_rate.toFixed(1)}%
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px' }}>
                    Percentage of cases routed to human review
                  </div>
                </div>
              </div>

              {/* Batch Decision Summary */}
              <div className="panel" style={{ padding: '16px' }}>
                <div style={{ fontWeight: 'bold', fontSize: '14px', marginBottom: '12px' }}>Batch Decision Summary</div>
                <div className="grid-3" style={{ gap: '10px' }}>
                  <div style={{ backgroundColor: 'var(--bg-tertiary)', padding: '10px', borderRadius: '8px', textAlign: 'center' }}>
                    <div style={{ fontSize: '18px', fontWeight: 'bold', color: 'var(--accent-emerald)' }}>
                      {selectedBatchImpact.summary.recovered_cases}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px' }}>Recovered</div>
                  </div>
                  <div style={{ backgroundColor: 'var(--bg-tertiary)', padding: '10px', borderRadius: '8px', textAlign: 'center' }}>
                    <div style={{ fontSize: '18px', fontWeight: 'bold', color: 'var(--accent-amber)' }}>
                      {selectedBatchImpact.summary.hitl_cases}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px' }}>Escalated (HITL)</div>
                  </div>
                  <div style={{ backgroundColor: 'var(--bg-tertiary)', padding: '10px', borderRadius: '8px', textAlign: 'center' }}>
                    <div style={{ fontSize: '18px', fontWeight: 'bold', color: 'var(--accent-rose)' }}>
                      {selectedBatchImpact.summary.stopped_cases}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-secondary)', marginTop: '2px' }}>Stopped by Policy</div>
                  </div>
                </div>
              </div>

              {/* Decision Insights: Top Reasons for STOP & HITL */}
              {selectedBatchImpact.decision_insights && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  <div className="panel" style={{ padding: '16px' }}>
                    <div style={{ fontWeight: 'bold', fontSize: '14px', marginBottom: '12px' }}>Top Reasons for STOP</div>
                    {selectedBatchImpact.decision_insights.top_stop_reasons.length === 0 ? (
                      <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>No cases stopped by policy.</div>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {selectedBatchImpact.decision_insights.top_stop_reasons.map((r, idx) => (
                          <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '6px' }}>
                            <span style={{ fontWeight: '500' }}>{r.reason}</span>
                            <span style={{ color: 'var(--accent-rose)', fontWeight: 'bold' }}>{r.count} case(s)</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="panel" style={{ padding: '16px' }}>
                    <div style={{ fontWeight: 'bold', fontSize: '14px', marginBottom: '12px' }}>Top Reasons for HITL</div>
                    {selectedBatchImpact.decision_insights.top_hitl_reasons.length === 0 ? (
                      <div style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>No cases escalated to human review.</div>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                        {selectedBatchImpact.decision_insights.top_hitl_reasons.map((r, idx) => (
                          <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '6px' }}>
                            <span style={{ fontWeight: '500' }}>{r.reason}</span>
                            <span style={{ color: 'var(--accent-amber)', fontWeight: 'bold' }}>{r.count} case(s)</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  
                  {/* Disagreement Analysis List */}
                  <div className="panel" style={{ padding: '16px' }}>
                    <div style={{ fontWeight: 'bold', fontSize: '14px', marginBottom: '12px' }}>
                      AI vs Policy Disagreement Analysis ({selectedBatchImpact.decision_insights.total_disagreements})
                    </div>
                    {selectedBatchImpact.decision_insights.disagreement_cases.length === 0 ? (
                      <div style={{ fontSize: '12px', color: 'var(--accent-emerald)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                        ✓ All AI recommendations aligned perfectly with policy outcomes.
                      </div>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                        {selectedBatchImpact.decision_insights.disagreement_cases.map((dc, idx) => (
                          <div key={idx} style={{ backgroundColor: 'var(--bg-tertiary)', padding: '12px', borderRadius: '8px', fontSize: '12px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                              <span style={{ fontWeight: 'bold', color: 'var(--accent-indigo)' }}>{dc.case_id}</span>
                              <span style={{ color: 'var(--text-muted)' }}>AI: {dc.ai_recommendation} ➔ Policy: {dc.policy_decision}</span>
                            </div>
                            <div style={{ color: 'var(--accent-rose)', fontSize: '11px', marginTop: '4px' }}>
                              <strong>Override Reason:</strong> {dc.reason}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
