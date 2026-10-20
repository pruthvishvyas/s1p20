import { useData } from '../useData';
import { dataPath } from '../../utils/contract';

export const useAnomalies = () => useData(dataPath('understand', 'anomalies'));
