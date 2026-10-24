// Dump every instruction Ghidra decoded in executable blocks (address,
// length, flow type) and every executable byte range that is not an
// instruction, for scripts/validate_lift.py's coverage audit.
//
// Headless (after analysis, read-only):
//   analyzeHeadless <projdir> <project> -process <module> -noanalysis -readOnly \
//     -scriptPath scripts/ghidra -postScript ExportInstructions.java <out_dir>
// Writes <out_dir>/instructions.tsv and <out_dir>/noncode.tsv.
//@category Recomp

import java.io.File;
import java.io.PrintWriter;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.address.AddressSet;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.listing.InstructionIterator;
import ghidra.program.model.mem.MemoryBlock;

public class ExportInstructions extends GhidraScript {
  @Override
  protected void run() throws Exception {
    String dir = getScriptArgs().length > 0 ? getScriptArgs()[0] : ".";
    AddressSet exec = new AddressSet();
    for (MemoryBlock b : currentProgram.getMemory().getBlocks())
      if (b.isExecute() && b.isInitialized()) exec.add(b.getStart(), b.getEnd());

    AddressSet code = new AddressSet();
    long count = 0;
    try (PrintWriter w = new PrintWriter(new File(dir, "instructions.tsv"))) {
      w.println("va\tlen\tflow\tmnemonic");
      InstructionIterator it = currentProgram.getListing().getInstructions(exec, true);
      while (it.hasNext() && !monitor.isCancelled()) {
        Instruction in = it.next();
        Address a = in.getAddress();
        code.add(a, in.getMaxAddress());
        w.printf("%08X\t%d\t%s\t%s%n", a.getOffset(), in.getLength(), in.getFlowType(),
            in.getMnemonicString());
        count++;
      }
    }
    AddressSet rest = exec.subtract(code);
    long bytes = 0;
    try (PrintWriter w = new PrintWriter(new File(dir, "noncode.tsv"))) {
      w.println("start\tend");
      for (var r : rest.getAddressRanges()) {
        w.printf("%08X\t%08X%n", r.getMinAddress().getOffset(), r.getMaxAddress().getOffset());
        bytes += r.getLength();
      }
    }
    println("ExportInstructions: " + count + " instructions, " + code.getNumAddresses()
        + " code bytes, " + bytes + " non-code bytes in executable blocks");
  }
}
