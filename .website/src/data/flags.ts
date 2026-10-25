// Feature flags. Flip SHOW_SCREENSHOTS to true to restore the Screenshots page everywhere:
// navigation, footer, home lane map, sitemap and indexing. When false, /screenshots/ is still
// prerendered and reachable by direct URL, but unlinked, marked noindex and left out of the sitemap.
export const SHOW_SCREENSHOTS: boolean = false

/** Prerendered paths that are unlinked, noindex and excluded from the sitemap. */
export const hiddenPaths: string[] = SHOW_SCREENSHOTS ? [] : ['/screenshots/']
