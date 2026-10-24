/* Development oracle only (never part of a player's pipeline): replays a
 * scripted key sequence into the official 1.26a client running under Wine,
 * so the oracle walks the same menus as the native TEST_INPUT scripts.
 *
 *   wine oracle_keys.exe <script>      (built by scripts/oracle_menus.sh)
 *
 * Script lines, times in seconds since the game's window appeared:
 *   <t> key <name> [seconds]   WM_KEYDOWN, then WM_KEYUP after the hold
 *                              (default 0.08); names as TEST_INPUT's SDL
 *                              scancode names: A-Z, 0-9, Return, Escape,
 *                              Space, Tab, Up, Down, Left, Right
 *   <t> size <w> <h>           resizes the window so its client area is
 *                              w x h (SetWindowPos; the game gets WM_SIZE)
 *   <t> shot <name>            creates <name>.req beside the script,
 *                              for the caller to capture the window; the
 *                              end is __done.req, a failure __fail.req (Wine
 *                              holds a console program's stdout until it
 *                              exits, so stdout cannot carry the timing)
 * '#' starts a comment. Keys are posted to the window (the game's own
 * TranslateMessage makes the WM_CHARs), so the host pointer and keyboard
 * are never touched. Freestanding: no CRT, no SDK headers.
 */
typedef unsigned int UINT;
typedef unsigned long DWORD;
typedef int BOOL;
typedef void *HANDLE;
typedef void *HWND;

__declspec(dllimport) HWND __stdcall FindWindowA(const char *, const char *);
__declspec(dllimport) BOOL __stdcall PostMessageA(HWND, UINT, UINT, long);
__declspec(dllimport) UINT __stdcall MapVirtualKeyA(UINT, UINT);
struct Rect { long l, t, r, b; };
__declspec(dllimport) BOOL __stdcall GetWindowRect(HWND, struct Rect *);
__declspec(dllimport) BOOL __stdcall GetClientRect(HWND, struct Rect *);
__declspec(dllimport) BOOL __stdcall SetWindowPos(HWND, HWND, int, int, int, int, UINT);
__declspec(dllimport) void __stdcall Sleep(DWORD);
__declspec(dllimport) DWORD __stdcall GetTickCount(void);
__declspec(dllimport) char *__stdcall GetCommandLineA(void);
__declspec(dllimport) HANDLE __stdcall CreateFileA(const char *, DWORD, DWORD, void *, DWORD, DWORD, HANDLE);
__declspec(dllimport) BOOL __stdcall ReadFile(HANDLE, void *, DWORD, DWORD *, void *);
__declspec(dllimport) BOOL __stdcall WriteFile(HANDLE, const void *, DWORD, DWORD *, void *);
__declspec(dllimport) HANDLE __stdcall GetStdHandle(DWORD);
__declspec(dllimport) BOOL __stdcall CloseHandle(HANDLE);
__declspec(dllimport) void __stdcall ExitProcess(UINT);

enum { WM_KEYDOWN = 0x100, WM_KEYUP = 0x101, MAX_EVENTS = 512 };

struct Event {
  DWORD at_ms;
  int kind; /* 0 key down, 1 key up, 2 shot, 3 size (vk = w << 16 | h) */
  UINT vk;
  char name[32];
};

static struct Event events[MAX_EVENTS];
static int nevents;
static char script[16384];

static void out(const char *s) {
  DWORD n = 0, w;
  while (s[n]) n++;
  WriteFile(GetStdHandle((DWORD)-11), s, n, &w, 0);
}

static const char *script_path;

/* Creates <name>.req beside the script. */
static void touch_req(const char *name) {
  char req[300];
  int n = 0, k = 0;
  for (; script_path[k] && n < 256; k++) req[n++] = script_path[k];
  while (n && req[n - 1] != '\\' && req[n - 1] != '/') n--;
  for (k = 0; name[k] && k < 32; k++) req[n++] = name[k];
  for (const char *x = ".req"; *x; x++) req[n++] = *x;
  req[n] = 0;
  HANDLE r = CreateFileA(req, 0x40000000u /* GENERIC_WRITE */, 0, 0, 2 /* CREATE_ALWAYS */, 0, 0);
  if (r != (HANDLE)-1) CloseHandle(r);
}

/* The caller learns of the end from __done.req or __fail.req (it may not
 * see this process: under explorer /desktop the launcher returns at once). */
static void fail(const char *msg) {
  out("oracle_keys: ");
  out(msg);
  out("\n");
  if (script_path) touch_req("__fail");
  ExitProcess(2);
}

static int eq(const char *a, const char *b) {
  while (*a && *a == *b) a++, b++;
  return *a == *b;
}

/* The game's window, waited for up to 10 s: the -opengl renderer replaces
 * the window it first created, so there are moments without one. */
static HWND game_window(void) {
  HWND w = 0;
  for (int i = 0; i < 100 && !(w = FindWindowA("Warcraft III", 0)); i++) Sleep(100);
  if (!w) fail("the Warcraft III window is gone");
  return w;
}

static UINT vk_for(const char *n) {
  if (n[0] && !n[1]) {
    if (n[0] >= 'A' && n[0] <= 'Z') return (UINT)n[0];
    if (n[0] >= 'a' && n[0] <= 'z') return (UINT)(n[0] - 32);
    if (n[0] >= '0' && n[0] <= '9') return (UINT)n[0];
  }
  if (eq(n, "Return")) return 0x0D;
  if (eq(n, "Escape")) return 0x1B;
  if (eq(n, "Space")) return 0x20;
  if (eq(n, "Tab")) return 0x09;
  if (eq(n, "Left")) return 0x25;
  if (eq(n, "Up")) return 0x26;
  if (eq(n, "Right")) return 0x27;
  if (eq(n, "Down")) return 0x28;
  return 0;
}

