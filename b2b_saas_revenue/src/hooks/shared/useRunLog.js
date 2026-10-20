import { useData } from '../useData';
import { metaPath } from '../../utils/contract';

export function useRunLog() {
  const { data, loading, error } = useData(metaPath('run_log.json'));
  const last = Array.isArray(data) && data.length ? data[data.length - 1] : null;
  return { last, runs: Array.isArray(data) ? data : [], loading, error };
}
