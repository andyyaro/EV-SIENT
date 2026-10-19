// The notices for everything the planner ships (public/licences.txt, written at build time by
// platform/tools/build_licences.mjs). Opens in a new tab so the planner's open project is kept.

export function LicencesLink() {
  return (
    <a className="app-licences" href="/licences.txt" target="_blank" rel="noopener">
      Licences<span className="hig-visually-hidden"> (opens in a new tab)</span>
    </a>
  );
}
