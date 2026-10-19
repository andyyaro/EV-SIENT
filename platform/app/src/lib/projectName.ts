// The project's name, as the planner reads it on the report cover, in the project file and in every
// download's file name: the jurisdiction from the source details when given, else the uploaded file's
// name made readable ("example_city_facilities.csv" -> "Example City Facilities").

import type { AcceptDetails } from '../engine/protocol';

/** "example_city_facilities.csv" -> "Example City Facilities"; words with capitals ("EV") are kept as written. */
export function readableFileName(fileName: string): string {
  const stem = fileName.replace(/\.[^.]+$/, '');
  return stem
    .replace(/[_\-.+]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .split(' ')
    .map((w) => (w && w === w.toLowerCase() ? w.charAt(0).toUpperCase() + w.slice(1) : w))
    .join(' ');
}

export function projectName(details: AcceptDetails, fileName: string | null | undefined): string {
  return details.jurisdiction?.trim() || (fileName ? readableFileName(fileName) : '') || 'EV-SIENT Project';
}
