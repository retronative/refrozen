// Game functions reFrozen replaces (config/game.manifest, "replace"). The lifter keeps
// each one's translated body as f_<address>_lifted; the replacement runs it except
// where noted.
#include "runtime/lifted.h"

namespace recomp::gen {
using namespace ::recomp::lift;

void f_6F40B6C0_lifted(::recomp::Ctx& c);
void f_6F26FC10_lifted(::recomp::Ctx& c);

namespace {

// Event response helpers (attack and damage events). A trigger that reads one after a
// wait can find the event's data gone (ecx 0). Instead of a fault, the helper takes its
// own path for a unit that has left the game, so the response is "no unit".
void NoUnit(::recomp::Ctx& c, uint32_t link) {
  LIFT_ENTER
  (void)B;
  eax = Logic<4>(F, 0xFFFFFFFFu & 0xFFFFFFFFu);
  ecx = Add<4>(F, ecx, link);
  (void)Sub<4>(F, eax, 0xFFFFFFFFu);
  eax = Logic<4>(F, eax ^ eax);
  esp += 4u;
  LIFT_SPILL
}

}  // namespace

void f_6F40B6C0(::recomp::Ctx& c) {
  if (c.ecx == 0) return NoUnit(c, 0x38u);
  LIFT_MUSTTAIL return f_6F40B6C0_lifted(c);
}

void f_6F26FC10(::recomp::Ctx& c) {
  if (c.ecx == 0) return NoUnit(c, 0x2Cu);
  LIFT_MUSTTAIL return f_6F26FC10_lifted(c);
}

}  // namespace recomp::gen
