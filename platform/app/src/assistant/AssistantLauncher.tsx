// How the planner opens the Assistant: a link in the sidebar footer, a button in the compact bar
// on narrow screens, and the dialog itself, which loads only when first opened. Focus returns to
// whichever control opened it.

import { lazy, Suspense } from 'react';
import { create } from 'zustand';
import { Icon } from '../components/Icon';
import './assistant.css';

const AssistantPanel = lazy(() => import('./AssistantPanel').then((m) => ({ default: m.AssistantPanel })));

interface OpenState {
  open: boolean;
  opener: HTMLElement | null;
  show(opener: HTMLElement | null): void;
  hide(): void;
}

export const useAssistantOpen = create<OpenState>((set, get) => ({
  open: false,
  opener: null,
  show(opener) { set({ open: true, opener }); },
  hide() {
    const opener = get().opener;
    set({ open: false, opener: null });
    // Safari does not focus a clicked link, so the dialog cannot hand focus back by itself.
    opener?.focus();
  },
}));

export function AssistantLink() {
  const show = useAssistantOpen((s) => s.show);
  return (
    <a className="app-licences" href="#assistant" aria-haspopup="dialog" onClick={(e) => { e.preventDefault(); show(e.currentTarget); }}>
      Assistant
    </a>
  );
}

export function AssistantButton() {
  const show = useAssistantOpen((s) => s.show);
  return (
    <button type="button" className="app-compact__assistant hig-focus" aria-haspopup="dialog" onClick={(e) => show(e.currentTarget)}>
      <Icon name="bubble" size={20} strokeWidth={1.8} />
      <span className="hig-visually-hidden">Open Assistant</span>
    </button>
  );
}

export function AssistantHost() {
  const open = useAssistantOpen((s) => s.open);
  const hide = useAssistantOpen((s) => s.hide);
  if (!open) return null;
  return (
    <Suspense fallback={null}>
      <AssistantPanel onClose={hide} />
    </Suspense>
  );
}
