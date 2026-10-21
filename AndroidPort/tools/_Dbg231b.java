public class _Dbg231b {
    public static void main(String[] a) {
        com.xjzb.rts.core.LockstepLink.Hub h =
                new com.xjzb.rts.core.LockstepLink.Hub(2, 0, 0, false, 1L);
        com.xjzb.rts.core.LockstepLink.Link l0 = h.end(0);
        com.xjzb.rts.core.LockstepLink.Link l1 = h.end(1);
        System.out.println("frame=" + h.frame());
        l1.send("L 0 1 hello");
        System.out.println("l0 poll @frame" + h.frame() + " -> " + l0.poll());
        h.tick();
        System.out.println("l0 poll @frame" + h.frame() + " -> " + l0.poll());
        System.out.println("decode 'L 0 1 ' -> " + com.xjzb.rts.core.Lockstep.decode("L 0 1 "));
        System.out.println("decode 'L 0 1 hello' -> " + com.xjzb.rts.core.Lockstep.decode("L 0 1 hello"));
        com.xjzb.rts.core.Lockstep ls = new com.xjzb.rts.core.Lockstep(2);
        ls.submit(1, "hello");
        System.out.println("after b report ready=" + ls.ready() + " row1='" + "?" + "'");
        ls.submit(0, "");
        System.out.println("after a report ready=" + ls.ready() + " release=" + ls.release().size());
    }
}