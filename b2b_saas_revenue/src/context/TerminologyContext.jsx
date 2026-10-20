import { createContext, useContext } from 'react';
import { labels, } from '../utils/terminology';
import { term } from '../utils/contract';

export const TerminologyContext = createContext({ term, labels: labels() });
export const useTerminology = () => useContext(TerminologyContext);
