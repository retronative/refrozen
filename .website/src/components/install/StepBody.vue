<script setup lang="ts">
// The content of one installation step. Used by each step's own page (sub-headings at level 2)
// and by the all-steps page (level 3, ids prefixed so they stay unique on one page).
import { computed } from 'vue'
import { RouterLink } from 'vue-router'
import StatusTag from './StatusTag.vue'
import StepArt from './StepArt.vue'
import { TBA, installPath, installSteps, release } from '../../data/release'

const props = defineProps<{ index: number; level: 2 | 3; idPrefix?: string }>()
const n = computed(() => props.index + 1)
const h = computed(() => `h${props.level}`)
const id = (name: string) => `${props.idPrefix ?? ''}${name}`
const dataFolder = '~/Library/Application Support/reFrozen'
</script>

<template>
  <div class="install-body">
    <!-- 1. Download -->
    <template v-if="n === 1">
      <p class="install-lead">Get reFrozen {{ release.version }} for Apple silicon Macs: an offline-only alpha pre-release.</p>
      <div class="install-download">
        <a class="btn" :href="release.dmg.url ?? undefined" :aria-describedby="id('download-note')">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M8 1v10M3.5 6.5 8 11l4.5-4.5M2 15h12" /></svg>
          Download reFrozen
        </a>
        <p :id="id('download-note')" class="install-download__note">
          From the <a :href="release.page ?? undefined">GitHub release page</a>, with the release notes and known limitations.
        </p>
        <dl class="install-facts">
          <div><dt>Version</dt><dd>{{ release.version ?? TBA }}</dd></div>
          <div><dt>File</dt><dd>{{ release.dmg.name ?? TBA }}</dd></div>
          <div><dt>Released</dt><dd>{{ release.released ?? TBA }}</dd></div>
        </dl>
      </div>
      <StepArt :step="1" />

      <component :is="h" :id="id('what-you-will-need')">What you will need</component>
      <ul class="install-list">
        <li>An <strong>Apple silicon Mac</strong> (M-series). Intel Macs are not supported.</li>
        <li><strong>{{ release.minMacos ?? TBA }} or later.</strong> <StatusTag kind="verified" /> Tested on macOS 27.0.1.</li>
        <li>
          <strong>Apple's Command Line Tools</strong>, a free download from Apple. The first-run setup checks for them and offers
          Apple's installer if they are missing.
        </li>
        <li>
          <strong>Your own copy of the game:</strong> the official installers for <em>Warcraft III: Reign of Chaos</em> and
          <em>The Frozen Throne</em>, with your own CD keys, plus the official 1.26a English patch. The exact versions are on the
          <RouterLink to="/compatibility/#game-version">Compatibility</RouterLink> page.
        </li>
        <li><StatusTag kind="verified" /> <strong>Free disk space:</strong> {{ (release.diskSpace ?? TBA).toLowerCase() }}.</li>
        <li><strong>Any maps you want to play</strong>, which you supply yourself.</li>
      </ul>

      <details class="install-details">
        <summary><span>Check the download (optional)</span> <StatusTag kind="verified" /></summary>
        <div class="install-details__body">
          <p>The release publishes a SHA-256 checksum next to the download. To compare it, open Terminal in the folder with the download and run <code>shasum -a 256</code> followed by the file name.</p>
          <p>The code it prints must match the published one exactly.</p>
          <p class="mb-0">Published checksum: <code class="install-hash">{{ release.dmg.sha256 ?? TBA }}</code></p>
        </div>
      </details>
    </template>

    <!-- 2. Install -->
    <template v-else-if="n === 2">
      <p class="install-lead">Open the downloaded disk image, then drag <strong>reFrozen</strong> onto the <strong>Applications</strong> folder.</p>
      <StepArt :step="2" />
      <p>Then open reFrozen from your Applications folder, not from the disk image. You can eject the disk image afterwards.</p>
      <p class="install-quiet">The app contains no game code, assets, maps or keys. The game is set up from your own copy in step 4.</p>
    </template>

    <!-- 3. First launch -->
    <template v-else-if="n === 3">
      <p class="install-lead">
        Open reFrozen from Applications. reFrozen is ad hoc signed and <strong>not notarized</strong>: Apple has not checked it, so
        macOS blocks the first launch. Opening it anyway is your own decision to make an exception for this app.
      </p>
      <p><StatusTag kind="verified" /> The steps and wording below are as tested on macOS 27.0.1. Other macOS versions may word them differently.</p>

      <component :is="h" :id="id('if-macos-blocks-refrozen')">When macOS blocks reFrozen</component>
      <ol class="install-substeps">
        <li>
          macOS shows <strong>“reFrozen” Not Opened</strong>: “Apple could not verify “reFrozen” is free of malware that may harm your
          Mac or compromise your privacy.” Choose <strong>Done</strong>, not <strong>Move to Trash</strong>.
        </li>
        <li>
          Open <strong>System Settings › Privacy &amp; Security</strong> and scroll down to <strong>Security</strong>. It says
          <strong>“reFrozen” was blocked to protect your Mac.</strong> Choose <strong>Open Anyway</strong>.
        </li>
        <li>
          macOS asks <strong>Open “reFrozen”?</strong>: “Apple is not able to verify that it is free from malware that could harm your
          Mac or compromise your privacy. Don’t open this unless you are certain it is from a trustworthy source.” Choose
          <strong>Open Anyway</strong>. macOS may ask for your password.
        </li>
      </ol>
      <StepArt :step="3" />
      <p>After that, reFrozen opens normally. <strong>Open Anyway</strong> appears only after a blocked attempt, for a limited time.</p>

      <aside class="install-callout install-callout--danger" :aria-labelledby="id('only-a-copy-you-trust')">
        <p :id="id('only-a-copy-you-trust')" class="install-callout__title">Only for a copy you trust</p>
        <p class="mb-0">
          Allow reFrozen only if it came from reFrozen's official release and its checksum matches (see
          <RouterLink :to="installPath(installSteps[0])">check the download</RouterLink> in step 1). Never turn Gatekeeper off, and
          never remove the download's quarantine attribute.
        </p>
      </aside>
    </template>

    <!-- 4. Prepare the game -->
    <template v-else-if="n === 4">
      <p class="install-lead">On its first run, reFrozen sets the game up from your own copy. Nothing from the game is downloaded: it is installed and built on your Mac.</p>
      <StepArt :step="4" />
      <ol class="install-substeps">
        <li>
          <strong>Checks your Mac:</strong> Apple silicon, the macOS version, free disk space and Apple's Command Line Tools. If the
          tools are missing, reFrozen offers Apple's installer.
        </li>
        <li>
          <strong>You choose your installers:</strong> <em>Reign of Chaos</em>, <em>The Frozen Throne</em> and the official 1.26a
          English patch. Each file is checked before anything is installed. A file that isn't a supported version is refused, with the
          reason.
        </li>
        <li>
          <strong>You enter your CD keys</strong> and owner name, as the official installer asks for them. They are stored only the way
          the official installer stores them, and are never sent anywhere or written to logs.
        </li>
        <li><strong>Installs and patches the game</strong>, checks the result, then moves it into place. Cancelling leaves nothing half-installed.</li>
        <li>
          <strong>Builds the game for your Mac:</strong> the game code from your copy is translated into native code, with progress
          shown. You can cancel and try again. See <RouterLink to="/docs/how-it-works/">How it works</RouterLink>.
          <dl class="install-facts install-facts--inline">
            <div><dt><StatusTag kind="verified" /> Build time</dt><dd>{{ release.buildTime ?? TBA }}</dd></div>
            <div><dt><StatusTag kind="verified" /> Disk space</dt><dd>{{ release.diskSpace ?? TBA }}</dd></div>
          </dl>
        </li>
        <li>
          <strong>Opens the Mini Launcher.</strong> From then on, every launch opens it: <strong>Install New Maps</strong> adds your
          <code>.w3x</code> or <code>.w3m</code> maps (an installed map is never overwritten), and <strong>Start Game</strong> starts
          the game. After a reFrozen update, the game is rebuilt once first.
        </li>
      </ol>

      <component :is="h" :id="id('where-your-data-goes')">Where your data goes</component>
      <p>
        Everything reFrozen sets up lives in <code>{{ dataFolder }}</code>: the installed game, the built game code, maps, saves, replays
        and logs. Your original installers and maps are never modified.
      </p>
      <p class="install-quiet">
        Only the versions listed under <RouterLink to="/compatibility/#game-version">Compatibility</RouterLink> are supported; other
        patch versions and <em>Reforged</em> will not work. reFrozen includes no game files, and this site does not explain how to
        obtain them in any other way.
      </p>
    </template>

    <!-- 5. Play -->
    <template v-else>
      <p class="install-lead">Press <strong>Start Game</strong>, open <strong>Single Player › Custom Game</strong> and pick a map you supply.</p>
      <p>
        v0.1.0 is offline only. LAN, private servers, iCCup and Battle.net are not part of it: their menus stay as the game has them,
        and are not supported or tested. Which DotA maps work is on the <RouterLink to="/compatibility/#dota-maps">Compatibility</RouterLink> page.
      </p>
      <StepArt :step="5" />

      <component :is="h" :id="id('controls')">Controls <StatusTag kind="verified" /></component>
      <ul class="install-keys">
        <li>
          <span><kbd>Ctrl</kbd> + <kbd aria-label="Command">⌘</kbd> + <kbd>F</kbd></span>
          <span>Switch between borderless fullscreen and a window</span>
        </li>
        <li><span class="install-keys__none">On start</span><span>reFrozen opens in borderless fullscreen</span></li>
        <li><span class="install-keys__none">Wide screens</span><span>The game's 4:3 picture is kept sharp and framed with bars, not stretched</span></li>
        <li><span class="install-keys__none">In game</span><span>Mouse and keyboard work as in the original game</span></li>
      </ul>

      <component :is="h" :id="id('known-limitations')">Known limitations</component>
      <p>
        v0.1.0 is an alpha. Its <a :href="release.page ?? undefined">release notes</a> list the known limitations, among them an
        intermittent crash in long AI matches, and saved games of the DotA v6.83d AI map that can't be loaded (the game reports an
        error, then crashes; standard maps' saves load).
      </p>

      <component :is="h" :id="id('troubleshooting')">Troubleshooting</component>
      <dl class="install-trouble">
        <div>
          <dt>An installer or the patch is refused</dt>
          <dd>It isn't a supported version; the message says why. Check the versions under <RouterLink to="/compatibility/#game-version">Compatibility</RouterLink>.</dd>
        </div>
        <div>
          <dt>Not enough disk space</dt>
          <dd>Free some space and start again. The amount needed is {{ (release.diskSpace ?? TBA).toLowerCase() }}.</dd>
        </div>
        <div>
          <dt>The setup or the build fails</dt>
          <dd>reFrozen keeps a log in the <code>logs</code> folder inside its data folder, and a failed rebuild keeps the previous working game.</dd>
        </div>
        <div>
          <dt>The game crashes</dt>
          <dd>A report is written to the <code>crashes</code> folder inside the data folder.</dd>
        </div>
        <div>
          <dt>macOS won't open reFrozen</dt>
          <dd>See <RouterLink :to="installPath(installSteps[2])">step 3</RouterLink>.</dd>
        </div>
      </dl>
      <p class="install-callout install-callout--danger">
        When you report a problem, never attach reFrozen's data folder or files from it: it holds your installed game, including your
        encoded CD keys. A crash report on its own can be shared.
      </p>

      <component :is="h" :id="id('uninstall')">Uninstall</component>
      <ol class="install-substeps">
        <li>Quit reFrozen.</li>
        <li>Move <strong>reFrozen</strong> from Applications to the Bin.</li>
        <li>Delete the folder <code>{{ dataFolder }}</code>. It holds your installed game, including your encoded CD keys.</li>
      </ol>
      <p class="install-quiet">Your original installers and maps are never touched, so you can set reFrozen up again later.</p>
    </template>
  </div>
</template>
