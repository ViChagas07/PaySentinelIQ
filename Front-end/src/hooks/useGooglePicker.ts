"use client";

import { useState, useCallback, useEffect, useRef } from "react";

declare global {
  interface Window {
    google?: {
      accounts: {
        oauth2: {
          initTokenClient: (config: {
            client_id: string;
            scope: string;
            callback: (response: {
              access_token: string;
              error?: string;
            }) => void;
          }) => {
            requestAccessToken: () => void;
          };
        };
      };

      picker: any;
    };

    gapi?: {
      load: (
        api: string,
        callback: () => void
      ) => void;

      client: {
        init: (config: {
          discoveryDocs: string[];
        }) => Promise<void>;
      };
    };
  }
}

const GOOGLE_CLIENT_ID =
  process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "";

const GOOGLE_API_KEY =
  process.env.NEXT_PUBLIC_GOOGLE_API_KEY || "";

const SCOPES = [
  "https://www.googleapis.com/auth/drive.readonly"
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
  const [token, setToken] =
    useState<string | null>(null);

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  const tokenClientRef = useRef<any>(null);

  const pickerCallbackRef = useRef<
    ((files: PickedFile[]) => void) | null
  >(null);

  const loadingRef = useRef(false);
  const oauthActiveRef = useRef(false);

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) return;

    const loadGis = () => {
      if (window.google?.accounts?.oauth2) {
        tokenClientRef.current =
          window.google.accounts.oauth2.initTokenClient({
            client_id: GOOGLE_CLIENT_ID,

            scope: SCOPES,

            callback: (response) => {
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

              if (
                pickerCallbackRef.current &&
                response.access_token
              ) {
                openPickerWithToken(
                  response.access_token,
                  pickerCallbackRef.current
                );

                pickerCallbackRef.current =
                  null;
              }
            },
          });
      }
    };

    const existingScript =
      document.querySelector(
        'script[src="https://accounts.google.com/gsi/client"]'
      );

    if (!existingScript) {
      const script =
        document.createElement("script");

      script.src =
        "https://accounts.google.com/gsi/client";

      script.async = true;

      script.onload = loadGis;

      document.head.appendChild(script);
    } else {
      loadGis();
    }
  }, []);

  useEffect(() => {
    const handleFocus = () => {
      if (
        oauthActiveRef.current &&
        loadingRef.current
      ) {
        loadingRef.current = false;
        oauthActiveRef.current = false;

        setLoading(false);

        pickerCallbackRef.current?.([]);

        pickerCallbackRef.current =
          null;
      }
    };

    window.addEventListener(
      "focus",
      handleFocus
    );

    return () => {
      window.removeEventListener(
        "focus",
        handleFocus
      );
    };
  }, []);

  const loadPickerApi =
    useCallback((): Promise<void> => {
      return new Promise((resolve) => {
        if (window.gapi) {
          resolve();
          return;
        }

        const script =
          document.createElement("script");

        script.src =
          "https://apis.google.com/js/api.js";

        script.async = true;

        script.onload = () => {
          window.gapi!.load(
            "client:picker",
            async () => {
              await window.gapi!.client.init({
                discoveryDocs:
                  DISCOVERY_DOCS,
              });

              resolve();
            }
          );
        };

        document.head.appendChild(
          script
        );
      });
    }, []);

  const openPickerWithToken =
    useCallback(
      async (
        accessToken: string,
        onPick: (
          files: PickedFile[]
        ) => void
      ) => {
        await loadPickerApi();

        const view =
          new window.google!.picker.DocsView()
            .setIncludeFolders(true)
            .setMimeTypes(
              "application/pdf,image/png,image/jpeg,image/jpg"
            );

        const picker =
          new window.google!.picker.PickerBuilder()
            .addView(view)

            .setOAuthToken(
              accessToken
            )

            .setDeveloperKey(
              GOOGLE_API_KEY
            )

            .setCallback(
              (data: any) => {
                if (
                  data.action ===
                  window.google!.picker
                    .Action.PICKED
                ) {
                  const docs =
                    data[
                      window.google!
                        .picker.Response
                        .DOCUMENTS
                    ];

                  const files =
                    docs.map(
                      (
                        doc: any
                      ): PickedFile => ({
                        id: doc.id,
                        name:
                          doc.name,
                        mimeType:
                          doc.mimeType,
                        sizeBytes:
                          doc.sizeBytes,
                        url:
                          doc.url,
                        thumbnailUrl:
                          doc.iconUrl,
                      })
                    );

                  onPick(files);
                } else if (
                  data.action ===
                  window.google!.picker
                    .Action.CANCEL
                ) {
                  // User closed the picker without selecting files
                  onPick([]);
                }
              }
            )

            .build();

        picker.setVisible(true);
      },

      [loadPickerApi]
    );

  const openPicker =
    useCallback(
      (
        onPick: (
          files: PickedFile[]
        ) => void
      ) => {
        if (
          !GOOGLE_CLIENT_ID ||
          !GOOGLE_API_KEY
        ) {
          setError(
            "Google Drive not configured."
          );

          return;
        }

        if (token) {
          openPickerWithToken(
            token,
            onPick
          );

          return;
        }

        pickerCallbackRef.current =
          onPick;

        setLoading(true);

        loadingRef.current = true;
        oauthActiveRef.current = true;

        tokenClientRef.current?.requestAccessToken();
      },

      [token, openPickerWithToken]
    );

  return {
    openPicker,
    loading,
    error,
    token,
    isConfigured:
      !!GOOGLE_CLIENT_ID &&
      !!GOOGLE_API_KEY,
  };
}

/* ═══════════════════════════════════════════════════
   Fetch file content from Google Drive URL
   ═══════════════════════════════════════════════════ */

export async function fetchGoogleFileContent(
  fileUrl: string,
  accessToken: string
): Promise<Blob> {

  const response = await fetch(fileUrl, {
    headers: {
      Authorization: `Bearer ${accessToken}`
    }
  });

  if (!response.ok) {
    throw new Error(
      `Failed to fetch file: ${response.status} ${response.statusText}`
    );
  }

  return await response.blob();
}