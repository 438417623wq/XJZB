public class _Dbg232 {
    public static void main(String[] a) {
        com.xjzb.rts.core.LockstepLink.Hub h =
                new com.xjzb.rts.core.LockstepLink.Hub(2, 0, 0, false, 99L);
        h.chop = true; h.chopMax = 7;
        com.xjzb.rts.core.LockstepLink.Link l0 = h.end(0);
        com.xjzb.rts.core.LockstepLink.Link l1 = h.end(1);
        l1.send("L 0 1 move 1,2,3,4 400 400");
        int polls = 0, partialPolls = 0;
        java.util.List<String> got = new java.util.ArrayList<>();
        for (int i = 0; i < 12 && got.isEmpty(); i++) {
            java.util.List<String> r = l0.poll();
            polls++;
            if (r.isEmpty()) partialPolls++;
            got.addAll(r);
        }
        System.out.println("chopped delivery: polls=" + polls + " emptyPolls=" + partialPolls
                + " got=" + got);
        System.out.println("full line intact=" + (got.size() == 1
                && got.get(0).equals("L 0 1 move 1,2,3,4 400 400")));
        // and a long UTF-8 line must survive mid-character splits
        com.xjzb.rts.core.LockstepLink.Hub h2 =
                new com.xjzb.rts.core.LockstepLink.Hub(2, 0, 0, false, 7L);
        h2.chop = true; h2.chopMax = 1;
        com.xjzb.rts.core.LockstepLink.Link a0 = h2.end(0);
        com.xjzb.rts.core.LockstepLink.Link a1 = h2.end(1);
        String cn = "L 5 2 build 3 barracks 中文坐标测试 640 480";
        a1.send(cn);
        java.util.List<String> out = new java.util.ArrayList<>();
        for (int i = 0; i < 200 && out.isEmpty(); i++) out.addAll(a0.poll());
        System.out.println("1-byte chopping, utf8 intact=" + (out.size() == 1
                && out.get(0).equals(cn)) + " -> " + out);
    }
}