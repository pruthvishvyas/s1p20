import { useData } from '../useData';
import { dataPath } from '../../utils/contract';

export const useGoalProgress = () => useData(dataPath('monitor', 'goal_progress'));
