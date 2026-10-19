// One pattern that passed: what was compared, the engine's sentence, how many sites it rests on,
// its adjusted significance and a small strength chart. A within-country (or region, or city)
// check that reverses or erases the pattern is shown inside the same card, never apart from it.

import { useId, useState } from 'react';
import { Icon } from '../components/Icon';
import type { ExploreCard } from '../engine/protocol';
import { StrengthChart } from './StrengthChart';
import { comparedText, int, kindLabel, plural, qText } from './text';

interface Within { column?: string; groups?: number; verdict?: string }

const SHOW_SITES = 60;

export function PatternCard({ card, companion, labels }: {
  card: ExploreCard;
  companion?: ExploreCard;
  labels: Record<string, string>;
}) {
  const titleId = useId();
  const sitesId = useId();
  const [sitesOpen, setSitesOpen] = useState(false);
  const [allSites, setAllSites] = useState(false);
  const few = card.reliability === 'few sites';
  const hidden = typeof card.hiddenGroups === 'number' ? card.hiddenGroups : 0;
  const within = (card.within ?? null) as Within | null;
  const stratumLabel = within?.column ? labels[within.column] ?? within.column : '';
  const companionStratum = (companion?.stratum ?? null) as { column?: string; verdict?: string; groups?: number } | null;
  const insideLabel = companionStratum?.column ? labels[companionStratum.column] ?? companionStratum.column : stratumLabel;
  const sites = card.siteIds ?? [];
  const missingOf = card.kind === 'missingness' ? labels[card.columns[0]] ?? card.columns[0] : '';
  const shownSites = allSites ? sites : sites.slice(0, SHOW_SITES);

  return (
    <article className="xp-card" aria-labelledby={titleId}>
      <div className="xp-card__tags">
        <span className="xp-tag">{kindLabel(card)}</span>
        {few && <span className="xp-tag xp-tag--few"><Icon name="exclamationmark.triangle" size={13} strokeWidth={2} /> Few Sites</span>}
        {companion && (
          <span className="xp-tag xp-tag--few">
            <Icon name="exclamationmark.triangle" size={13} strokeWidth={2} />{' '}
            {companionStratum?.verdict === 'reverses' ? `Reverses Within ${insideLabel}` : `Vanishes Within ${insideLabel}`}
          </span>
        )}
      </div>
      <h3 className="xp-card__title" id={titleId}>{comparedText(card, labels)}</h3>
      <p className="xp-card__sentence">{card.sentence}</p>

      <dl className="xp-facts">
        <div className="xp-fact">
          <dt>Sites Compared</dt>
          <dd className="num">{int(card.n)}</dd>
        </div>
        <div className="xp-fact">
          <dt>Adjusted q</dt>
          <dd className="num">{qText(card.q)}</dd>
        </div>
        {hidden > 0 && (
          <div className="xp-fact">
            <dt>Small Groups Left Out</dt>
            <dd className="num">{int(hidden)}</dd>
          </div>
        )}
      </dl>
      {few && <p className="xp-card__note">Fewer than 30 sites stand behind at least one side of this pattern, so it could easily look different with a few more sites.</p>}

      {card.effect && <StrengthChart effect={card.effect} />}

      {within?.verdict === 'holds' && (
        <p className="xp-card__note">
          <Icon name="checkmark.circle" size={16} className="xp-card__note-icon" />{' '}
          The pattern also holds within each {stratumLabel}{within.groups ? ` (${plural(within.groups, 'group')} of 10 or more sites)` : ''}.
        </p>
      )}

      {companion && (
        <div className="xp-inside" role="group" aria-label={`Within each ${insideLabel}`}>
          <p className="xp-inside__title">Within Each {insideLabel}</p>
          <p className="xp-inside__text">{companion.sentence}</p>
          <p className="xp-inside__text">
            {companionStratum?.verdict === 'reverses'
              ? `Across all sites the pattern points one way, but inside each ${insideLabel} it points the other way.`
              : `The pattern is clear across all sites but not inside each ${insideLabel}.`}
            {` Compare sites within the same ${insideLabel} before reading anything into it.`}
          </p>
          {companion.footer && <p className="footnote">{companion.footer}</p>}
        </div>
      )}

      {sites.length > 0 && (
        <div className="xp-sites">
          <button
            type="button"
            className="hig-button hig-button--ios hig-button--small hig-button--borderless hig-focus xp-sites__toggle"
            aria-expanded={sitesOpen}
            aria-controls={sitesId}
            onClick={() => setSitesOpen((o) => !o)}
          >
            <span className="hig-button__label">
              {sitesOpen ? 'Hide the Sites' : `Show the ${plural(sites.length, 'Site')} Missing ${missingOf}`}
            </span>
            <Icon name={sitesOpen ? 'chevron.up' : 'chevron.down'} size={13} strokeWidth={2.4} />
          </button>
          <div id={sitesId} hidden={!sitesOpen}>
            <p className="footnote">Site IDs from your file where {missingOf} is blank or marked unknown.</p>
            <ul className="xp-sites__list" role="list">
              {shownSites.map((id) => <li key={id} className="num">{id}</li>)}
            </ul>
            {sites.length > SHOW_SITES && !allSites && (
              <button type="button" className="hig-button hig-button--ios hig-button--small hig-button--borderless hig-focus" onClick={() => setAllSites(true)}>
                <span className="hig-button__label">Show All {int(sites.length)}</span>
              </button>
            )}
          </div>
        </div>
      )}

      {card.footer && <p className="xp-card__footer footnote">{card.footer}</p>}
    </article>
  );
}
