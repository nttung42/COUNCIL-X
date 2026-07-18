import type { AgentTraceEvent, DashboardStepSummary, DashboardVerdict } from '../types';
import type { ApiPropertyDashboardOutput } from '../services/apiTypes';
import { formatVndShort } from './format';

export interface MappedPropertyDashboard {
  verdict: DashboardVerdict | null;
  dashboardSteps: DashboardStepSummary[];
  overallNarrative: string | null;
  agentTrace: AgentTraceEvent[];
  warnings: string[];
}

export function mapPropertyDashboardOutput(output: ApiPropertyDashboardOutput): MappedPropertyDashboard {
  const verdict: DashboardVerdict | null = output.verdict
    ? {
        decision: output.verdict.decision,
        headline: output.verdict.headline,
        maxLoanVndLabel: formatVndShort(output.verdict.max_loan_vnd),
        downgraded: output.verdict.downgraded,
        reasons: output.verdict.reasons,
      }
    : null;

  const dashboardSteps: DashboardStepSummary[] = output.step_summaries
    .filter((s) => s.step_number >= 1 && s.step_number <= 4)
    .map((s) => ({
      stepNumber: s.step_number as 1 | 2 | 3 | 4,
      title: s.title,
      summaryText: s.summary_text,
    }));

  const agentTrace: AgentTraceEvent[] = output.trace.map((t, index) => ({
    id: `te-api-${index}`,
    secondsOffsetLabel: `t+${t.seconds_offset.toFixed(1)}s`,
    actor: t.actor,
    title: t.title,
    description: t.description ?? '',
  }));

  return {
    verdict,
    dashboardSteps,
    overallNarrative: output.overall_narrative,
    agentTrace,
    warnings: output.warnings ?? [],
  };
}
