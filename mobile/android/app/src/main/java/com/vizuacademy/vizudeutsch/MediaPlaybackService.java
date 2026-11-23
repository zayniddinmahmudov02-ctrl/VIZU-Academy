package com.vizuacademy.vizudeutsch;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.content.pm.ServiceInfo;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.drawable.Icon;
import android.media.MediaMetadata;
import android.media.session.MediaSession;
import android.media.session.PlaybackState;
import android.net.Uri;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;

import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;

/**
 * Foreground service of type mediaPlayback: one MediaSession + one media-style notification (previous / play-pause / next),
 * which Android also shows on the lock screen. Every button goes back to the page (MediaSessionPlugin.emit); the page's
 * audio element does the playing. Paused = the notification stays (swipe-able), the service leaves the foreground; stop()
 * or removing the app from the recent apps ends everything.
 */
public class MediaPlaybackService extends Service {
    static final String CHANNEL = "vizu_media";
    static final int NOTIFICATION_ID = 4711;
    static final String ACTION_PLAY = "vizu.media.PLAY";
    static final String ACTION_PAUSE = "vizu.media.PAUSE";
    static final String ACTION_NEXT = "vizu.media.NEXT";
    static final String ACTION_PREV = "vizu.media.PREV";
    static final String ACTION_STOP = "vizu.media.STOP";
    private static final int MAX_ART_BYTES = 2 * 1024 * 1024;

    static MediaPlaybackService instance;
    static State pending;

    static class State {
        String title, artist, album, artwork;
        boolean playing, hasPrev, hasNext;
        long positionMs, durationMs;
    }

    private MediaSession session;
    private State state;
    private boolean foreground;
    private String artUrl;
    private Bitmap art;
    private final Handler main = new Handler(Looper.getMainLooper());

