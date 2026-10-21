/** v2.29 focused runner: the mission engine tests plus the campaign walk. */
public class _RunV229 {
    public static void main(String[] a) throws Exception {
        GameDesktop.readManifestPublic();
        System.out.println("[missions]");
        GameDesktop.missionTest1();
        GameDesktop.missionTest2();
        GameDesktop.missionTest3();
        GameDesktop.missionTest4();
        GameDesktop.missionTest5();
        System.out.println("[v229]");
        GameDesktop.v229Tests();
    }
}