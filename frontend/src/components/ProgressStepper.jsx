import React from "react";

const ProgressStepper = ({ steps }) => {
  // steps = [{step, total, title, status, detail}]
  // Generate all 3 steps even if only some have been received
  const totalSteps = 3;
  const defaultTitles = [
    "Checking visa requirements…",
    "Analyzing keywords & match…",
    "Tailoring resume with AI…",
  ];

  const allSteps = Array.from({ length: totalSteps }, (_, i) => {
    const stepNum = i + 1;
    const received = steps.find((s) => s.step === stepNum);
    if (received) return received;
    // Determine if this step is pending or hasn't started
    const maxDone = Math.max(0, ...steps.filter(s => s.status === 'done').map(s => s.step));
    const maxRunning = Math.max(0, ...steps.filter(s => s.status === 'running').map(s => s.step));
    if (stepNum <= maxDone) {
      return { step: stepNum, total: totalSteps, title: defaultTitles[i], status: "done" };
    }
    return { step: stepNum, total: totalSteps, title: defaultTitles[i], status: "pending" };
  });

  return (
    <div className="progress-stepper">
      <div className="stepper-title">Tailoring your resume…</div>
      <div className="stepper-steps">
        {allSteps.map((s) => (
          <div key={s.step} className={`step-item step-${s.status}`}>
            <div className="step-icon">
              {s.status === "done" && (
                <svg viewBox="0 0 20 20" fill="currentColor" width="16" height="16">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              )}
              {s.status === "running" && <div className="spinner" />}
              {s.status === "pending" && <div className="step-dot" />}
            </div>
            <div className="step-text">
              <span className="step-title">{s.title}</span>
              {s.detail && s.status === "done" && (
                <span className="step-detail">
                  {s.detail.match_percentage != null && `${s.detail.match_percentage}% match`}
                  {s.detail.keywords_count != null && ` · ${s.detail.keywords_count} keywords`}
                </span>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ProgressStepper;