/* Seconds with an optional fraction ("12", "20.35") to milliseconds. */
static const char *parse_ms(const char *p, DWORD *ms) {
  DWORD whole = 0, frac = 0, scale = 1000;
  while (*p >= '0' && *p <= '9') whole = whole * 10 + (DWORD)(*p++ - '0');
  if (*p == '.')
    for (p++; *p >= '0' && *p <= '9'; p++)
      if (scale > 1) scale /= 10, frac += (DWORD)(*p - '0') * scale;
  *ms = whole * 1000 + frac;
  return p;
}

static const char *word(const char *p, char *buf, int cap) {
  int i = 0;
  while (*p == ' ' || *p == '\t') p++;
  while (*p && *p != ' ' && *p != '\t' && *p != '\n' && *p != '\r' && *p != '#')
    if (i < cap - 1) buf[i++] = *p++;
    else p++;
  buf[i] = 0;
  return p;
}

static void add(DWORD at, int kind, UINT vk, const char *name) {
  if (nevents == MAX_EVENTS) fail("too many events");
  events[nevents].at_ms = at;
  events[nevents].kind = kind;
  events[nevents].vk = vk;
  int i = 0;
  if (name)
    for (; name[i] && i < 31; i++) events[nevents].name[i] = name[i];
  events[nevents].name[i] = 0;
  nevents++;
}

static void parse(void) {
  const char *p = script;
  while (*p) {
    char cmd[16], a[32], b[32];
    DWORD at, hold = 80;
    while (*p == ' ' || *p == '\t') p++;
    if (*p >= '0' && *p <= '9') {
      p = parse_ms(p, &at);
      p = word(p, cmd, sizeof cmd);
      p = word(p, a, sizeof a);
      p = word(p, b, sizeof b);
      if (eq(cmd, "key")) {
        UINT vk = vk_for(a);
        if (!vk) fail("unknown key name");
        if (b[0]) parse_ms(b, &hold);
        add(at, 0, vk, 0);
        add(at + hold, 1, vk, 0);
      } else if (eq(cmd, "size") && a[0] && b[0]) {
        DWORD w, h;
        parse_ms(a, &w);
        parse_ms(b, &h);
        add(at, 3, (UINT)((w / 1000) << 16 | (h / 1000)), 0);
      } else if (eq(cmd, "shot") && a[0]) {
        add(at, 2, 0, a);
      } else {
        fail("bad script line");
      }
    }
    while (*p && *p != '\n') p++;
    if (*p) p++;
  }
  /* Stable insertion sort by time. */
  for (int i = 1; i < nevents; i++) {
    struct Event e = events[i];
    int j = i - 1;
    for (; j >= 0 && events[j].at_ms > e.at_ms; j--) events[j + 1] = events[j];
    events[j + 1] = e;
  }
}

void start(void) {
  /* The script path is the command line's last argument. */
  char *cl = GetCommandLineA(), *path = cl;
  for (char *q = cl; *q; q++)
    if (*q == ' ' && q[1] && q[1] != ' ') path = q + 1;
  if (*path == '"') {
    path++;
    for (char *q = path; *q; q++)
      if (*q == '"') *q = 0;
  }
  script_path = path;
  HANDLE f = CreateFileA(path, 0x80000000u /* GENERIC_READ */, 1, 0, 3 /* OPEN_EXISTING */, 0, 0);
  if (f == (HANDLE)-1) fail("cannot open script");
  DWORD got = 0;
  if (!ReadFile(f, script, sizeof script - 1, &got, 0)) fail("cannot read script");
  script[got] = 0;
  parse();

  HWND w = 0;
  for (int i = 0; i < 1200 && !(w = FindWindowA("Warcraft III", 0)); i++) Sleep(100);
  if (!w) fail("no Warcraft III window after 120 s");
  out("WINDOW\n");
  DWORD t0 = GetTickCount();
  for (int i = 0; i < nevents; i++) {
    struct Event *e = &events[i];
    while (GetTickCount() - t0 < e->at_ms) Sleep(5);
    if (e->kind == 2) {
      touch_req(e->name);
      continue;
    }
    if (e->kind == 3) {
      struct Rect wr, cr;
      w = game_window();
      if (!GetWindowRect(w, &wr) || !GetClientRect(w, &cr)) fail("GetWindowRect failed");
      int cw = (int)(e->vk >> 16), ch = (int)(e->vk & 0xFFFF);
      int fw = (int)((wr.r - wr.l) - (cr.r - cr.l)), fh = (int)((wr.b - wr.t) - (cr.b - cr.t));
      if (!SetWindowPos(w, 0, 0, 0, cw + fw, ch + fh, 0x16 /* NOMOVE|NOZORDER|NOACTIVATE */))
        fail("SetWindowPos failed");
      continue;
    }
    w = game_window();  /* again for every key (see game_window) */
    UINT sc = MapVirtualKeyA(e->vk, 0 /* MAPVK_VK_TO_VSC */);
    long lp = 1 | (long)(sc << 16);
    if (e->kind == 1) lp |= (long)0xC0000000u;
    if (!PostMessageA(w, e->kind ? WM_KEYUP : WM_KEYDOWN, e->vk, lp)) fail("PostMessageA failed");
  }
  touch_req("__done");
  ExitProcess(0);
}
