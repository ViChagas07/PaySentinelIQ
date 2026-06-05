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
    };
  }
}

const GOOGLE_CLIENT_ID =
  process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || "";

const GOOGLE_API_KEY =
  process.env.NEXT_PUBLIC_GOOGLE_API_KEY || "";


/*
  Escopo reduzido:
  Permite selecionar arquivos do Drive
  sem pedir acesso amplo ao Drive inteiro.
*/

const SCOPES =
  "https://www.googleapis.com/auth/drive.file";

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

  const tokenClientRef =
    useRef<any>(null);

  const pickerCallbackRef =
    useRef<
      ((files: PickedFile[]) => void) | null
    >(null);

  const loadingRef =
    useRef(false);

  const oauthActiveRef =
    useRef(false);

  /*
   ─────────────────────────────
   Load Google Identity Services
   ─────────────────────────────
  */

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) return;

    const loadGIS = () => {
      if (
        window.google?.accounts
          ?.oauth2
      ) {
        tokenClientRef.current =
          window.google.accounts.oauth2.initTokenClient(
            {
              client_id:
                GOOGLE_CLIENT_ID,

              scope: SCOPES,

              callback: (
                response
              ) => {
                if (
                  response.error
                ) {
                  setError(
                    response.error
                  );

                  setLoading(
                    false
                  );

                  loadingRef.current =
                    false;

                  oauthActiveRef.current =
                    false;

                  return;
                }

                setToken(
                  response.access_token
                );

                setLoading(
                  false
                );

                loadingRef.current =
                  false;

                oauthActiveRef.current =
                  false;

                if (
                  pickerCallbackRef.current
                ) {
                  openPickerWithToken(
                    response.access_token,
                    pickerCallbackRef.current
                  );

                  pickerCallbackRef.current =
                    null;
                }
              },
            }
          );
      }
    };

    if (
      !document.querySelector(
        'script[src="https://accounts.google.com/gsi/client"]'
      )
    ) {
      const script =
        document.createElement(
          "script"
        );

      script.src =
        "https://accounts.google.com/gsi/client";

      script.async = true;

      script.onload =
        loadGIS;

      document.head.appendChild(
        script
      );
    } else {
      loadGIS();
    }
  }, []);

  /*
   ─────────────────────────────
   Detect popup close
   ─────────────────────────────
  */

  useEffect(() => {
    const handleFocus =
      () => {
        if (
          oauthActiveRef.current &&
          loadingRef.current
        ) {
          loadingRef.current =
            false;

          oauthActiveRef.current =
            false;

          setLoading(
            false
          );

          pickerCallbackRef.current?.(
            []
          );

          pickerCallbackRef.current =
            null;
        }
      };

    window.addEventListener(
      "focus",
      handleFocus
    );

    return () =>
      window.removeEventListener(
        "focus",
        handleFocus
      );
  }, []);

  /*
   ─────────────────────────────
   Load Picker API
   ─────────────────────────────
  */

  const loadPickerApi =
    useCallback(() => {
      return new Promise<void>(
        (resolve) => {
          if (
            window.gapi
          ) {
            resolve();
            return;
          }

          const script =
            document.createElement(
              "script"
            );

          script.src =
            "https://apis.google.com/js/api.js";

          script.async =
            true;

          script.onload =
            () => {
              window.gapi!.load(
                "picker",
                resolve
              );
            };

          document.head.appendChild(
            script
          );
        }
      );
    }, []);

  /*
   ─────────────────────────────
   Open Picker
   ─────────────────────────────
  */

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
            .setIncludeFolders(
              true
            )
            .setMimeTypes(
              "application/pdf,image/png,image/jpeg,image/jpg"
            );

        const picker =
          new window.google!.picker.PickerBuilder()

            .addView(
              view
            )

            .setOAuthToken(
              accessToken
            )

            .setDeveloperKey(
              GOOGLE_API_KEY
            )

            .setCallback(
              (
                data: any
              ) => {
                if (
                  data.action ===
                  window.google
                    ?.picker
                    .Action
                    .PICKED
                ) {
                  const docs =
                    data[
                      window
                        .google
                        ?.picker
                        .Response
                        .DOCUMENTS
                    ];

                  const files =
                    docs.map(
                      (
                        doc: any
                      ) => ({
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
                          doc
                            .thumbnails?.[0]
                            ?.url ||
                          doc.iconUrl,
                      })
                    );

                  onPick(
                    files
                  );
                }
              }
            )

            .build();

        picker.setVisible(
          true
        );
      },
      [loadPickerApi]
    );

  /*
   ─────────────────────────────
   Main function
   ─────────────────────────────
  */

  const openPicker =
    useCallback(
      (
        onPick: (
          files: PickedFile[]
        ) => void
      ) => {
        if (
          !GOOGLE_CLIENT_ID
        ) {
          setError(
            "Missing Google Client ID"
          );

          return;
        }

        if (
          !GOOGLE_API_KEY
        ) {
          setError(
            "Missing Google API Key"
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

        setLoading(
          true
        );

        loadingRef.current =
          true;

        oauthActiveRef.current =
          true;

        setError(
          null
        );

        tokenClientRef.current?.requestAccessToken();
      },
      [
        token,
        openPickerWithToken
      ]
    );

  const signOut =
    useCallback(() => {
      setToken(
        null
      );
    }, []);

  return {
    openPicker,
    signOut,
    loading,
    error,
    token,
    isConfigured:
      !!GOOGLE_CLIENT_ID &&
      !!GOOGLE_API_KEY,
  };
}

export async function fetchGoogleFileContent(
  fileUrl: string,
  accessToken: string
): Promise<Blob> {

  const response =
    await fetch(
      fileUrl,
      {
        headers: {
          Authorization:
            `Bearer ${accessToken}`,
        },
      }
    );

  if (
    !response.ok
  ) {
    throw new Error(
      `Failed: ${response.statusText}`
    );
  }

  return response.blob();
}