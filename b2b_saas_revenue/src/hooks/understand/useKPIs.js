import { useData } from '../useData';
import { dataPath } from '../../utils/contract';

export const useKPIs = () => useData(dataPath('understand', 'kpis'));
