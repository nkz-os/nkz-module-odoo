declare module '@nekazari/sdk' {
  export const i18n: {
    t?: (key: string, options?: Record<string, unknown> & { ns?: string }) => string;
    addResourceBundle?: (
      lng: string,
      ns: string,
      resources: Record<string, unknown>,
      deep?: boolean,
      overwrite?: boolean
    ) => unknown;
  };

  export function useTranslation(ns?: string): {
    t: (key: string, options?: Record<string, unknown>) => string;
    i18n: typeof i18n;
  };

  export type ModuleViewerSlots = Record<string, unknown>;
}

declare global {
  interface Window {
    __NKZ__?: {
      register: (opts: {
        id: string;
        viewerSlots?: unknown;
        main?: import('react').ComponentType<unknown>;
        version?: string;
      }) => void;
    };
  }
}

export {};
