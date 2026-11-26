using System;
using System.Linq;
using Mono.Cecil;
using Mono.Cecil.Cil;

class Program
{
    static void Main(string[] args)
    {
        var path = args[0];
        var resolver = new DefaultAssemblyResolver();
        var managedDir = System.IO.Path.GetDirectoryName(path);
        resolver.AddSearchDirectory(managedDir);
        var asm = AssemblyDefinition.ReadAssembly(path, new ReaderParameters { AssemblyResolver = resolver });
        var mod = asm.MainModule;
        var t = mod.GetType("InitScene2");
        var m = t.Methods.First(x => x.Name == "CheckHMD");
        Console.WriteLine("找到 CheckHMD");

        // find the GetKey(Home) call inside the !isPresent block, patch its branch to fall through
        var body = m.Body;
        var il = body.Instructions;
        var edited = 0;
        for (int i = 0; i < il.Count; i++)
        {
            var ins = il[i];
            if (ins.OpCode == OpCodes.Call && ins.Operand is MethodReference mr &&
                mr.Name == "GetKey" && mr.DeclaringType.Name == "Input")
            {
                // next meaningful instruction = branch (brtrue/brfalse) skipping the ForceMouse block
                var next = il[i + 1];
                if (next.OpCode == OpCodes.Brfalse || next.OpCode == OpCodes.Brtrue)
                {
                    // NOP the branch: always fall through into the ForceMouse=true path
                    var nop = Instruction.Create(OpCodes.Nop);
                    var oldOp = next.OpCode;
                    var oldOperand = next.Operand;
                    il.Insert(i + 1, nop);
                    next.OpCode = OpCodes.Nop;
                    next.Operand = null;
                    Console.WriteLine($"  patched branch after GetKey ({oldOp} {oldOperand} -> NOP)");
                    edited++;
                    break; // only the HMD check's GetKey(Home) — stop at first
                }
            }
        }
        if (edited == 0)
        {
            Console.WriteLine("没找到目标分支,列出所有 GetKey 调用:");
            for (int i = 0; i < il.Count; i++)
            {
                var ins = il[i];
                if (ins.OpCode == OpCodes.Call && ins.Operand is MethodReference mr &&
                    mr.Name == "GetKey" && mr.DeclaringType.Name == "Input")
                {
                    Console.WriteLine($"  @{i}: {il[i-2]} / {il[i-1]} / {ins} / {il[i+1]}");
                }
            }
            Environment.Exit(1);
        }
        asm.Write(path + ".patched");
        Console.WriteLine("已写出 " + path + ".patched");
    }
}
