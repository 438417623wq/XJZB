import java.awt.*;
public class Fit {
  public static void main(String[] a){
    int[] Hs = {1080, 720, 480};
    int[] ui = {2, 2, 1};
    for (int k=0;k<Hs.length;k++){
      int H=Hs[k], u=ui[k];
      float titleH=34*u, backH=40*u, rowGap=8*u;
      float bodyTop=H*0.10f+titleH;
      float bodyBottom=H-16*u-backH-rowGap;
      float rowPitch=(bodyBottom-bodyTop)/5f;
      float ctrlH=Math.max(20*u, Math.min(38*u, rowPitch-20*u));
      float lastBottom = bodyTop + 4*rowPitch + 18*u + ctrlH;
      float backTop = H-16*u-backH;
      System.out.printf("H=%d u=%d rowPitch=%.1f ctrlH=%.1f lastBottom=%.1f backTop=%.1f overlap=%s%n",
        H,u,rowPitch,ctrlH,lastBottom,backTop,(lastBottom>backTop?"YES ***":"no"));
    }
  }
}
