# reFrozen v0.2.0 Beta: release notes (draft)

Draft, not published. Scope, requirements and the release decision are in `M7_READINESS.md`;
the text below grows with the release and is reviewed before publication.

## Known issues

- **Terror of the Tides (The Frozen Throne's Sentinel campaign) stops the game when you start it.**
  The game paints a full-screen window with a Windows drawing call (GDI's FillRect) that reFrozen
  does not implement yet. A known compatibility limitation, not blocking v0.2.0; planned for after
  it. The Founding of Durotar starts and its opening sequence plays (the rest of that campaign is
  not verified); the other campaigns are not verified yet.
- **Saved games of one map version, DotA v6.83d AI (PMV 1.42 EN), can't be loaded** (as in v0.1.0).
  Saving works; saves load on Booty Bay and DotA v6.78c AI 1.4e.
