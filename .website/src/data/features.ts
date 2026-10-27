export interface Feature {
  id: string
  glyph: string
  title: string
  text: string
  /** Milestone that verifies (or will verify) this feature; its state comes from docs/status.md. */
  milestone: string
}

export const features: Feature[] = [
  { id: 'menus', glyph: 'gate', title: 'Native menus and rendering', milestone: 'M4', text: 'The main menu, profiles, Single Player and the Custom Game screen run as a native arm64 process, drawn by reFrozen’s own graphics layer.' },
  { id: 'match', glyph: 'blade', title: 'A full local DotA match', milestone: 'M5', text: 'Load a DotA map, start the game and play it out: the enemy base falls, the score screen appears, and you return to the menus.' },
  { id: 'audio', glyph: 'horn', title: 'Miles audio', milestone: 'M5', text: 'The game’s sound plays through its own Miles audio library, running on SDL3 instead of DirectSound.' },
  { id: 'input', glyph: 'hand', title: 'Mouse and keyboard', milestone: 'M5', text: 'Native mouse and keyboard input, with the pointer mapped exactly onto the game’s screen — even in fullscreen with bars.' },
  { id: 'display', glyph: 'eye', title: 'Retina and borderless fullscreen', milestone: 'M5', text: 'Sharp on Retina and scaled displays. Ctrl + Cmd + F toggles borderless fullscreen; the classic 4:3 interface is framed, never stretched.' },
  { id: 'replays', glyph: 'scroll', title: 'Replays written', milestone: 'M5', text: 'Each finished match writes its replay file, just as it always did, and it plays back in the game.' },
  { id: 'installer', glyph: 'forge', title: 'A native installer, no Wine', milestone: 'M2', text: 'reFrozen installs the game from your own official installers directly on macOS. No Wine, no virtual machine, at any step.' },
  { id: 'ai', glyph: 'duel', title: 'AI matches', milestone: 'M6', text: 'Full matches against computer opponents on DotA AI maps, with frame pacing and long-session stability.' },
]
