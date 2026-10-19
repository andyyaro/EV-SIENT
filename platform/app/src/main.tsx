import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './styles/tokens.css';
import './styles/legibility.css';
import './styles/base.css';
import './styles/hig.css';
import './styles/shell.css';
import './styles/app.css';
import './styles/steps.css';
import { App } from './App';
import { registerServiceWorker } from './pwa/register';

createRoot(document.getElementById('root')!).render(<StrictMode><App /></StrictMode>);
registerServiceWorker();
