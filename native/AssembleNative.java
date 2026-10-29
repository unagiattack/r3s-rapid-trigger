// @category R3S Rapid Trigger
// Assemble only authored source in an isolated binary; never import stock here.
import java.io.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.regex.*;
import ghidra.app.script.GhidraScript;
import ghidra.app.plugin.assembler.*;
import ghidra.program.model.listing.Instruction;
import ghidra.program.model.lang.Register;

public class AssembleNative extends GhidraScript {
    static class Row {
        long address; int width; String text; boolean data;
        Row(long a, int w, String t, boolean d) { address=a; width=w; text=t; data=d; }
    }
    @Override public void run() throws Exception {
        String[] args=getScriptArgs();
        if(args.length!=2) throw new IOException("Pass source file and output directory.");
        Path output=Paths.get(args[1]); Files.createDirectories(output);
        Map<String,Long> labels=new LinkedHashMap<>();
        List<Row> rows=new ArrayList<>(); Set<Long> occupied=new HashSet<>();
        long pc=0;
        for(String raw:Files.readAllLines(Paths.get(args[0]),StandardCharsets.UTF_8)) {
            String line=raw.trim();
            if(line.isEmpty()||line.startsWith(";")) continue;
            if(line.startsWith(".org ")) { pc=Long.decode(line.substring(5)); continue; }
            if(line.equals(".align4")) { pc=(pc+3)&~3L; continue; }
            if(line.endsWith(":")) {
                if(labels.put(line.substring(0,line.length()-1),pc)!=null)
                    throw new IOException("Duplicate label.");
                continue;
            }
            int width; Row row=null;
            if(line.startsWith(".stock16 ")) {
                // Reserve a hole. Manufacturer words are derived by Python locally.
                width=2;
            } else if(line.startsWith(".word ")) {
                width=4; row=new Row(pc,width,line.substring(6),true);
            } else {
                String[] fields=line.split("\\|",2); width=Integer.parseInt(fields[0]);
                if(width!=2&&width!=4) throw new IOException("Invalid instruction width.");
                row=new Row(pc,width,fields[1],false);
            }
            if(pc<0x0801e394L||pc+width>0x08020000L)
                throw new IOException("Outside isolated native region.");
            for(long at=pc;at<pc+width;at++) if(!occupied.add(at))
                throw new IOException("Overlapping source rows.");
            if(row!=null) rows.add(row);
            pc+=width;
        }
        // Reject any nonblank input image, including manufacturer firmware.
        byte[] blank=new byte[0x2000];
        currentProgram.getMemory().getBytes(toAddr(0x0801e000L),blank);
        for(byte b:blank) if(b!=0) throw new IOException("Input must be a zero-filled isolated binary.");
        Register thumb=currentProgram.getRegister("TMode");
        currentProgram.getProgramContext().setValue(thumb,toAddr(0x0801e000L),toAddr(0x0801ffffL),BigInteger.ONE);
        Assembler assembler=Assemblers.getAssembler(currentProgram);
        Pattern reference=Pattern.compile("<([a-z_][a-z_0-9]*)>");
        for(Row row:rows) {
            byte[] bytes;
            if(row.data) {
                long value=Long.decode(row.text); bytes=new byte[4];
                for(int i=0;i<4;i++) bytes[i]=(byte)(value>>(i*8));
            } else {
                Matcher matcher=reference.matcher(row.text); StringBuffer resolved=new StringBuffer();
                while(matcher.find()) {
                    Long address=labels.get(matcher.group(1));
                    if(address==null) throw new IOException("Missing label.");
                    matcher.appendReplacement(resolved,"0x"+Long.toHexString(address));
                }
                matcher.appendTail(resolved);
                bytes=assembler.assembleLine(toAddr(row.address),resolved.toString());
                if(bytes.length!=row.width) throw new IOException("Instruction width mismatch.");
            }
            currentProgram.getMemory().setBytes(toAddr(row.address),bytes);
        }
        try(PrintWriter listing=new PrintWriter(Files.newBufferedWriter(output.resolve("native-listing.txt"),StandardCharsets.UTF_8))) {
            for(Row row:rows) {
                byte[] bytes=new byte[row.width];
                currentProgram.getMemory().getBytes(toAddr(row.address),bytes);
                String text="DATA";
                if(!row.data) {
                    disassemble(toAddr(row.address)); Instruction instruction=getInstructionAt(toAddr(row.address));
                    if(instruction==null||instruction.getLength()!=row.width)
                        throw new IOException("Disassembly width mismatch.");
                    text=instruction.toString();
                }
                listing.printf("%08x | %s | %s%n",row.address,HexFormat.of().formatHex(bytes),text);
            }
            listing.flush(); if(listing.checkError()) throw new IOException("Could not write native listing.");
        }
        println("Authored native listing written; stock-derived words omitted.");
    }
}
