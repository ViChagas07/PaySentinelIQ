"use client";

import { useState, useCallback, useEffect, useRef } from "react";

/* ═══════════════════════════════════════════════════
   Google Picker Hook
   Uses Google Identity Services + Picker API to let
   users browse and select files from Drive / Photos.
   ═══════════════════════════════════════════════════ */

declare global {
  interface Window {
    google?: {
      accounts: {
        oauth2: {
          initTokenClient: (config: {
            client_id: string;
            scope: string;
            callback: (response: { access_token: string; error?: string }) => void;
          }) => {
            requestAccessToken: () => void;
          };
        };
      };
    };
    gapi?: {
      load: (api: string, callback: () => void) => void;
    };
  }
}

const GOOGLE_CLIENT_ID = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "";
const SCOPES = [
  "https://www.googleapis.com/auth/drive.readonly",
  "https://www.googleapis.com/auth/photoslibrary.readonly",
].join(" ");

const DISCOVERY_DOCS = [
  "https://www.googleapis.com/discovery/v1/apis/drive/v3/rest",
];

export interface PickedFile {
  id: string;
  name: string;
  mimeType: string;
  sizeBytes?: string;
  url: string;
  thumbnailUrl?: string;
}

export function useGooglePicker() {
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const tokenClientRef = useRef<any>(null);
  const pickerCallbackRef = useRef<((files: PickedFile[]) => void) | null>(null);

  // Refs for synchronous access in event handlers (avoid stale closures)
  const loadingRef = useRef(false);
  const oauthActiveRef = useRef(false);

  // Load Google Identity Services script
  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) return;

    const loadGis = () => {
      if (window.google?.accounts?.oauth2) {
        tokenClientRef.current = window.google.accounts.oauth2.initTokenClient({
          client_id: GOOGLE_CLIENT_ID,
          scope: SCOPES,
          callback: (response: { access_token: string; error?: string }) => {
            if (response.error) {
              setError(response.error);
              setLoading(false);
              loadingRef.current = false;
              oauthActiveRef.current = false;
              return;
            }
            setToken(response.access_token);
            setLoading(false);
            loadingRef.current = false;
            oauthActiveRef.current = false;
            // If a picker callback is waiting, proceed
            if (pickerCallbackRef.current && response.access_token) {
              openPickerWithToken(response.access_token, pickerCallbackRef.current);
              pickerCallbackRef.current = null;
            }
          },
        });
      }
    };

    if (!document.querySelector('script[src="https://accounts.google.com/gsi/client"]')) {
      const script = document.createElement("script");
      script.src = "https://accounts.google.com/gsi/client";
      script.async = true;
      script.onload = loadGis;
      document.head.appendChild(script);
    } else {
      loadGis();
    }

    return () => {
      // Cleanup not needed for head scripts
    };
  }, []);

  // Detect when user closes the OAuth popup without completing auth
  useEffect(() => {
    const handleFocus = () => {
      if (oauthActiveRef.current && loadingRef.current) {
        // The popup was closed without completing authentication.
        // Reset loading state and notify the waiting callback with empty result.
        loadingRef.current = false;
        oauthActiveRef.current = false;
        setLoading(false);
        pickerCallbackRef.current?.([]);
        pickerCallbackRef.current = null;
      }
    };

    window.addEventListener("focus", handleFocus);
    return () => window.removeEventListener("focus", handleFocus);
  }, []);

  // Load Picker API
  const loadPickerApi = useCallback((): Promise<void> => {
    return new Promise((resolve) => {
      if (window.gapi) { resolve(); return; }
      const script = document.createElement("script");
      script.src = "https://apis.google.com/js/api.js";
      script.async = true;
      script.onload = () => {
        window.gapi!.load("picker", resolve);
      };
      document.head.appendChild(script);
    });
  }, []);

  // Open the Google Picker with a valid token
  const openPickerWithToken = useCallback(async (accessToken: string, onPick: (files: PickedFile[]) => void) => {
    await loadPickerApi();

    const view = new (window as any).google.picker.DocsView()
      .setIncludeFolders(true)
      .setMimeTypes("application/pdf,image/png,image/jpeg,image/jpg");

    const photosView = new (window as any).google.picker.PhotosView();

    const picker = new (window as any).google.picker.PickerBuilder()
      .addView(view)
      .addView(photosView)
      .setOAuthToken(accessToken)
      .setDeveloperKey(GOOGLE_CLIENT_ID)
      .setCallback((data: any) => {
        if (data.action === (window as any).google.picker.Action.PICKED) {
          const docs = data[(window as any).google.picker.Response.DOCUMENTS];
          const files: PickedFile[] = docs.map((doc: any) => ({
            id: doc.id,
            name: doc.name,
            mimeType: doc.mimeType,
            sizeBytes: doc.sizeBytes,
            url: doc.url,
            thumbnailUrl: doc.thumbnails?.[0]?.url || doc.iconUrl,
          }));
          onPick(files);
        }
      })
      .build();

    picker.setVisible(true);
  }, [loadPickerApi]);

  // Main entry point — requests token then opens picker
  const openPicker = useCallback((onPick: (files: PickedFile[]) => void) => {
    if (!GOOGLE_CLIENT_ID) {
      setError("Google Client ID not configured. Add NEXT_PUBLIC_GOOGLE_CLIENT_ID to .env.local");
      return;
    }

    // If we already have a token, try opening picker directly
    if (token) {
      openPickerWithToken(token, onPick).catch(() => {
        // Token expired, re-auth
        setToken(null);
        pickerCallbackRef.current = onPick;
        setLoading(true);
        loadingRef.current = true;
        oauthActiveRef.current = true;
        tokenClientRef.current?.requestAccessToken();
      });
      return;
    }

    pickerCallbackRef.current = onPick;
    setLoading(true);
    loadingRef.current = true;
    oauthActiveRef.current = true;
    setError(null);

    if (tokenClientRef.current) {
      tokenClientRef.current.requestAccessToken();
    } else {
      // GIS not loaded yet — retry after a delay
      setTimeout(() => {
        if (tokenClientRef.current) {
          tokenClientRef.current.requestAccessToken();
        } else {
          setError("Google Sign-In not available. Please refresh the page.");
          setLoading(false);
          loadingRef.current = false;
          oauthActiveRef.current = false;
        }
      }, 1000);
    }
  }, [token, openPickerWithToken]);

  const signOut = useCallback(() => {
    setToken(null);
  }, []);

  return { openPicker, signOut, loading, error, token, isConfigured: !!GOOGLE_CLIENT_ID };
}

/* ═══════════════════════════════════════════════════
   Fetch file content from Google Drive URL
   ═══════════════════════════════════════════════════ */

export async function fetchGoogleFileContent(
  fileUrl: string,
  accessToken: string
): Promise<Blob> {
  const response = await fetch(fileUrl, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!response.ok) throw new Error(`Failed to fetch file: ${response.statusText}`);
  return response.blob();
}
