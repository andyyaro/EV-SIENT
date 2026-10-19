// Common Questions: fixed answers to what a planner asks first, in a modal dialog so the open
// project is kept. Linked beside Licences in the sidebar footer and the Start screen's small print.
//
// Every answer restates the repository's own documents and code, and must change when they do:
// where data goes (README "Rules the code keeps", DEC-024, the Start screen's data panel), the
// score (docs/GLOSSARY.md, docs/INPUT_SCHEMA.md "What the results mean", scoring.SUBSCORE_WEIGHTS),
// missing values (DEC-011 as docs/INPUT_SCHEMA.md states it), tiers (scoring.recommendation_tier,
// config.TIER*), data confidence (confidence.py, docs/GLOSSARY.md), citing (the report's
// Reproducibility section, data/contract/v1/README.md rule 3), limits
// (docs/WHAT_THIS_CAN_AND_CANNOT_TELL_YOU.md), browsers (tools/browser_check.py, tools/matrix.py),
// offline use (pwa/sw.js) and accessibility (docs/accessibility/ACR.md, public/accessibility.html).

import { useEffect, useRef, useState, type ReactNode } from 'react';

const ANSWERS: { q: string; a: ReactNode }[] = [
  {
    q: 'Where does my data go?',
    a: (
      <>
        <p>Nowhere. Your file is read in this browser tab and the model runs here too. Nothing you upload is sent to a server, and the planner has no analytics or tracking.</p>
        <p>The only other network use is the map on the Results step, which loads background map tiles. The tile server sees which area the map shows, never your file or your sites. Close the tab and the file and results are gone, unless you save a project file from the Report step.</p>
      </>
    ),
  },
  {
    q: 'What does the score mean?',
    a: (
      <>
        <p>The readiness score, from 0 to 100, compares how ready each site appears for public charging, given what your file records. It adds four parts: demand (45%), feasibility (30%), safety (15%) and equity (10%), each built from fields in your file. Results show which fields drive each site's score.</p>
        <p>Scores use fixed anchors, so a site gets the same score whichever other sites are in the run, and scores can be compared across runs. The anchors were set for the reference study's region and were not calibrated to yours. A score is not a statement that a site is electrically feasible.</p>
      </>
    ),
  },
  {
    q: 'Why does a missing value earn no credit?',
    a: (
      <>
        <p>A value nobody recorded earns no credit and is never replaced by a guess (decision DEC-011). A gap must never lift a site above where a recorded answer could have put it, so a site with gaps may be understated, never overstated.</p>
        <p>This includes the "lower is better" fields, such as distance to electrical service and trenching: a blank earns nothing, not the best possible value. A file with gaps gives lower scores and lower data confidence, not a refusal and not a confident answer. Each site's missing fields are listed with its results, so you can fill them in and run again.</p>
      </>
    ),
  },
  {
    q: 'What do the tiers mean?',
    a: (
      <>
        <p><strong>Tier 1</strong> (advance to site screening) needs rank 2 or better and a score of at least 50, so at most two sites in any run can hold it. <strong>Tier 2</strong> (promising candidate, refine data) needs a score of at least 45. <strong>Tier 3</strong> (lower priority, monitor) is the rest.</p>
        <p>Two labels come first. A site not recorded as open to the public is <strong>Low public-priority / special-use</strong>, and a site whose parking is an enclosed garage, or not recorded either way, is a <strong>High-review candidate</strong> until someone checks. Because Tier 1 depends on the other sites in the run, compare scores across runs, never tiers.</p>
      </>
    ),
  },
  {
    q: 'What does Data Confidence mean?',
    a: (
      <>
        <p>How well sourced each site's figures are, from 0 to 100. It is worked out only from typed provenance: where each group of figures came from, whether anyone verified it, and how old the source is (more than two years, or no date, costs points). It is never judged from how good the answer looks.</p>
        <p>High is 75 or more, Medium 50 to 74.9, Low below 50. Confirming the column matches confirms what the columns mean, not that the figures are right, so a new file is Low until your organization records where its figures came from.</p>
      </>
    ),
  },
  {
    q: 'How do I cite a result?',
    a: (
      <p>Cite the run, not only the number. The report's Reproducibility section lists the run ID, the model mode, when the run was generated, the date data confidence was judged as of, the engine version and its SHA-256, the data contract version and the hash of every input and result file. Quote those with any figure you use, under the name EV-SIENT Planner. Anyone with your project file can open it in the planner and run the same result again.</p>
    ),
  },
  {
    q: 'What is this tool not?',
    a: (
      <>
        <p>It is planning support, not engineering advice. It compares sites to help decide what to study next. It cannot tell you whether a site has the electrical capacity for chargers: capacity stays a placeholder until a utility or facility confirms it.</p>
        <p>Costs are screening-class estimates for comparing options, never budgets, quotes or bids. Demand and waits are modelled, not observed. Nothing in a result is an approval: what can be built is decided by the Authority Having Jurisdiction (the building official, electrical inspector or fire marshal) and the utility.</p>
      </>
    ),
  },
  {
    q: 'Which browsers does it work in?',
    a: (
      <p>A current browser that runs WebAssembly and module Web Workers. Each release is checked in Chromium (the engine of Chrome and Edge) and WebKit (the engine of Safari), at phone, tablet and desktop window sizes, in light and dark appearance. Firefox is not part of those checks. The first visit downloads about 14 MB, the Python runtime and the model, once.</p>
    ),
  },
  {
    q: 'Can I use it offline?',
    a: (
      <>
        <p>Yes, once the model has loaded on this device. The planner keeps its own files and, after the model first loads, the Python runtime and the model, so it opens and runs without a connection. The background tiles of the Results map still need one. Your browser may also offer to install the planner as an app.</p>
        <p>What is kept is the planner itself, never your file or results. When a new version is published, the planner says so and waits for you to reload.</p>
      </>
    ),
  },
  {
    q: 'Is the planner accessible?',
    a: (
      <p>It aims to meet WCAG 2.1 and 2.2 Level AA, and every release is checked with axe-core in four colour themes and by keyboard alone. The project team&apos;s own assessment, which is not an independent audit, says what meets each criterion and what does not yet: <a className="app-licences" href="/accessibility.html" target="_blank" rel="noopener">Accessibility Conformance Report<span className="hig-visually-hidden"> (opens in a new tab)</span></a>.</p>
    ),
  },
];

