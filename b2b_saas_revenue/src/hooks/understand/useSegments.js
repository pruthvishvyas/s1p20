import { useData } from '../useData';
import { dataPath } from '../../utils/contract';

export const useSegments = () => useData(dataPath('understand', 'segments'));