    @Override
    public void onCreate() {
        super.onCreate();
        instance = this;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel ch = new NotificationChannel(CHANNEL, "Musik", NotificationManager.IMPORTANCE_LOW);
            ch.setDescription("VIZU-DEUTSCH Musik-Steuerung");
            ch.setShowBadge(false);
            getSystemService(NotificationManager.class).createNotificationChannel(ch);
        }
        session = new MediaSession(this, "VIZU-DEUTSCH");
        session.setCallback(new MediaSession.Callback() {
            @Override public void onPlay() { emit("play", null); }
            @Override public void onPause() { emit("pause", null); }
            @Override public void onSkipToNext() { emit("next", null); }
            @Override public void onSkipToPrevious() { emit("previous", null); }
            @Override public void onStop() { emit("stop", null); }
            @Override public void onSeekTo(long pos) { emit("seekto", pos); }
        });
        session.setSessionActivity(openApp());
        session.setActive(true);
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        String action = intent != null ? intent.getAction() : null;
        if (action == null) {
            State s = pending != null ? pending : state;
            pending = null;
            if (s == null) { // nothing to show: never stay in the foreground without a notification
                end();
                return START_NOT_STICKY;
            }
            apply(s);
        } else if (ACTION_PLAY.equals(action)) emit("play", null);
        else if (ACTION_PAUSE.equals(action)) emit("pause", null);
        else if (ACTION_NEXT.equals(action)) emit("next", null);
        else if (ACTION_PREV.equals(action)) emit("previous", null);
        else if (ACTION_STOP.equals(action)) emit("stop", null);
        return START_NOT_STICKY;
    }

    private void emit(String action, Long positionMs) {
        MediaSessionPlugin p = MediaSessionPlugin.instance;
        if (p != null) p.emit(action, positionMs);
        else if ("stop".equals(action)) end(); // the page is gone: nothing can play any more
    }

    void apply(State s) {
        if (session == null) return; // already ended
        state = s;
        if (s.artwork == null || !s.artwork.equals(artUrl)) loadArtwork(s.artwork);
        MediaMetadata.Builder meta = new MediaMetadata.Builder()
                .putString(MediaMetadata.METADATA_KEY_TITLE, s.title)
                .putString(MediaMetadata.METADATA_KEY_ARTIST, s.artist)
                .putString(MediaMetadata.METADATA_KEY_ALBUM, s.album);
        if (s.durationMs > 0) meta.putLong(MediaMetadata.METADATA_KEY_DURATION, s.durationMs);
        if (art != null) meta.putBitmap(MediaMetadata.METADATA_KEY_ALBUM_ART, art);
        session.setMetadata(meta.build());
        long actions = PlaybackState.ACTION_PLAY | PlaybackState.ACTION_PAUSE | PlaybackState.ACTION_PLAY_PAUSE | PlaybackState.ACTION_STOP
                | PlaybackState.ACTION_SEEK_TO;
        if (s.hasNext) actions |= PlaybackState.ACTION_SKIP_TO_NEXT;
        if (s.hasPrev) actions |= PlaybackState.ACTION_SKIP_TO_PREVIOUS;
        session.setPlaybackState(new PlaybackState.Builder()
                .setActions(actions)
                .setState(s.playing ? PlaybackState.STATE_PLAYING : PlaybackState.STATE_PAUSED, s.positionMs, s.playing ? 1f : 0f)
                .build());
        Notification n = build(s);
        if (s.playing) {
            try {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                    startForeground(NOTIFICATION_ID, n, ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PLAYBACK);
                } else {
                    startForeground(NOTIFICATION_ID, n);
                }
                foreground = true;
            } catch (RuntimeException e) { // Android 12+ may refuse a foreground start from the background: show it anyway
                getSystemService(NotificationManager.class).notify(NOTIFICATION_ID, n);
            }
        } else {
            if (foreground) {
                stopForeground(STOP_FOREGROUND_DETACH);
                foreground = false;
            }
            getSystemService(NotificationManager.class).notify(NOTIFICATION_ID, n);
        }
    }

    private Notification build(State s) {
        Notification.Builder b = Build.VERSION.SDK_INT >= Build.VERSION_CODES.O ? new Notification.Builder(this, CHANNEL) : new Notification.Builder(this);
        b.setSmallIcon(R.drawable.ic_stat_vizu)
                .setContentTitle(s.title)
                .setContentText(s.artist)
                .setSubText(s.album)
                .setContentIntent(openApp())
                .setDeleteIntent(action(ACTION_STOP, 5))
                .setVisibility(Notification.VISIBILITY_PUBLIC)
                .setOnlyAlertOnce(true)
                .setShowWhen(false)
                .setOngoing(s.playing);
        if (art != null) b.setLargeIcon(art);
        int compact = 0;
        if (s.hasPrev) {
            b.addAction(new Notification.Action.Builder(Icon.createWithResource(this, android.R.drawable.ic_media_previous), "Zurück", action(ACTION_PREV, 1)).build());
            compact++;
        }
        b.addAction(s.playing
                ? new Notification.Action.Builder(Icon.createWithResource(this, android.R.drawable.ic_media_pause), "Pause", action(ACTION_PAUSE, 2)).build()
                : new Notification.Action.Builder(Icon.createWithResource(this, android.R.drawable.ic_media_play), "Abspielen", action(ACTION_PLAY, 3)).build());
        int playIndex = compact;
        int[] compactView;
        if (s.hasNext) {
            b.addAction(new Notification.Action.Builder(Icon.createWithResource(this, android.R.drawable.ic_media_next), "Weiter", action(ACTION_NEXT, 4)).build());
            compactView = s.hasPrev ? new int[] {0, 1, 2} : new int[] {0, 1};
        } else {
            compactView = s.hasPrev ? new int[] {0, 1} : new int[] {playIndex};
        }
        b.setStyle(new Notification.MediaStyle().setMediaSession(session.getSessionToken()).setShowActionsInCompactView(compactView));
        return b.build();
    }

    private PendingIntent action(String name, int code) {
        Intent i = new Intent(this, MediaPlaybackService.class).setAction(name);
        return PendingIntent.getService(this, code, i, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }

    private PendingIntent openApp() {
        Intent i = new Intent(this, MainActivity.class).setFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        return PendingIntent.getActivity(this, 0, i, PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
    }

    /** Cover image: https only, at most 2 MB, loaded off the main thread; the notification is refreshed when it arrives. */
    private void loadArtwork(String url) {
        artUrl = url;
        art = null;
        if (url == null || !"https".equals(Uri.parse(url).getScheme())) return;
        new Thread(() -> {
            Bitmap bmp = null;
            HttpURLConnection con = null;
            try {
                con = (HttpURLConnection) new URL(url).openConnection();
                con.setConnectTimeout(8000);
                con.setReadTimeout(8000);
                try (InputStream in = con.getInputStream(); ByteArrayOutputStream out = new ByteArrayOutputStream()) {
                    byte[] buf = new byte[16384];
                    int n, total = 0;
                    while ((n = in.read(buf)) > 0) {
                        total += n;
                        if (total > MAX_ART_BYTES) return;
                        out.write(buf, 0, n);
                    }
                    byte[] data = out.toByteArray();
                    bmp = BitmapFactory.decodeByteArray(data, 0, data.length);
                }
            } catch (Exception ignored) {
                // no cover: the notification shows the app icon
            } finally {
                if (con != null) con.disconnect();
            }
            final Bitmap result = bmp;
            main.post(() -> {
                if (result != null && url.equals(artUrl) && state != null && instance == this) {
                    art = result;
                    apply(state);
                }
            });
        }).start();
    }

    void end() {
        if (session != null) {
            session.setActive(false);
            session.release();
            session = null;
        }
        stopForeground(STOP_FOREGROUND_REMOVE);
        getSystemService(NotificationManager.class).cancel(NOTIFICATION_ID);
        foreground = false;
        instance = null;
        stopSelf();
    }

    @Override
    public void onTaskRemoved(Intent rootIntent) {
        end(); // the app (and its page with the audio element) was closed
        super.onTaskRemoved(rootIntent);
    }

    @Override
    public void onDestroy() {
        if (instance == this) instance = null;
        if (session != null) {
            session.release();
            session = null;
        }
        super.onDestroy();
    }

    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
}
