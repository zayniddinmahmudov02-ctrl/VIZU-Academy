package com.vizu.deutsch;

import android.app.DownloadManager;
import android.content.Context;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.webkit.CookieManager;
import android.webkit.URLUtil;
import android.webkit.WebView;
import android.widget.Toast;

import com.getcapacitor.BridgeActivity;

/**
 * VIZU DEUTSCH Android shell. The UI is the live site (capacitor.config.json server.url); Capacitor keeps
 * vizu-deutsch.com inside the app and opens other hosts in the system browser, and handles the back button,
 * the file chooser (gallery / camera) and the microphone permission for getUserMedia.
 *
 * Added here: a WebView download listener. A plain WebView silently ignores downloads, so an https download
 * (e.g. the APK update from /downloads/android/latest.apk) goes to the system DownloadManager: it shows the
 * usual download notification, and the user installs the APK with the normal Android package installer
 * (never silently). Not ACTION_VIEW: the App Link filter would route vizu-deutsch.com URLs back into this app.
 */
public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        WebView webView = getBridge().getWebView();
        webView.setDownloadListener((url, userAgent, contentDisposition, mimeType, contentLength) -> {
            if (url == null || !url.startsWith("https://")) {
                return; // blob:/data: downloads are handled by the page itself; no plain http
            }
            try {
                String name = URLUtil.guessFileName(url, contentDisposition, mimeType);
                DownloadManager.Request request = new DownloadManager.Request(Uri.parse(url))
                        .setMimeType(mimeType)
                        .addRequestHeader("User-Agent", userAgent)
                        .setTitle(name)
                        .setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                    request.setDestinationInExternalPublicDir(Environment.DIRECTORY_DOWNLOADS, name);
                } else {
                    // Android 7–9: public Downloads would need a storage permission; the app folder needs none.
                    request.setDestinationInExternalFilesDir(this, Environment.DIRECTORY_DOWNLOADS, name);
                }
                String cookies = CookieManager.getInstance().getCookie(url);
                if (cookies != null) {
                    request.addRequestHeader("Cookie", cookies);
                }
                DownloadManager dm = (DownloadManager) getSystemService(Context.DOWNLOAD_SERVICE);
                dm.enqueue(request);
                Toast.makeText(this, "Download gestartet · Yuklab olish boshlandi", Toast.LENGTH_SHORT).show();
            } catch (RuntimeException e) {
                Toast.makeText(this, "Download fehlgeschlagen · Yuklab bo'lmadi", Toast.LENGTH_LONG).show();
            }
        });
    }
}
