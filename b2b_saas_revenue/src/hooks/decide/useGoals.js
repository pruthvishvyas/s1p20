import { useData } from '../useData';
import { dataPath } from '../../utils/contract';

export const useGoals = () => useData(dataPath('decide', 'goals'));