function FaqDialog({ onClose }: { onClose: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  // Removing an open modal dialog from the page closes it, so unmounting needs no cleanup.
  useEffect(() => { if (ref.current && !ref.current.open) ref.current.showModal(); }, []);
  return (
    <dialog
      ref={ref}
      className="app-faq"
      aria-labelledby="faq-title"
      onClose={onClose}
      onClick={(e) => { if (e.target === ref.current) ref.current.close(); }}
    >
      <div className="app-faq__head">
        <h2 id="faq-title" className="app-faq__title">Common Questions</h2>
        <button type="button" className="hig-button hig-button--ios hig-button--medium hig-button--borderless hig-focus" onClick={() => ref.current?.close()}>
          <span className="hig-button__label">Done</span>
        </button>
      </div>
      <div className="app-faq__body">
        {ANSWERS.map(({ q, a }) => (
          <section key={q} className="app-faq__item">
            <h3 className="app-faq__q">{q}</h3>
            {a}
          </section>
        ))}
      </div>
    </dialog>
  );
}

export function FaqLink() {
  const [open, setOpen] = useState(false);
  const link = useRef<HTMLAnchorElement>(null);
  // Safari does not focus a clicked link, so the dialog cannot hand focus back by itself.
  const close = () => { setOpen(false); link.current?.focus(); };
  return (
    <>
      <a ref={link} className="app-licences" href="#faq" aria-haspopup="dialog" onClick={(e) => { e.preventDefault(); setOpen(true); }}>
        Common Questions
      </a>
      {open && <FaqDialog onClose={close} />}
    </>
  );
}
