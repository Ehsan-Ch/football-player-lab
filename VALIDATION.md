# Validation record

Validated locally on 24 October 2026.

## Automated checks

- **18 Python tests passed**, including period lengths, extra time, substitutions, tactical shifts, on-pitch/bench dismissals, shootout exclusion, spatial boundaries, progressions, rates and ties.
- **5 Node tests passed**: browser aggregates match Python output for all players, cohort filters, single-match scope, zero denominators/ties and CSV escaping.
- JavaScript syntax check passed.
- The frozen report covers 16 matches and 287 players. All 32 team-minute checks reconcile (maximum floating-point difference below 0.000001 seconds).
- All match scoring totals reconcile with the source, including own-goal credit to the opposition. Individual totals exclude own goals.
- 106 shootout events are excluded from player analysis. Shot-zone totals and xG reconcile with player statistics. No source-quality flags remain in this dataset.
- The local server rejects raw-data, source-file and traversal requests.

Tests run offline using synthetic fixtures and the committed aggregate report; they do not redistribute the raw source or download it in CI.

## Browser checks

- Default Messi/Mbappe comparisons loaded with no console errors or warnings.
- Selecting the final changes goals to Messi 2 and Mbappe 3, excluding the shootout.
- A 270-minute minimum in a single-match scope produces a clear empty state.
- Shot zones and passing-flow views render with coverage explanations.
- Searching for Kane and selecting him updates the comparison card.
- CSV export downloads the comparison pool independently of the table search.
- A 390-pixel phone viewport has no page-level horizontal overflow; desktop and phone layouts were visually inspected.

## Limits

This checks arithmetic, conservation, input assumptions and application behavior. It is not independent validation of the provider's event annotations or xG model. No predictive accuracy, causal player impact, complete-tournament ranking or professional scouting suitability is claimed. Small samples and broad position groups can make comparisons unstable.
