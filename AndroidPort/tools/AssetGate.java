import java.security.MessageDigest;
import java.util.Enumeration;
import java.util.HashMap;
import java.util.Map;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;

/** v2.41 asset gate: the version touched only Java code, so every assets/
 *  entry in the two APKs must hash identically. Mirrors verify_v223_gate.py. */
public class AssetGate {
    public static void main(String[] args) throws Exception {
        String oldApk = "F:/KF/XJZB/AndroidPort/星际争霸RTS-v2.39.apk";
        String newApk = "F:/KF/XJZB/AndroidPort/星际争霸RTS-v2.41.apk";
        Map<String, String> a = read(oldApk), b = read(newApk);
        int same = 0, onlyNew = 0, onlyOld = 0, diff = 0;
        StringBuilder diffs = new StringBuilder();
        for (Map.Entry<String, String> e : b.entrySet()) {
            String ha = a.get(e.getKey());
            if (ha == null) { onlyNew++; diffs.append("only_new ").append(e.getKey()).append('\n'); }
            else if (ha.equals(e.getValue())) same++;
            else { diff++; diffs.append("diff ").append(e.getKey()).append('\n'); }
        }
        for (String k : a.keySet()) if (!b.containsKey(k)) { onlyOld++; diffs.append("only_old ").append(k).append('\n'); }
        System.out.printf("素材比对: same=%d diff=%d only_apk=%d only_disk=%d  GATE: %s%n",
                same, diff, onlyOld, onlyNew, (diff == 0 && onlyOld == 0 && onlyNew == 0) ? "PASS" : "FAIL");
        if (diffs.length() > 0) System.out.print(diffs);
    }

    static Map<String, String> read(String apk) throws Exception {
        MessageDigest md = MessageDigest.getInstance("SHA-256");
        Map<String, String> out = new HashMap<>();
        try (ZipFile z = new ZipFile(apk)) {
            Enumeration<? extends ZipEntry> en = z.entries();
            while (en.hasMoreElements()) {
                ZipEntry e = en.nextElement();
                String n = e.getName();
                if (n.startsWith("assets/") && !n.endsWith("/")) {
                    byte[] data = z.getInputStream(e).readAllBytes();
                    StringBuilder sb = new StringBuilder();
                    for (byte x : md.digest(data)) sb.append(String.format("%02x", x));
                    out.put(n.substring("assets/".length()), sb.toString());
                }
            }
        }
        return out;
    }
}
