// Which states the public data hub covers, where the planner's sites fall, and which state's own
// files (2020 Census blocks, LODES jobs) the values were worked out from (DEC-028). Shown once the
// planner has looked up public data; the state of each site comes from its coordinates.

import type { HubLookup } from '../hub/hub';
import { plural } from '../lib/fieldText';

export function FillCoverage({ hub }: { hub: HubLookup }) {
  const { manifest, states, outside } = hub;
  const title = (id: string) => manifest.datasets[id]?.title ?? id;
  const used = states.filter((s) => s.used);
  const inStates = states.filter((s) => s.sites > 0);
  return (
    <div className="card st-gap-top">
      <p>
        This release covers {manifest.coverage.name}.
        {inStates.length > 0 && ` Your sites: ${inStates.map((s) => `${s.sites} in ${s.state.prose ?? s.state.name}`).join(', ')}.`}
        {outside > 0 && ` ${plural(outside, 'site')} outside these states ${outside === 1 ? 'gets' : 'get'} a reason instead of a value.`}
      </p>
      {used.length > 0 && (
        <>
          <p className="footnote st-gap-top">Each state's own files that the values near your sites were worked out from:</p>
          <ul className="st-plain-list footnote">
            {used.map(({ state }) => (
              <li key={state.fips}>
                <strong>{state.name}</strong>: {title(state.datasets.blocks)}; {title(state.datasets.jobs)}.
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
