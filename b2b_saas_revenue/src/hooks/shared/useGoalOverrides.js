import { useEffect, useState } from 'react';
import { getOverrides } from '../../utils/goalStore';

export function useGoalOverrides() {
  const [o, setO] = useState(getOverrides);
  useEffect(() => {
    const h = () => setO(getOverrides());
    window.addEventListener('goals-changed', h);
    return () => window.removeEventListener('goals-changed', h);
  }, []);
  return o;
}
