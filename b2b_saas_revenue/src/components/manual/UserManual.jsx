import { useState, useMemo } from 'react';
import { ManualSection } from './ManualSection';
import { GlossaryTable } from './GlossaryTable';
import { useTerm } from '../shared/TerminologyProvider';
import { plural, CONTRACT } from '../../utils/contract';

export function UserManual() {
  const term = useTerm();
  const [q, setQ] = useState('');
  const R = term('revenue'), C = term('customer'), Cs = plural(C), P = term('product'), T = term('transaction');
  const sections = useMemo(() => [
    { title: 'How to use this dashboard', items: [
      { h: 'Three questions, three sections', p: ['UNDERSTAND answers: what is happening in my business right now?', 'DECIDE answers: what should I do about it?', 'MONITOR answers: is my business on track without me checking manually?', 'Explorer lets you slice your own data by any group, and this manual explains everything in plain English.'] }] },
    { title: 'UNDERSTAND', items: [
      { h: 'Your numbers (KPI cards)', p: ['What you see: your ' + R + ', how many ' + Cs.toLowerCase() + ' you have, how much of your ' + R + ' you keep, and how healthy your cash collection is.', 'What it means: a number marked with an up arrow went up since last month. For lost ' + Cs.toLowerCase() + ' and overdue receivables, down is the good direction.', 'What to do: check these cards first every Monday. If retention is below 100% your base shrinks unless new sales cover the gap.'] },
      { h: 'Charts', p: ['A line chart shows how something changes over time: look for the direction, not each wiggle.', 'A bar chart compares groups: the taller (or longer) the bar, the bigger the number.', 'What to look for: sudden drops in ' + R + ', rising lost-' + Cs.toLowerCase() + ' lines and growing overdue receivables.'] },
      { h: 'Segments', p: ['Your ' + Cs.toLowerCase() + ' are grouped by how they behave (health, seat usage, discount, tenure). Click a group to list its ' + Cs.toLowerCase() + '.', 'What to do: protect "Champions", help "Under-Adopting" groups use the product, and watch "At-Risk" groups weekly.'] },
      { h: 'Unusual patterns (anomalies)', p: ['These are ' + Cs.toLowerCase() + ' whose month looked very different from normal: a sudden drop in logins, health or a cost spike.', 'What to do: open the top rows and call the ' + C.toLowerCase() + ' or check the data. The driver column tells you what changed most.'] }] },
    { title: 'DECIDE', items: [
      { h: 'Your insights', p: ['Severity explained:', 'HIGH: needs attention this week. MEDIUM: review this month. LOW: good to know.', 'Each card says what we found, the numbers behind it and what to do. Cards are ordered by the money at stake.'] },
      { h: 'Your recommendations', p: ['Each row is a ' + C.toLowerCase() + ' that needs attention. P1 means act this week, P2 this month, P3 plan for it.', 'It tells you the action, why (the reason tags), and how much ' + R + ' is at risk. Use the filter buttons to build a call list.'] },
      { h: 'What-if simulator', p: ['Use it to explore: what would happen if I changed prices, ran a retention campaign or reduced discounts?', 'Move the slider or pick a button and the projected result updates immediately. These are estimates based on stated assumptions, not promises.'] },
      { h: 'Goals', p: ['Set the targets you care about (for example a ' + R + ' target). They are saved in this browser and drive the Goal Progress panel.'] }] },
    { title: 'MONITOR', items: [
      { h: 'Forecast', p: ['Our prediction of your future ' + R + ' based on your history. The shaded band is the range it will most likely fall in; the wider it is, the less certain we are.', 'Use "Look up a forecast" to get the expected ' + R + ' for any number of months ahead.'] },
      { h: 'Goal progress', p: ['Green means you are within your target, red means you are off target, grey means you have not set a target yet.'] },
      { h: 'Alerts', p: ['A list of things that moved outside your limits, most serious first. If it is empty, nothing needs attention right now.'] }] },
    { title: 'Explorer', items: [
      { h: 'Slicing your data', p: ['Pick a measure (what to count or add up) and a group (how to split it). Click any bar to filter every other chart to that group; click it again to remove the filter.', 'A panel slides in with totals and the top ' + Cs.toLowerCase() + ' of the group you clicked. "Copy summary" puts a one-line description of your current view on the clipboard.'] }] }
  ], [R, C, Cs]);
  const glossary = useMemo(() => [
    [R, 'Monthly recurring revenue: the predictable subscription income you earn each month.'],
    [C, 'A business that pays you for the ' + P.toLowerCase() + ' (' + Cs.toLowerCase() + ' in plural).'],
    [P, 'The package a ' + C.toLowerCase() + ' buys, for example Starter, Growth or Scale.'],
    [T, 'A bill sent to a ' + C.toLowerCase() + '.'],
    ['Net revenue retention (NRR)', 'How much ' + R + ' you keep from existing ' + Cs.toLowerCase() + ' after upgrades, downgrades and losses. Above 100% means growth without new sales.'],
    ['Gross revenue retention (GRR)', 'The same, but ignoring upgrades. It shows how much you simply hold on to.'],
    ['Churn', 'A ' + C.toLowerCase() + ' leaving or reducing what they pay.'],
    ['Health score', 'A 0-100 score of how well a ' + C.toLowerCase() + ' is doing with your product. Under 50 is a warning sign.'],
    ['Seat usage', 'The share of paid seats that people actually use. Low usage often comes before leaving.'],
    ['Risk level (HIGH / MEDIUM / LOW)', 'How likely a ' + C.toLowerCase() + ' is to leave next month, compared with the rest of your base.'],
    ['Anomaly', "An unusual month that doesn't match a " + C.toLowerCase() + "'s normal behaviour."],
    ['Forecast', 'Our prediction of your future ' + R + ' based on your historical patterns.'],
    ['Likely range (P10-P90)', 'The band the forecast should fall inside about 8 times out of 10.'],
    ['Priority P1 / P2 / P3 / P4', 'How urgent an action is: P1 this week, P2 this month, P3 plan for it, P4 routine.'],
    ['Receivables 60+ days', 'Money customers owe you that is more than 60 days old.'],
    ['Contribution margin', 'What is left of revenue after delivering the service and the cost of winning the ' + C.toLowerCase() + '.'],
    ['Line chart / Bar chart', 'A line shows change over time; a bar compares groups side by side.']
  ], [R, C, Cs, P, T]);
  const ql = q.trim().toLowerCase();
  const textOf = (s) => (s.title + ' ' + s.items.map((i) => i.h + ' ' + i.p.join(' ')).join(' ')).toLowerCase();
  const shown = sections.filter((s) => !ql || textOf(s).includes(ql));
  const gl = glossary.filter(([t, d]) => !ql || (t + ' ' + d).toLowerCase().includes(ql));
  return (
    <div className="manual">
      <div className="manual-tools">
        <input className="input" type="search" placeholder="Search the manual..." value={q} onChange={(e) => setQ(e.target.value)} aria-label="Search the manual" />
        <button className="btn" onClick={() => window.print()}>Print</button>
      </div>
      <h2 className="manual-title">{CONTRACT.project.name} &mdash; Your Analytics Guide</h2>
      {shown.map((s) => <ManualSection key={s.title} title={s.title} items={s.items} q={ql} />)}
      {gl.length > 0 && <section className="manual-section card"><h2>Glossary</h2><GlossaryTable rows={gl} q={ql} /></section>}
      {!shown.length && !gl.length && <p className="muted">Nothing in the manual matches "{q}".</p>}
    </div>
  );
}
