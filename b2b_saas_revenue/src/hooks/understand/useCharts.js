import { filesUnder } from '../../utils/contract';

// chart specs are listed in the contract; each ChartCard loads its own file through useData
export const useCharts = (outcome) => filesUnder('understand/charts/').filter((c) => !outcome || String(c.outcome).toUpperCase() === outcome);
