import { useData } from '../useData';
import { dataPath } from '../../utils/contract';

export const useInsights = () => useData(dataPath('decide', 'insights'));
