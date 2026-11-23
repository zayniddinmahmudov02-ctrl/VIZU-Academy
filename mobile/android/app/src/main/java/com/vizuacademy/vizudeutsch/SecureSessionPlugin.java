package com.vizuacademy.vizudeutsch;

import android.content.Context;
import android.content.SharedPreferences;
import android.net.Uri;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.util.Base64;
import android.webkit.WebView;

import androidx.webkit.ScriptHandler;
import androidx.webkit.WebViewCompat;
import androidx.webkit.WebViewFeature;

import com.getcapacitor.Logger;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;

import org.json.JSONObject;

import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import java.util.Collections;

import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;

/**
 * The login session of the app, kept OUT of the WebView's localStorage.
 *
 * - "Angemeldet bleiben" on: access + refresh token are stored encrypted with an AES-256-GCM key that lives in the Android
 *   Keystore (the key never leaves it; another app or a copied file cannot decrypt). Off: kept in memory only (gone when the
 *   app process ends), nothing is written.
 * - The page gets the session synchronously before its own scripts run: a document-start script for the app's own origin only
 *   (never for other origins or embedded third-party frames) defines window.__VIZU_SESSION__. The website (lib/token.ts) reads
 *   it once and reports every change back through set() / clear().
 * - No token is ever logged. Called only by pages of the app's own origin (the Capacitor bridge exists only there).
 */
@CapacitorPlugin(name = "VizuSession")
public class SecureSessionPlugin extends Plugin {
    private static final String PREFS = "vizu_secure_session";
    private static final String BLOB = "session";
    private static final String KEY_ALIAS = "vizu_session_key";

    private static String access;
    private static String refresh;
    private static boolean remember = true;

    private ScriptHandler script;
    private String origin;

    @Override
    public void load() {
        origin = originOf(getBridge().getAppUrl());
        restore();
        inject();
    }

    @PluginMethod
    public void set(PluginCall call) {
        access = emptyToNull(call.getString("access", null));
        refresh = emptyToNull(call.getString("refresh", null));
        remember = Boolean.TRUE.equals(call.getBoolean("remember", true));
        persist();
        getActivity().runOnUiThread(this::inject);
        call.resolve();
    }

    @PluginMethod
    public void clear(PluginCall call) {
        access = null;
        refresh = null;
        remember = true;
        prefs().edit().remove(BLOB).apply();
        getActivity().runOnUiThread(this::inject);
        call.resolve();
    }

    // ── document-start injection ──────────────────────────────────────────────

    private void inject() {
        if (origin == null || !WebViewFeature.isFeatureSupported(WebViewFeature.DOCUMENT_START_SCRIPT)) {
            return; // old WebView: the website falls back to its normal storage
        }
        WebView webView = getBridge().getWebView();
        if (script != null) {
            script.remove();
            script = null;
        }
        String js = "window.__VIZU_SESSION__=Object.freeze({v:1,access:" + quote(access) + ",refresh:" + quote(refresh)
                + ",remember:" + remember + "});";
        try {
            script = WebViewCompat.addDocumentStartJavaScript(webView, js, Collections.singleton(origin));
        } catch (IllegalArgumentException e) {
            Logger.warn("VizuSession: invalid origin rule");
        }
    }

    private static String quote(String value) {
        return value == null ? "null" : JSONObject.quote(value);
    }

    private static String originOf(String url) {
        if (url == null) return null;
        Uri u = Uri.parse(url);
        if (u.getScheme() == null || u.getHost() == null) return null;
        return u.getScheme() + "://" + u.getHost() + (u.getPort() > 0 ? ":" + u.getPort() : "");
    }

    private static String emptyToNull(String s) {
        return s == null || s.isEmpty() ? null : s;
    }

    // ── encrypted storage ─────────────────────────────────────────────────────

    private SharedPreferences prefs() {
        return getContext().getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    private void persist() {
        if (!remember || (access == null && refresh == null)) {
            prefs().edit().remove(BLOB).apply();
            return;
        }
        try {
            JSONObject o = new JSONObject();
            o.put("access", access == null ? JSONObject.NULL : access);
            o.put("refresh", refresh == null ? JSONObject.NULL : refresh);
            Cipher c = Cipher.getInstance("AES/GCM/NoPadding");
            c.init(Cipher.ENCRYPT_MODE, key());
            byte[] ct = c.doFinal(o.toString().getBytes(StandardCharsets.UTF_8));
            String blob = Base64.encodeToString(c.getIV(), Base64.NO_WRAP) + ":" + Base64.encodeToString(ct, Base64.NO_WRAP);
            prefs().edit().putString(BLOB, blob).apply();
        } catch (Exception e) {
            Logger.warn("VizuSession: could not store the session (" + e.getClass().getSimpleName() + ")");
            prefs().edit().remove(BLOB).apply();
        }
    }

    private void restore() {
        if (access != null || refresh != null) return; // same process (activity re-created): keep the memory copy
        String blob = prefs().getString(BLOB, null);
        if (blob == null) return;
        try {
            String[] parts = blob.split(":", 2);
            Cipher c = Cipher.getInstance("AES/GCM/NoPadding");
            c.init(Cipher.DECRYPT_MODE, key(), new GCMParameterSpec(128, Base64.decode(parts[0], Base64.NO_WRAP)));
            JSONObject o = new JSONObject(new String(c.doFinal(Base64.decode(parts[1], Base64.NO_WRAP)), StandardCharsets.UTF_8));
            access = o.isNull("access") ? null : o.getString("access");
            refresh = o.isNull("refresh") ? null : o.getString("refresh");
            remember = true;
        } catch (Exception e) {
            Logger.warn("VizuSession: stored session unreadable, cleared (" + e.getClass().getSimpleName() + ")");
            prefs().edit().remove(BLOB).apply();
        }
    }

    private static SecretKey key() throws Exception {
        KeyStore ks = KeyStore.getInstance("AndroidKeyStore");
        ks.load(null);
        if (!ks.containsAlias(KEY_ALIAS)) {
            KeyGenerator kg = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore");
            kg.init(new KeyGenParameterSpec.Builder(KEY_ALIAS, KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                    .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                    .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                    .setKeySize(256)
                    .build());
            return kg.generateKey();
        }
        return ((KeyStore.SecretKeyEntry) ks.getEntry(KEY_ALIAS, null)).getSecretKey();
    }
}
