import { createContext, useCallback, useState } from 'react';

export const ExplorerContext = createContext({ filters: {}, setFilter: () => {}, clearFilters: () => {}, activeFilters: 0 });

export function ExplorerProvider({ children }) {
  const [filters, setFilters] = useState({});
  // clicking the same value again removes the filter (toggle)
  const setFilter = useCallback((dimension, value) => {
    setFilters((prev) => {
      const next = { ...prev };
      if (value === null || value === undefined || prev[dimension] === value) delete next[dimension]; else next[dimension] = value;
      return next;
    });
  }, []);
  const clearFilters = useCallback(() => setFilters({}), []);
  return (
    <ExplorerContext.Provider value={{ filters, setFilter, clearFilters, activeFilters: Object.keys(filters).length }}>
      {children}
    </ExplorerContext.Provider>
  );
}
