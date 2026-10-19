// Registers the service worker (/sw.js, written from pwa/sw.js at build time) in production
// builds, and keeps the one thing the interface needs from it: whether a new version is waiting.
// The page never reloads by itself. App shows a banner and the planner chooses when, because a
// reload closes the open project.

import { create } from 'zustand';
import { useSession } from '../state/store';

interface UpdateState {
  /** A new version has installed and is waiting for the planner's Reload. */
  ready: boolean;
  dismissed: boolean;
  dismiss(): void;
  apply(): void;
}

const CHECK_EVERY_MS = 60 * 60 * 1000;
let waiting: ServiceWorker | null = null;

export const useUpdate = create<UpdateState>((set) => ({
  ready: false,
  dismissed: false,
  dismiss: () => set({ dismissed: true }),
  apply() {
    if (!waiting) return;
    // Another tab may already have switched to the new version.
    if (waiting.state === 'activated') { location.reload(); return; }
    navigator.serviceWorker.addEventListener('controllerchange', () => location.reload(), { once: true });
    waiting.postMessage({ type: 'skip-waiting' });
  },
}));

async function register(): Promise<void> {
  let reg: ServiceWorkerRegistration;
  try {
    reg = await navigator.serviceWorker.register('/sw.js', { scope: '/' });
  } catch (e) {
    console.warn('The planner cannot work offline in this browser:', e);
    return;
  }
  const offer = (worker: ServiceWorker | null) => {
    // No controller yet means this is the first install: there is nothing to update from.
    if (!worker || !navigator.serviceWorker.controller) return;
    waiting = worker;
    useUpdate.setState({ ready: true });
  };
  offer(reg.waiting);
  reg.addEventListener('updatefound', () => {
    const worker = reg.installing;
    worker?.addEventListener('statechange', () => { if (worker.state === 'installed') offer(worker); });
  });
  // Browsers look for a new worker on each visit; a tab left open all day checks hourly.
  let checked = Date.now();
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState !== 'visible' || Date.now() - checked < CHECK_EVERY_MS) return;
    checked = Date.now();
    reg.update().catch(() => {});
  });
}

/** Once the real model has loaded, ask the worker to keep the runtime and engine for offline use. */
function keepRuntimeOnceLoaded(): void {
  const unsubscribe = useSession.subscribe((s) => {
    if (s.boot.status !== 'ready' || s.boot.info.pyodide === 'mock') return;
    unsubscribe();
    void navigator.serviceWorker.ready.then((reg) => reg.active?.postMessage({ type: 'keep-runtime' }));
  });
}

export function registerServiceWorker(): void {
  if (!import.meta.env.PROD || !('serviceWorker' in navigator)) return;
  keepRuntimeOnceLoaded();
  // After the first paint's own requests, so registering never slows the Start screen.
  if (document.readyState === 'complete') void register();
  else window.addEventListener('load', () => void register(), { once: true });
}
