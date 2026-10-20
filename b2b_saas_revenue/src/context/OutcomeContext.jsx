import { createContext, useContext } from 'react';
import { outcomeInfo } from '../utils/terminology';

export const OutcomeContext = createContext(outcomeInfo);
export const useOutcomes = () => useContext(OutcomeContext);
