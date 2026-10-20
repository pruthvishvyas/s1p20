import { TerminologyContext, useTerminology } from '../../context/TerminologyContext';
import { labels } from '../../utils/terminology';
import { term } from '../../utils/contract';

export function TerminologyProvider({ children }) {
  return <TerminologyContext.Provider value={{ term, labels: labels() }}>{children}</TerminologyContext.Provider>;
}
// useTerm() returns the term lookup function: term('revenue') -> the client's word for revenue
export const useTerm = () => useTerminology().term;
export const useLabels = () => useTerminology().labels;
