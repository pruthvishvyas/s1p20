import { KPICards } from '../components/understand/KPICards';
import { ChartPanel } from '../components/understand/ChartPanel';
import { SegmentExplorer } from '../components/understand/SegmentExplorer';
import { AnomalyTable } from '../components/understand/AnomalyTable';
import { InsightCards } from '../components/decide/InsightCards';
import { RecommendationEngine } from '../components/decide/RecommendationEngine';
import { WhatIfSimulator } from '../components/decide/WhatIfSimulator';
import { GoalTracker } from '../components/decide/GoalTracker';
import { Forecaster } from '../components/monitor/Forecaster';
import { GoalProgress } from '../components/monitor/GoalProgress';
import { AlertCenter } from '../components/monitor/AlertCenter';
import { InteractiveExplorer } from '../components/explorer/InteractiveExplorer';
import { UserManual } from '../components/manual/UserManual';
import { Section } from '../components/shared/Section';
import { ErrorBoundary } from '../components/shared/ErrorBoundary';
import { Header } from '../components/shared/Header';
import { outcomeInfo } from '../utils/terminology';
import { useLabels } from '../components/shared/TerminologyProvider';

const wrap = (n) => <ErrorBoundary>{n}</ErrorBoundary>;

export default function Dashboard({ tab }) {
  const L = useLabels();
  let body = null;
  if (tab === 'understand') body = (
    <>
      <Section title={'Your ' + L.revenue + ' at a glance'} subtitle={outcomeInfo.understand.question}>{wrap(<KPICards />)}</Section>
      <Section title="Trends and breakdowns">{wrap(<ChartPanel outcome="UNDERSTAND" />)}</Section>
      <Section title={L.customers + ' by behaviour'} subtitle="Click a group to see who is in it">{wrap(<SegmentExplorer />)}</Section>
      <Section title="Unusual patterns">{wrap(<AnomalyTable />)}</Section>
    </>
  );
  if (tab === 'decide') body = (
    <>
      <Section title="Insights" subtitle={outcomeInfo.decide.question}>{wrap(<InsightCards />)}</Section>
      <Section title="Where the losses come from">{wrap(<ChartPanel outcome="DECIDE" />)}</Section>
      <Section title="Recommended actions" subtitle={'Who to contact and what to do'}>{wrap(<RecommendationEngine />)}</Section>
      <Section title="What-if simulator" subtitle="Explore the impact of a change before you make it">{wrap(<WhatIfSimulator />)}</Section>
      <Section title="Goal tracker">{wrap(<GoalTracker />)}</Section>
    </>
  );
  if (tab === 'monitor') body = (
    <>
      <Section title="Alerts" subtitle={outcomeInfo.monitor.question}>{wrap(<AlertCenter />)}</Section>
      <Section title="Goal progress">{wrap(<GoalProgress />)}</Section>
      <Section title="Forecast">{wrap(<Forecaster />)}</Section>
      <Section title="Other things to keep an eye on">{wrap(<ChartPanel outcome="MONITOR" />)}</Section>
    </>
  );
  if (tab === 'explorer') body = <Section title="Interactive explorer" subtitle="Cross-filter, drill down and compare">{wrap(<InteractiveExplorer />)}</Section>;
  if (tab === 'manual') body = wrap(<UserManual />);
  const titles = { understand: 'UNDERSTAND', decide: 'DECIDE', monitor: 'MONITOR', explorer: 'Explorer', manual: 'User Manual' };
  return (
    <>
      <Header title={titles[tab] || ''} />
      <div className="content">{body}</div>
    </>
  );
}
