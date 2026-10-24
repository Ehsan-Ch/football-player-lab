# Data, definitions and rights

This project uses **StatsBomb Open Data**, hosted in [hudl/open-data](https://github.com/hudl/open-data) (formerly statsbomb/open-data).

- Pinned revision: `4b73468fc5b0f1950f9f66fada70ad3a4f9327cb`.
- Competition 43, season 106: men's World Cup 2022.
- Selected stages: Round of 16, Quarter-finals, Semi-finals, Final and 3rd Place Final.
- [Provider README](https://github.com/hudl/open-data/blob/4b73468fc5b0f1950f9f66fada70ad3a4f9327cb/README.md)
- [Provider license](https://github.com/hudl/open-data/blob/4b73468fc5b0f1950f9f66fada70ad3a4f9327cb/LICENSE.pdf)
- [Events specification](https://github.com/hudl/open-data/blob/4b73468fc5b0f1950f9f66fada70ad3a4f9327cb/doc/Open%20Data%20Events%20v4.0.0.pdf)
- [Lineups specification](https://github.com/hudl/open-data/blob/4b73468fc5b0f1950f9f66fada70ad3a4f9327cb/doc/Open%20Data%20Lineups%20v2.0.0.pdf)

The published JSON and CSV are aggregate research outputs. They contain player/match totals and coarse spatial summaries, not raw event records, event identifiers or exact event coordinates. Source event and lineup files and local documentation copies are excluded from Git. Download them directly from the provider using the reproducibility command only under the provider's terms.

The StatsBomb logo in `web/statsbomb-logo.png` comes from the provider repository's `img/SB - Icon Lockup - Colour positive.png` at the revision above. It is displayed for attribution, not as an endorsement. It is not covered by this project's MIT license.

Original software is MIT-licensed. Provider material and rights in data-derived outputs are not relicensed by that code license. The published analysis is intended for research and noncommercial use; consult the provider before commercial use or redistribution outside those terms.

## Processing decisions

Source lineup position intervals contained overlaps and inconsistent end times. Playing time is therefore reconstructed from event-stream starting lineups, substitutions, red cards and period endings. Tactical shifts determine time by role. Team-player minutes reconcile against eleven players times match duration, less on-pitch dismissal losses. This prevents double-counting overlapping position spells.

Period 5 is a penalty shootout and is excluded. Periods 1–4 include additional time, so elapsed-minute rates differ from conventional tables that cap halves at 45 or 15 minutes. See the README for metric definitions and the interface for sample limitations.
