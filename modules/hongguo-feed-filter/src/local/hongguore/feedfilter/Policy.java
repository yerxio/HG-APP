package local.hongguore.feedfilter;

/** Exact model-family classifier, matching the app's own isAdData predicate.
 * Unknown models are retained; absence of video data is NOT an ad classifier. */
public final class Policy {
    public static final String NORMAL = "KEEP";
    public static String classify(Object value) {
        if (value == null) return NORMAL;
        for (Class<?> c = value.getClass(); c != null; c = c.getSuperclass()) {
            String name = c.getName();
            if (name.equals("com.bytedance.tomato.onestop.base.model.OneStopAdModel$AdRemainNaturalMaterials"))
                return "NATURAL_PROMOTION";
            if (name.equals("com.bytedance.tomato.onestop.base.model.OneStopAdModel"))
                return "ONE_STOP_AD";
            if (name.equals("com.dragon.read.ad.onestop.serieslandscape.model.LandscapeOneStopAdModel"))
                return "LANDSCAPE_AD";
        }
        return NORMAL;
    }
    public static boolean reject(Object value, boolean blocking) {
        return blocking && !NORMAL.equals(classify(value));
    }
}
