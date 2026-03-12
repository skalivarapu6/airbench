import { Link, useLocation } from 'react-router-dom';
import './Layout.css';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout = ({ children }: LayoutProps) => {
  const location = useLocation();

  const isActive = (path: string) => {
    return location.pathname.startsWith(path);
  };

  return (
    <div className="layout">
      <nav className="sidebar">
        <div className="logo">
          <h1>AirBench</h1>
          <p>LLM Experiment Tracker</p>
        </div>

        <ul className="nav-menu">
          <li className={isActive('/experiments') ? 'active' : ''}>
            <Link to="/experiments">
              <span className="icon">🧪</span>
              Experiments
            </Link>
          </li>
          <li className={isActive('/datasets') ? 'active' : ''}>
            <Link to="/datasets">
              <span className="icon">📊</span>
              Datasets
            </Link>
          </li>
        </ul>

        <div className="sidebar-footer">
          <Link to="/experiments/new" className="btn-primary">
            + New Experiment
          </Link>
        </div>
      </nav>

      <main className="main-content">
        {children}
      </main>
    </div>
  );
};

export default Layout;
