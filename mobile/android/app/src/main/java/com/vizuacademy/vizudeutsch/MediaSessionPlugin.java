package com.vizuacademy.vizudeutsch;

import android.content.Intent;
import android.os.Handler;
import android.os.Looper;

import androidx.core.content.ContextCompat;

import com.getcapacitor.JSObject;
import com.getcapacitor.Logger;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

/**
 * Lock-screen / notification controls for the website's music player (Medien → Musik). The page tells the app what plays
 * (update) and receives the buttons the user presses (event "action": play, pause, next, previous, stop, seekto).
 * The playback itself stays in the page's own audio element; this only mirrors it into an Android MediaSession and a
 * media-playback foreground service, which also keeps the app alive while the user listens with the screen off.
 * The service is started only for playback the user started (update with playing = true) and ends with stop().
 */
@CapacitorPlugin(name = "VizuMedia")
public class MediaSessionPlugin extends Plugin {
    static MediaSessionPlugin instance;
    private final Handler main = new Handler(Looper.getMainLooper());

    @Override
    public void load() {
        instance = this;
    }

    @PluginMethod
    public void update(PluginCall call) {
        MediaPlaybackService.State s = new MediaPlaybackService.State();
        s.title = call.getString("title", "VIZU-DEUTSCH");
        s.artist = call.getString("artist", "");
        s.album = call.getString("album", "VIZU Medienwelt");
        s.artwork = call.getString("artwork", null);
        s.playing = Boolean.TRUE.equals(call.getBoolean("playing", false));
        s.positionMs = (long) (call.getDouble("position", 0.0) * 1000);
        s.durationMs = (long) (call.getDouble("duration", 0.0) * 1000);
        s.hasPrev = Boolean.TRUE.equals(call.getBoolean("hasPrev", true));
        s.hasNext = Boolean.TRUE.equals(call.getBoolean("hasNext", true));
        main.post(() -> {
            MediaPlaybackService svc = MediaPlaybackService.instance;
            if (svc != null) {
                svc.apply(s);
            } else if (s.playing) {
                MediaPlaybackService.pending = s;
                try {
                    ContextCompat.startForegroundService(getContext(), new Intent(getContext(), MediaPlaybackService.class));
                } catch (RuntimeException e) {
                    Logger.warn("VizuMedia: could not start the playback service (" + e.getClass().getSimpleName() + ")");
                }
            }
        });
        call.resolve();
    }

    @PluginMethod
    public void stop(PluginCall call) {
        main.post(() -> {
            if (MediaPlaybackService.instance != null) MediaPlaybackService.instance.end();
        });
        call.resolve();
    }

    void emit(String action, Long positionMs) {
        JSObject o = new JSObject();
        o.put("action", action);
        if (positionMs != null) o.put("position", positionMs / 1000.0);
        notifyListeners("action", o);
    }

    @Override
    protected void handleOnDestroy() {
        if (MediaPlaybackService.instance != null) MediaPlaybackService.instance.end();
        instance = null;
    }
}
