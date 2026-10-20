import { useData } from '../useData';
import { dataPath } from '../../utils/contract';

export const useAlerts = () => useData(dataPath('monitor', 'alerts'));
