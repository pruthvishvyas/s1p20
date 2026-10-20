import { Routes, Route, Navigate } from 'react-router-dom';
import { Sidebar } from './components/shared/Sidebar';
import { TerminologyProvider } from './components/shared/TerminologyProvider';
import Dashboard from './pages/Dashboard';

export default function App() {
  return (
    <TerminologyProvider>
      <div className="app">
        <Sidebar />
        <main className="main">
          <Routes>
            <Route path="/" element={<Navigate to="/understand" replace />} />
            {['understand', 'decide', 'monitor', 'explorer', 'manual'].map((t) => <Route key={t} path={'/' + t} element={<Dashboard tab={t} />} />)}
            <Route path="*" element={<Navigate to="/understand" replace />} />
          </Routes>
        </main>
      </div>
    </TerminologyProvider>
  );
}
