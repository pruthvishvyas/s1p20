import { useData } from '../useData';
import { dataPath } from '../../utils/contract';

export const useRecommendations = () => useData(dataPath('decide', 'recommendations'));
