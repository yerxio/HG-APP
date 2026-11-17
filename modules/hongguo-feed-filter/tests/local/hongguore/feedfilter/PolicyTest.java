package local.hongguore.feedfilter;
import java.util.ArrayList;
import java.util.List;
import com.bytedance.tomato.onestop.base.model.OneStopAdModel;
import com.dragon.read.ad.onestop.serieslandscape.model.LandscapeOneStopAdModel;
public final class PolicyTest {
    static class NormalVideo { }
    static class UnknownCard { }
    static class AdSubclass extends OneStopAdModel { }
    private static void check(boolean value, String label) {
        if (!value) throw new AssertionError(label);
        System.out.println("PASS " + label);
    }
    public static void main(String[] args) {
        boolean block = args.length > 0 && args[0].equals("block");
        Object normal = new NormalVideo();
        Object natural = new OneStopAdModel.AdRemainNaturalMaterials();
        Object commercial = new OneStopAdModel();
        Object landscape = new LandscapeOneStopAdModel();
        check(Policy.classify(normal).equals("KEEP"), "normal video retained");
        check(Policy.classify(null).equals("KEEP"), "null retained");
        check(Policy.classify(new UnknownCard()).equals("KEEP"), "unknown card retained");
        check(Policy.classify(new AdSubclass()).equals("ONE_STOP_AD"), "ad subclass recognized");
        check(Policy.classify(natural).equals("NATURAL_PROMOTION"), "natural promotion recognized");
        check(Policy.classify(landscape).equals("LANDSCAPE_AD"), "landscape wrapper recognized");
        List<Object> list = new ArrayList<>();
        for (Object value : new Object[]{normal, natural, commercial, landscape}) {
            if (!Policy.reject(value, block)) list.add(value);
        }
        check(list.get(0) == normal, "normal object identity unchanged");
        check(list.size() == (block ? 1 : 4), "insertion gate size=" + list.size());
        System.out.println("MODE=" + (block ? "BLOCK" : "OBSERVE") + " normal=1 ads=" + (list.size()-1));
        System.out.println("NOTE: JVM fixture test, not device hook validation");
    }
}
