// Screenshot manifest. Only rights-reviewed, actual reFrozen gameplay screenshots, chosen by
// the maintainer, may be listed here. Files live in public/screenshots/ (PNG or WebP).
// While this list is empty the gallery shows the original placeholder plates.
// The prerender step fails the build if an entry is incomplete or its file is missing.
export interface ScreenshotVariant {
  /** File name in public/screenshots/. */
  file: string
  /** Intrinsic pixel width of that file. */
  width: number
}

export interface Screenshot {
  /** File name in public/screenshots/ (the full-size image). */
  file: string
  /** Intrinsic size of `file`, used for width/height to prevent layout shift. */
  width: number
  height: number
  /** Optional smaller renditions for srcset. */
  variants?: ScreenshotVariant[]
  /** Visible caption. */
  caption: string
  /** Alternative text describing what the image shows. */
  alt: string
  /** How it was captured: reFrozen build, map, resolution/window mode, date. */
  captureContext: string
  /** Who reviewed and approved publication rights. Required. */
  rightsReviewedBy: string
  /** ISO date (YYYY-MM-DD) of the rights review. Required. */
  rightsReviewedOn: string
}

export const screenshots: Screenshot[] = []
