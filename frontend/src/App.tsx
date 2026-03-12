import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import ExperimentsList from './pages/ExperimentsList';
import ExperimentDetail from './pages/ExperimentDetail';
import DatasetsList from './pages/DatasetsList';
import NewExperiment from './pages/NewExperiment';
import './App.css';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Navigate to="/experiments" replace />} />
          <Route path="/experiments" element={<ExperimentsList />} />
          <Route path="/experiments/new" element={<NewExperiment />} />
          <Route path="/experiments/:id" element={<ExperimentDetail />} />
          <Route path="/datasets" element={<DatasetsList />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
