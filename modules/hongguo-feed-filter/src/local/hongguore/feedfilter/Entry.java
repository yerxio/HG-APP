package local.hongguore.feedfilter;

import android.app.Application;
import android.content.Context;
import android.content.pm.PackageInfo;
import android.util.Log;
import java.lang.reflect.Method;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import de.robv.android.xposed.IXposedHookLoadPackage;
import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedBridge;
import de.robv.android.xposed.callbacks.XC_LoadPackage;

public final class Entry implements IXposedHookLoadPackage {
    private static final String TARGET = "com.phoenix.read";
    private static final String ADAPTER = "com.dragon.read.component.shortvideo.impl.v2.view.adapter.a";
    private static final String TAG = "HGFeedFilter";
    private static final AtomicBoolean STARTED = new AtomicBoolean();
    private static final AtomicInteger LOGS = new AtomicInteger();

    private static void log(String text) {
        if (LOGS.incrementAndGet() <= 400) {
            Log.i(TAG, text);
            XposedBridge.log(TAG + " " + text);
        }
    }

    @Override public void handleLoadPackage(XC_LoadPackage.LoadPackageParam p) throws Throwable {
        if (!TARGET.equals(p.packageName) || !TARGET.equals(p.processName)) return;
        XposedBridge.hookMethod(Application.class.getDeclaredMethod("attach", Context.class), new XC_MethodHook() {
            @Override protected void afterHookedMethod(MethodHookParam param) {
                if (!STARTED.compareAndSet(false, true)) return;
                try {
                    Context context = (Context) param.args[0];
                    PackageInfo info = context.getPackageManager().getPackageInfo(TARGET, 0);
                    if (info.versionCode != 74532 || !"7.4.5.32".equals(info.versionName)) {
                        log("VERSION_MISMATCH: hooks disabled, version=" + info.versionName);
                        return;
                    }
                    install(context.getClassLoader());
                } catch (Throwable error) {
                    log("INIT_ERROR: " + error.getClass().getName() + ": " + error.getMessage());
                }
            }
        });
    }

    private static void install(ClassLoader loader) throws Exception {
        Class<?> adapter = Class.forName(ADAPTER, false, loader);
        // Resolve every required method before installing any of the insertion gates.
        Method i2 = adapter.getDeclaredMethod("I2", int.class, int.class, Object.class);
        Method y0 = adapter.getDeclaredMethod("Y0", int.class, int.class, String.class, Object.class);
        Method p4 = adapter.getDeclaredMethod("P4", int.class, Object.class);
        Method q0 = adapter.getDeclaredMethod("Q0", int.class, Object.class);
        if (i2.getReturnType() != boolean.class || y0.getReturnType() != boolean.class
                || p4.getReturnType() != boolean.class || q0.getReturnType() != void.class)
            throw new NoSuchMethodException("unexpected return types");
        gate(i2, 2, false);
        gate(y0, 3, false); // Reject BEFORE Y0 can delete an existing item using J1.
        gate(p4, 1, false);
        gate(q0, 1, true);  // Reject ad replacement, preserving the previous item.
        log("READY version=74532 mode=" + (BuildMode.BLOCK ? "BLOCK" : "OBSERVE") + " required_gates=4");

        try {
            Class<?> fullscreen = Class.forName("com.dragon.read.component.shortvideo.impl.fullscreen.d", false, loader);
            gate(fullscreen.getDeclaredMethod("P4", int.class, Object.class), 1, false);
        } catch (Throwable error) { log("OPTIONAL_FULLSCREEN: " + error.getClass().getSimpleName()); }

        // Observation only: no hiding views, no changing adapter counts or indices.
        try {
            Class<?> recycler = Class.forName("tx4.f", false, loader);
            for (Method m : recycler.getDeclaredMethods()) {
                Class<?>[] ps = m.getParameterTypes();
                if (!m.getName().equals("onBindViewHolder") || m.isBridge() || ps.length != 2
                        || ps[1] != int.class) continue;
                XposedBridge.hookMethod(m, new XC_MethodHook() {
                    @Override protected void afterHookedMethod(MethodHookParam param) {
                        if (!adapter.isInstance(param.thisObject)) return;
                        try {
                            Object value = recycler.getMethod("getData", int.class).invoke(param.thisObject, param.args[1]);
                            log("BIND position=" + param.args[1] + " " + describe(value));
                        } catch (Throwable ignored) { }
                    }
                });
            }
        } catch (Throwable error) { log("OPTIONAL_BIND: " + error.getClass().getSimpleName()); }
    }

    private static void gate(Method method, int objectIndex, boolean voidResult) {
        XposedBridge.hookMethod(method, new XC_MethodHook() {
            @Override protected void beforeHookedMethod(MethodHookParam param) {
                Object value = param.args[objectIndex];
                boolean rejected = Policy.reject(value, BuildMode.BLOCK);
                log((rejected ? "BLOCK " : "PASS ") + method.getName() + " " + describe(value));
                if (rejected) param.setResult(voidResult ? null : Boolean.FALSE);
            }
        });
    }

    private static String describe(Object value) {
        if (value == null) return "model=null class=KEEP";
        String text = "model=" + value.getClass().getName() + " class=" + Policy.classify(value);
        // Only structural markers. Do not dump raw payloads, URLs, account IDs or tokens.
        try { text += " type=" + value.getClass().getField("type").get(value); } catch (Throwable ignored) { }
        try { text += " adChannel=" + value.getClass().getField("adChannel").get(value); } catch (Throwable ignored) { }
        return text;
    }
}
