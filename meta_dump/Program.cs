using System;
using System.IO;
using LibCpp2IL;
using LibCpp2IL.Metadata;

class Program
{
    static void Main(string[] args)
    {
        var metaPath = args[0];
        var gameDataPath = args[1];
        var ver = LibCpp2IlMain.DetermineUnityVersion(null, gameDataPath);
        var meta = Il2CppMetadata.ReadFrom(File.ReadAllBytes(metaPath), ver);
        Console.Error.WriteLine($"version={ver} literals={meta.stringLiterals.Length}");
        uint n = (uint)meta.stringLiterals.Length;
        var litData = meta.metadataHeader.stringLiteralData;
        for (uint i = 0; i < n; i++)
        {
            var start = (long)litData.Offset + (long)meta.stringLiterals[i].dataIndex;
            var end = i + 1 < n ? (long)litData.Offset + (long)meta.stringLiterals[i + 1].dataIndex
                                : (long)litData.Offset + (long)litData.Size;
            var s = meta.GetStringLiteralFromIndex(i);
            var esc = s.Replace("\\", "\\\\").Replace("\n", "\\n").Replace("\r", "\\r").Replace("\t", "\\t");
            Console.WriteLine($"{i}\t{start}\t{end - start}\t{esc}");
        }
    }
}
